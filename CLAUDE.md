# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Serverless contact form API system built on AWS Lambda, API Gateway, SQS, and DynamoDB. The system processes contact form submissions through an event-driven architecture with filtering and notification capabilities.

## Architecture

Event-driven serverless pipeline with three Lambda functions:

1. **API Gateway** → `contact-listener` Lambda
   - Receives POST requests at `/v1/contact`
   - Validates payload (requires `contact_message`)
   - Extracts IP address and user agent from request context
   - Supports two contact types: `standard` and `consulting`
   - Forwards to `contact-message-queue` SQS

2. **contact-message-queue** → `contact-filter` Lambda
   - Checks `blocked_contacts` DynamoDB table by IP address
   - Writes all messages to `all-contact-messages` DynamoDB
   - Forwards non-blocked messages to `contact-notify-queue`

3. **contact-notify-queue** → `contact-notifier` Lambda
   - Formats HTML email (different templates for consulting vs standard)
   - Sends via AWS SES to im@johnsosoka.com
   - Deletes processed messages from queue

## Project Structure

```
lambdas/
  src/
    contact-listener/
      app/contact_listener_lambda.py
      test/                    # Unit tests for contact-listener
      requirements.txt
      .venv/                   # Virtual environment for local development
    contact-filter/
      app/contact_filter_lambda.py
      test/                    # Unit tests for contact-filter
      requirements.txt
      .venv/                   # Virtual environment for local development
    contact-notifier/
      app/contact_notifier_lambda.py
      test/                    # Unit tests for contact-notifier
      requirements.txt
      .venv/                   # Virtual environment for local development
    contact-admin/
      app/contact_admin_lambda.py
      test/                    # Unit tests for contact-admin
      requirements.txt
      .venv/                   # Virtual environment for local development
    contact-admin-authorizer/
      app/contact_admin_authorizer_lambda.py
      test/                    # Unit tests for contact-admin-authorizer
      requirements.txt
      .venv/                   # Virtual environment for local development

terraform/
  main.tf              # Provider, backend, remote state references
  lambdas.tf           # Lambda function modules and event source mappings
  api-gateway.tf       # API Gateway v2 integration and route
  dynamoDB.tf          # DynamoDB tables
  sqs.tf               # SQS queues
  variables.tf         # Terraform variables
  terraform.tfvars     # Sensitive configuration (not in version control)

test/
  prod_test_report.md  # Production regression test results
```

**Note:** Each Lambda function has its own `test/` directory within its module for unit tests, allowing independent test dependencies and virtual environments per function.

### Python Development Environment

Each Lambda function has its own isolated virtual environment for local development and testing:

**Virtual Environment Locations:**
- `lambdas/src/contact-listener/.venv/`
- `lambdas/src/contact-filter/.venv/`
- `lambdas/src/contact-notifier/.venv/`
- `lambdas/src/contact-admin/.venv/`
- `lambdas/src/contact-admin-authorizer/.venv/`

**Activating a Virtual Environment:**
```bash
# From project root
cd lambdas/src/contact-notifier
source .venv/bin/activate

# Or from lambdas directory
source src/contact-notifier/.venv/bin/activate
```

**Installing Dependencies:**
```bash
# Activate the virtual environment first, then:
pip install -r requirements.txt

# For development/testing dependencies:
pip install pytest moto boto3
```

**Running Tests:**
Each Lambda function has its own `test/` directory within its module for unit tests. This allows each function to have independent test dependencies and virtual environments.

```bash
# Run tests for a specific Lambda function
cd lambdas/src/contact-notifier
source .venv/bin/activate
python -m pytest test/ -v

# Or run a specific test file
python -m pytest test/test_notifier.py -v
```

**Test Structure:**
- `lambdas/src/contact-listener/test/` - Unit tests for contact-listener
- `lambdas/src/contact-filter/test/` - Unit tests for contact-filter
- `lambdas/src/contact-notifier/test/` - Unit tests for contact-notifier
- `lambdas/src/contact-admin/test/` - Unit tests for contact-admin
- `lambdas/src/contact-admin-authorizer/test/` - Unit tests for contact-admin-authorizer

**Important Notes:**
- Each Lambda has isolated dependencies defined in its own `requirements.txt`
- Each Lambda has its own test directory with independent test dependencies
- Virtual environments are for local development/testing only
- Lambda deployment packages are built by Terraform using Docker (`build_in_docker = true`)
- When running Terraform commands, ensure `AWS_PROFILE=jscom` is set

## Dependencies and Infrastructure

### Remote State Dependencies

This project depends on remote Terraform state from two other projects:

- **jscom-core-infra**: Provides shared infrastructure (not directly used in current config)
- **jscom-blog**: Provides API Gateway instance that this project integrates with
  - `api_gateway_id`
  - `api_gateway_execution_arn`
  - `custom_domain_name` (api.johnsosoka.com)
  - `custom_domain_name_target`

The API Gateway is provisioned in `jscom-blog` project, and this project adds routes/integrations to it.

### AWS Resources

**Lambda Functions:**
- Runtime: Python 3.13 (Amazon Linux 2023)
- Deployment: Built in Docker via terraform-aws-modules/lambda/aws
- Each function has isolated `app/` directory and `requirements.txt`

**DynamoDB Tables:**
- `all-contact-messages`: Stores all submissions with fields: `id`, `contact_email`, `contact_message`, `contact_name`, `ip_address`, `user_agent`, `timestamp`, `is_blocked`, `contact_type`, and optional `company_name`, `industry`
- `blocked_contacts`: Tracks blocked IPs with fields: `id`, `ip_address`, `user_agent`, `is_blocked`

**SQS Queues:**
- `contact-message-queue`: Receives from contact-listener
- `contact-notify-queue`: Receives from contact-filter

## Development Commands

### Terraform

When running terraform locally, ensure the current AWS_PROFILE is jscom.

Navigate to `terraform/` directory for all infrastructure operations:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

**Note**: Terraform state is managed remotely in S3 bucket `jscom-tf-backend` with DynamoDB locking.

### Testing Lambda Functions

Each Lambda function has its own test directory with independent test dependencies and virtual environments. Tests use pytest with mocking.

```bash
# Run tests for a specific Lambda function
cd lambdas/src/contact-notifier
source .venv/bin/activate
python -m pytest test/ -v

# Run all tests for all Lambda functions (from lambdas directory)
cd lambdas
for dir in src/*/; do
  if [ -d "${dir}test" ] && [ -d "${dir}.venv" ]; then
    echo "Testing ${dir}..."
    (cd "$dir" && source .venv/bin/activate && python -m pytest test/ -v)
  fi
done
```

**Test Locations:**
- `lambdas/src/contact-listener/test/` - contact-listener unit tests
- `lambdas/src/contact-filter/test/` - contact-filter unit tests
- `lambdas/src/contact-notifier/test/` - contact-notifier unit tests
- `lambdas/src/contact-admin/test/` - contact-admin unit tests
- `lambdas/src/contact-admin-authorizer/test/` - contact-admin-authorizer unit tests

### Lambda Deployment

Lambda code is deployed via Terraform. After modifying Lambda source:

```bash
cd terraform
terraform apply
```

Terraform uses `build_in_docker = true` to build Python dependencies for Linux runtime.

## API Specification

**Endpoint**: `POST https://api.johnsosoka.com/v1/contact`

**Standard Contact Request**:
```json
{
  "contact_name": "John Doe",
  "contact_email": "john.doe@example.com",
  "contact_message": "Hello, this is a test message."
}
```

**Consulting Contact Request** (includes additional fields):
```json
{
  "contact_name": "Jane Smith",
  "contact_email": "jane@company.com",
  "contact_message": "Interested in consulting services.",
  "company_name": "Acme Corp",
  "industry": "Technology",
  "consulting_contact": true
}
```

**Response** (200 OK):
```json
{
  "message": "Message Received. Currently Processing"
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "contact_message is a required field"
}
```

## Key Implementation Details

### Contact Types

The system supports two contact form types distinguished by the `consulting_contact` boolean field:

- **Standard**: Basic contact form (name, email, message)
- **Consulting**: Extended form with `company_name` and `industry` fields

The `contact_type` field is set to `"standard"` or `"consulting"` and flows through the entire pipeline.

### Request Context Extraction

The `contact-listener` Lambda extracts metadata from API Gateway v2 event:
- IP Address: `event['requestContext']['http']['sourceIp']`
- User Agent: `event['requestContext']['http']['userAgent']`

### Blocking Logic

The `contact-filter` Lambda scans the `blocked_contacts` table by `ip_address`. If a match is found:
- Message is written to `all-contact-messages` with `is_blocked = 1`
- Message is NOT forwarded to notification queue
- SQS message is deleted from `contact-message-queue`

### Email Formatting

The `contact-notifier` Lambda generates HTML emails with different templates based on `contact_type`. Both templates include sender details and request metadata (IP, user agent).

## Important Notes

- Lambda functions manually delete SQS messages after processing (not automatic)
- All contact messages are stored in DynamoDB regardless of blocked status
- SES sender is `mail@johnsosoka.com`, recipient is `im@johnsosoka.com`
- API Gateway integration uses `payload_format_version = "2.0"` (API Gateway v2 format)
- Lambda functions use `handler` format: `<filename>.<function_name>` (e.g., `contact_listener_lambda.lambda_handler`)
