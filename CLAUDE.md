# CLAUDE.md

LLM guidance for working with the jscom-contact-services repository.

## Repository Overview

Serverless contact form API system for johnsosoka.com, built on AWS Lambda, API Gateway, SQS, and DynamoDB. Provides both a public contact submission API and a protected admin API for managing messages and blocked contacts.

**Core Capabilities:**
- Event-driven message processing pipeline with filtering
- Multi-channel notifications (Email via SES, Discord webhooks)
- Admin API with Lambda authorizer for authentication
- Support for standard and consulting contact form types

## Architecture

### Message Flow (Public API)

```
API Gateway POST /v1/contact
    ↓
contact-listener Lambda (validates, extracts metadata)
    ↓
contact-message-queue (SQS)
    ↓
contact-filter Lambda (checks blocked_contacts, writes to DynamoDB)
    ↓
contact-notify-queue (SQS)
    ↓
contact-notifier Lambda (sends notifications via Email/Discord)
```

### Admin Flow (Protected API)

```
API Gateway ANY /v1/contact/admin/{proxy+}
    ↓
contact-admin-authorizer (validates x-api-key header)
    ↓
contact-admin Lambda (CRUD operations on DynamoDB)
```

### Lambda Functions

**contact-listener** (`lambdas/src/contact-listener/app/`)
- Entry point for public contact form submissions
- Validates payload structure (requires `contact_message`)
- Extracts IP address and user agent from API Gateway v2 event context
- Determines contact type: `standard` or `consulting` (based on `consulting_contact` boolean)
- Forwards to `contact-message-queue` SQS

**contact-filter** (`lambdas/src/contact-filter/app/`)
- Event-driven via SQS (`contact-message-queue`)
- Scans `blocked_contacts` DynamoDB table by IP address
- Writes ALL messages to `all-contact-messages` table with `is_blocked` flag
- Forwards non-blocked messages to `contact-notify-queue`
- Manually deletes processed SQS messages

**contact-notifier** (`lambdas/src/contact-notifier/app/`)
- Event-driven via SQS (`contact-notify-queue`)
- Plugin-based notification system with configurable methods:
  - **Email**: HTML templates via AWS SES (different formatting for consulting vs standard)
  - **Discord**: Webhook notifications with rich embeds
- Environment variables control which notification methods are enabled
- Manually deletes processed SQS messages

**contact-admin** (`lambdas/src/contact-admin/app/`)
- REST API Lambda using AWS Lambda Powertools (APIGatewayRestResolver)
- Pydantic v2 models for type-safe request/response validation
- Provides admin endpoints: list messages, view message, get stats, manage blocked contacts
- Protected by custom Lambda authorizer (API key authentication)

### Authorization

The admin API uses a **shared Lambda authorizer module** from `jscom-tf-modules`:
- Module: `git::https://github.com/johnsosoka/jscom-tf-modules.git//modules/lambda-authorizer`
- Validates `x-api-key` header against Terraform variable
- Returns simple boolean authorization response (API Gateway v2 format)
- Invoked before admin Lambda, preventing unauthorized access

**Note:** The authorizer is NOT a local Lambda function in this repository - it's provisioned as a Terraform module dependency.

## Dependencies

### Shared Infrastructure (jscom-core-infrastructure)

Not directly referenced in current Terraform state but part of broader jscom ecosystem.

### API Gateway (jscom-blog)

This project integrates with an existing API Gateway provisioned in the `jscom-blog` project:

```hcl
data "terraform_remote_state" "jscom_blog" {
  backend = "s3"
  config = {
    bucket = "jscom-tf-backend"
    key    = "jscom-blog/terraform.tfstate"
    region = "us-east-1"
  }
}
```

**Imported from jscom-blog:**
- `api_gateway_id` - API Gateway instance ID
- `api_gateway_execution_arn` - Execution ARN for Lambda permissions
- `custom_domain_name` - api.johnsosoka.com
- `custom_domain_name_target` - CloudFront distribution target

The contact services add routes and integrations to this shared API Gateway.

### Terraform Modules (jscom-tf-modules)

**lambda-authorizer module:**
- Provides custom authorizer for API Gateway v2
- Handles x-api-key validation
- Used by admin API endpoints

## Project Structure

```
jscom-contact-services/
├── lambdas/
│   ├── src/                           # Lambda function source code
│   │   ├── contact-listener/
│   │   │   ├── app/                   # Python source
│   │   │   │   └── contact_listener_lambda.py
│   │   │   ├── requirements.txt
│   │   │   └── .venv/                 # Virtual environment (local dev)
│   │   ├── contact-filter/
│   │   │   ├── app/
│   │   │   │   └── contact_filter_lambda.py
│   │   │   ├── test/                  # Unit tests for contact-filter
│   │   │   ├── requirements.txt
│   │   │   └── .venv/
│   │   ├── contact-notifier/
│   │   │   ├── app/
│   │   │   │   ├── contact_notifier_lambda.py
│   │   │   │   └── notification_methods/  # Email, Discord plugins
│   │   │   ├── requirements.txt
│   │   │   └── .venv/
│   │   └── contact-admin/
│   │       ├── app/
│   │       │   ├── contact_admin_lambda.py
│   │       │   ├── handlers/          # Message & blocked contact logic
│   │       │   ├── models/            # Pydantic models
│   │       │   └── utils/             # DynamoDB helpers
│   │       ├── requirements.txt
│   │       └── .venv/
│   └── test/                          # Centralized integration tests
│       ├── test_contact_listener.py
│       ├── test_contact_notifier_lambda.py
│       ├── test_contact_admin.py
│       └── test_discord_method.py
├── terraform/
│   ├── main.tf                        # Provider, backend, remote state
│   ├── lambdas.tf                     # Lambda function modules
│   ├── api-gateway.tf                 # Routes, integrations, authorizer
│   ├── dynamoDB.tf                    # Tables (messages, blocked_contacts)
│   ├── sqs.tf                         # Queues (message, notify)
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars               # Sensitive config (NOT in git)
├── docs/
│   └── llm/                           # Additional LLM documentation
├── postman/                           # API testing collections
├── llm_docs/                          # Agent reports and findings
├── CLAUDE.md
└── README.md
```

## Python Development

### Virtual Environments

Each Lambda has an isolated virtual environment for local development:

```bash
# Example: Working with contact-notifier
cd lambdas/src/contact-notifier
source .venv/bin/activate
pip install -r requirements.txt
```

**Virtual Environment Locations:**
- `lambdas/src/contact-listener/.venv/`
- `lambdas/src/contact-filter/.venv/`
- `lambdas/src/contact-notifier/.venv/`
- `lambdas/src/contact-admin/.venv/`

**Important:** Virtual environments are for local development/testing ONLY. Lambda deployment packages are built by Terraform using Docker (`build_in_docker = true`) to ensure Linux runtime compatibility.

### Testing

Tests are organized in two locations:

**Centralized Tests** (`lambdas/test/`):
- Integration tests covering end-to-end Lambda behavior
- `test_contact_listener.py`
- `test_contact_notifier_lambda.py`
- `test_contact_admin.py`
- `test_discord_method.py`

**Function-Specific Tests** (`lambdas/src/<function>/test/`):
- Currently only `contact-filter` has local unit tests
- Other functions rely on centralized tests

**Running Tests:**

```bash
# Run centralized tests
cd lambdas
python -m pytest test/ -v

# Run specific test file
python -m pytest test/test_contact_admin.py -v

# Run contact-filter unit tests
cd src/contact-filter
source .venv/bin/activate
python -m pytest test/ -v
```

### Python Runtime

All Lambdas use **Python 3.13** on Amazon Linux 2023 runtime.

### Key Dependencies

- **boto3**: AWS SDK (DynamoDB, SQS, SES)
- **aws-lambda-powertools**: Logging, routing (admin Lambda)
- **pydantic>=2.0.0**: Type-safe models (admin Lambda)
- **Jinja2**: HTML email templates (notifier)
- **pytest, moto**: Testing framework and AWS mocking

## Terraform Operations

### Prerequisites

```bash
export AWS_PROFILE=jscom
cd terraform
```

### Standard Workflow

```bash
# Initialize (first time or after module changes)
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply
```

**Remote State:**
- Backend: S3 bucket `jscom-tf-backend`
- State file: `jscom-contact-services/terraform.tfstate`
- Locking: DynamoDB table `terraform-locks`

### Lambda Deployment

Lambda code changes trigger automatic redeployment via Terraform:

```bash
# After modifying Lambda source
cd terraform
terraform apply
```

Terraform uses `build_in_docker = true` to:
- Install Python dependencies in Linux-compatible containers
- Build deployment packages automatically
- Handle architecture differences (Apple Silicon → x86_64 Lambda)

**Special Case:** `contact-admin` Lambda uses `docker_additional_options = ["--platform", "linux/amd64"]` to force x86_64 builds on ARM64 hosts.

## API Reference

### Public Endpoints

**Submit Contact Form**

```http
POST https://api.johnsosoka.com/v1/contact
Content-Type: application/json

# Standard Contact
{
  "contact_name": "John Doe",
  "contact_email": "john.doe@example.com",
  "contact_message": "Hello, this is a test message."
}

# Consulting Contact
{
  "contact_name": "Jane Smith",
  "contact_email": "jane@company.com",
  "contact_message": "Interested in consulting services.",
  "company_name": "Acme Corp",
  "industry": "Technology",
  "consulting_contact": true
}

# Response (200 OK)
{
  "message": "Message Received. Currently Processing"
}

# Error (400 Bad Request)
{
  "error": "contact_message is a required field"
}
```

### Admin Endpoints

All admin endpoints require `x-api-key` header.

**Get Statistics**
```http
GET https://api.johnsosoka.com/v1/contact/admin/stats
x-api-key: <your-api-key>
```

**List Messages** (with pagination and filtering)
```http
GET https://api.johnsosoka.com/v1/contact/admin/messages?limit=20&contact_type=standard
x-api-key: <your-api-key>
```

**Get Single Message**
```http
GET https://api.johnsosoka.com/v1/contact/admin/messages/{message_id}
x-api-key: <your-api-key>
```

**List Blocked Contacts**
```http
GET https://api.johnsosoka.com/v1/contact/admin/blocked
x-api-key: <your-api-key>
```

**Block Contact**
```http
POST https://api.johnsosoka.com/v1/contact/admin/blocked
x-api-key: <your-api-key>
Content-Type: application/json

{
  "ip_address": "192.168.1.100",
  "user_agent": "BadBot/1.0"
}
```

**Unblock Contact**
```http
DELETE https://api.johnsosoka.com/v1/contact/admin/blocked/{contact_id}
x-api-key: <your-api-key>
```

See README.md for full API documentation with response examples.

## AWS Resources

### DynamoDB Tables

**all-contact-messages**
- Primary key: `id` (UUID string)
- Attributes: `contact_email`, `contact_message`, `contact_name`, `ip_address`, `user_agent`, `timestamp`, `is_blocked`, `contact_type`
- Optional consulting fields: `company_name`, `industry`
- Stores ALL submissions regardless of blocked status

**blocked_contacts**
- Primary key: `id` (UUID string)
- Attributes: `ip_address`, `user_agent`, `is_blocked` (always 1)
- Used for IP-based blocking in contact-filter Lambda

### SQS Queues

**contact-message-queue**
- Source: contact-listener Lambda
- Consumer: contact-filter Lambda
- Purpose: Buffer raw contact submissions

**contact-notify-queue**
- Source: contact-filter Lambda
- Consumer: contact-notifier Lambda
- Purpose: Buffer validated messages for notification

### API Gateway Integration

Routes added to shared API Gateway from jscom-blog:

**Public Route:**
- `POST /v1/contact` → contact-listener Lambda
- Payload format version: 2.0 (API Gateway v2)

**Admin Route:**
- `ANY /v1/contact/admin/{proxy+}` → contact-admin Lambda
- Authorization: Custom Lambda authorizer
- Validates x-api-key header before invocation

## Key Implementation Details

### Contact Types

Two form types distinguished by `consulting_contact` boolean:

- **Standard**: Basic form (name, email, message)
- **Consulting**: Extended form with `company_name` and `industry`

The `contact_type` field flows through entire pipeline and affects email template formatting.

### Request Context Extraction

`contact-listener` extracts metadata from API Gateway v2 event:
- IP Address: `event['requestContext']['http']['sourceIp']`
- User Agent: `event['requestContext']['http']['userAgent']`

### Blocking Logic

`contact-filter` scans `blocked_contacts` by IP address:
- Match found → Write to `all-contact-messages` with `is_blocked = 1`, do NOT forward to notify queue
- No match → Write to `all-contact-messages` with `is_blocked = 0`, forward to notify queue
- All SQS messages deleted manually after processing

### Notification Methods

`contact-notifier` uses plugin-based system controlled by environment variables:

**Email Notifications** (`EMAIL_ENABLED=true`):
- Sender: `mail@johnsosoka.com` (configured via `EMAIL_SENDER`)
- Recipient: `im@johnsosoka.com` (configured via `EMAIL_RECIPIENT`)
- HTML templates with different formatting for consulting vs standard
- Sent via AWS SES

**Discord Notifications** (`DISCORD_ENABLED=true`):
- Webhook URL configured via `DISCORD_WEBHOOK_URL` variable
- Rich embed format with metadata fields
- Optional - can be disabled independently of email

Both notification methods can run simultaneously.

### Admin API Patterns

**Technology Stack:**
- AWS Lambda Powertools `APIGatewayRestResolver` for routing
- Pydantic v2 for request/response validation
- Type hints using modern Python 3.11+ syntax (`str | None`, `list[T]`)

**Pagination:**
- Uses DynamoDB `LastEvaluatedKey` for cursor-based pagination
- Tokens are base64-encoded JSON
- Empty `next_token` indicates no more results

**Error Handling:**
- Pydantic ValidationError → 400 response
- ValueError → 400 response
- Generic exceptions → 500 response
- All errors logged via Lambda Powertools

## Development Workflow

### Creating a New Feature Branch

```bash
cd jscom-contact-services
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Check for relevant GitHub issues
gh issue list
```

### Making Changes

1. Modify Lambda source code in `lambdas/src/<function>/app/`
2. Update tests in `lambdas/test/` or function-specific test directory
3. Run tests locally to verify changes
4. Update Terraform if infrastructure changes needed

### Testing Changes

```bash
# Run relevant tests
cd lambdas
python -m pytest test/test_<your_function>.py -v

# Test Terraform changes
cd terraform
terraform plan
```

### Deploying Changes

```bash
cd terraform
export AWS_PROFILE=jscom
terraform apply
```

### Creating a Pull Request

```bash
# Ensure changes are committed
git add .
git commit -m "Description of changes"

# Push branch
git push -u origin feature/your-feature-name

# Create PR
gh pr create --title "Feature: Your Feature Name" --body "Description of changes"
```

## Configuration

### Environment Variables (Terraform)

Sensitive configuration in `terraform/terraform.tfvars` (NOT in git):

```hcl
admin_api_key_value = "your-secure-api-key"  # Generate with: openssl rand -hex 32
discord_webhook_url = "https://discord.com/api/webhooks/..."  # Optional
email_notifications_enabled = "true"
discord_notifications_enabled = "true"
email_sender = "mail@johnsosoka.com"
email_recipient = "im@johnsosoka.com"
```

Use `terraform.tfvars.example` as template.

### Lambda Environment Variables

Automatically configured by Terraform:

**contact-listener:**
- `CONTACT_MESSAGE_QUEUE_URL`

**contact-filter:**
- `CONTACT_MESSAGE_QUEUE_URL`
- `CONTACT_NOTIFY_QUEUE_URL`
- `ALL_CONTACT_MESSAGES_TABLE_NAME`
- `BLOCKED_CONTACTS_TABLE_NAME`

**contact-notifier:**
- `CONTACT_NOTIFY_QUEUE`
- `EMAIL_ENABLED`
- `EMAIL_SENDER`
- `EMAIL_RECIPIENT`
- `DISCORD_ENABLED`
- `DISCORD_WEBHOOK_URL`

**contact-admin:**
- `ALL_CONTACT_MESSAGES_TABLE_NAME`
- `BLOCKED_CONTACTS_TABLE_NAME`

## Common Tasks

### Adding a New Notification Method

1. Create new method class in `lambdas/src/contact-notifier/app/notification_methods/`
2. Inherit from `NotificationMethod` base class
3. Implement `send()` method
4. Register in `contact_notifier_lambda.py`
5. Add environment variable for enable/disable toggle
6. Update Terraform variables in `terraform/variables.tf`
7. Update tests in `lambdas/test/`

### Modifying DynamoDB Schema

1. Update table definition in `terraform/dynamoDB.tf`
2. Update Pydantic models in `lambdas/src/contact-admin/app/models/`
3. Update DynamoDB helper functions in `utils/dynamodb_helper.py`
4. Run `terraform apply` (note: may require table recreation)
5. Update tests to reflect new schema

### Changing API Routes

1. Update route in `terraform/api-gateway.tf`
2. If admin route: Update handler in `lambdas/src/contact-admin/app/contact_admin_lambda.py`
3. If public route: Update integration mapping
4. Run `terraform apply`
5. Test endpoint with curl or Postman

### Rotating Admin API Key

```bash
# Generate new key
openssl rand -hex 32

# Update terraform.tfvars
# admin_api_key_value = "<new-key>"

# Apply changes
cd terraform
terraform apply

# Update any external systems using the API
```

## Monitoring and Debugging

### CloudWatch Logs

Lambda log groups follow pattern: `/aws/lambda/<function-name>`

```bash
# View logs using AWS CLI
aws logs tail /aws/lambda/contact-listener --follow

# View specific time range
aws logs tail /aws/lambda/contact-admin --since 1h
```

### Key Metrics to Monitor

- API Gateway 4xx/5xx error rates
- Lambda invocation errors and throttling
- SQS queue depth (message backlog)
- DynamoDB read/write capacity utilization
- SES bounce/complaint rates

### Debugging Tips

**Contact submissions not being processed:**
1. Check CloudWatch logs for contact-listener Lambda
2. Verify SQS queue depth - messages backing up?
3. Check contact-filter Lambda for errors
4. Verify DynamoDB tables are accessible

**Admin API returning 403:**
1. Verify x-api-key header is present and correct
2. Check contact-admin-authorizer CloudWatch logs
3. Confirm API key matches Terraform variable

**Notifications not sending:**
1. Check contact-notifier CloudWatch logs
2. Verify SES sender/recipient are verified in SES console
3. Check Discord webhook URL is valid
4. Verify EMAIL_ENABLED/DISCORD_ENABLED environment variables

## Security Considerations

### API Key Management
- Generate strong keys: `openssl rand -hex 32`
- Store in `terraform.tfvars` (excluded from git)
- Rotate periodically
- Monitor CloudWatch logs for failed authorization attempts

### IAM Permissions
All Lambda functions follow least-privilege principle:
- contact-listener: SQS SendMessage only
- contact-filter: SQS Read/Write, DynamoDB Read/Write on specific tables
- contact-notifier: SQS Read/Delete, SES SendEmail
- contact-admin: DynamoDB Read/Write on specific tables only

### Input Validation
- API Gateway validates Content-Type headers
- Lambda functions validate payload structure
- Pydantic models provide type-safe validation in admin API
- All inputs sanitized before storage

### Network Security
- All endpoints use HTTPS (enforced by API Gateway)
- No public IP addresses or VPC required (serverless)
- Lambda functions access AWS services via IAM roles (no credentials in code)

## Turnstile Integration

This project uses Cloudflare Turnstile for CAPTCHA protection on contact form submissions.

**Key Components:**
- `lambdas/src/contact-listener/app/turnstile.py` - Validation module with site-to-secret mapping
- `SITE_SECRET_MAP` - Maps site domains to AWS Parameter Store paths
- Parameter Store pattern: `/jscom/turnstile/{site-name}/secret-key`

**Adding a New Site:**

See comprehensive guide at `docs/turnstile-integration.md` for:
- Step-by-step setup instructions
- Frontend integration examples (Next.js, Jekyll, vanilla JS)
- Testing with Cloudflare test keys
- Troubleshooting common issues
- Security best practices

**Quick Add:**
1. Create Turnstile widget in Cloudflare Dashboard
2. Store secret: `aws ssm put-parameter --name "/jscom/turnstile/{site}/secret-key" --value "SECRET" --type SecureString`
3. Add to `SITE_SECRET_MAP` in `turnstile.py`
4. Deploy via Terraform

## Additional Documentation

See `docs/llm/` for additional LLM-focused documentation and `llm_docs/` for agent reports and findings.

## Troubleshooting

### Terraform Issues

**State lock error:**
```bash
# Force unlock (use with caution)
terraform force-unlock <lock-id>
```

**Module not found:**
```bash
terraform init -upgrade
```

### Lambda Issues

**Import errors in Lambda:**
- Ensure dependencies in `requirements.txt`
- Verify `build_in_docker = true` in Terraform
- Check CloudWatch logs for detailed error

**Lambda timeout:**
- Default timeout may be too low for large DynamoDB scans
- Update `timeout` in Lambda module configuration

### API Gateway Issues

**CORS errors:**
- API Gateway CORS configuration is managed in jscom-blog project
- Contact jscom-blog repository for CORS changes

**404 Not Found:**
- Verify route exists in `terraform/api-gateway.tf`
- Check API Gateway deployment stage
- Confirm custom domain mapping in jscom-blog

## Links

- [GitHub Repository](https://github.com/johnsosoka/jscom-contact-services)
- [jscom-tf-modules](https://github.com/johnsosoka/jscom-tf-modules)
- [jscom-blog (API Gateway owner)](https://github.com/johnsosoka/jscom-blog)
- [Production API](https://api.johnsosoka.com/v1/contact)
