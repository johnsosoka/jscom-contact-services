The README you provided is already quite detailed and provides a good overview of the project. However, adding an API Methods section with example JSON payloads would indeed be beneficial for users who want to interact with the API. Here's a revised version of the README with the suggested changes:

---

# JSCOM Contact Services

This repository contains the source code for the JSCOM Contact Services, a serverless application that handles contact form submissions. The application is built using AWS services, including API Gateway, Lambda, DynamoDB, and SQS, and is managed using Terraform.

## Architecture

The application consists of five AWS Lambda functions, an API Gateway with custom authorizer, two DynamoDB tables, and two SQS queues.

The architecture follows two main flows:

### Contact Form Flow (Public API)
1. Contact form submissions are sent to API Gateway at `POST /v1/contact`
2. The API Gateway triggers the `contact-listener` Lambda function
3. The `contact-listener` validates the incoming message and forwards it to the `contact-message-queue`
4. The `contact-filter` Lambda function is triggered by new messages in `contact-message-queue`
   - Checks the `blocked_contacts` DynamoDB table to see if the sender is blocked
   - Writes all messages to the `all-contact-messages` DynamoDB table
   - Forwards non-blocked messages to the `contact-notify-queue`
5. The `contact-notifier` Lambda function is triggered by the `contact-notify-queue` and sends notifications to the admin via:
   - Email (AWS SES)
   - Discord webhook (optional)

### Admin API Flow (Protected API)
1. Admin requests are sent to API Gateway at `/v1/contact/admin/*` endpoints
2. API Gateway invokes the `contact-admin-authorizer` Lambda to validate the `x-api-key` header
3. If authorized, the request is routed to the `contact-admin` Lambda function
4. The admin Lambda performs CRUD operations on DynamoDB tables:
   - List/view contact messages with pagination and filtering
   - Get system statistics (message counts, recent activity)
   - List blocked contacts
   - Block/unblock IP addresses
5. Results are returned as JSON responses

### Authentication & Authorization

The admin endpoints are protected by a custom Lambda authorizer that:
- Validates the `x-api-key` header against a securely stored API key (Terraform variable)
- Returns a simple boolean authorization response to API Gateway v2
- Runs before the admin Lambda is invoked, providing request-level security
- Logs all authorization attempts for audit purposes

## Resources

### Lambda Functions

All Lambda functions are written in Python 3.13.

#### Public API Lambdas

- **`contact-listener`**: Receives contact form submissions from API Gateway, performs validation, and forwards messages to SQS. [Source Code](https://github.com/johnsosoka/jscom-contact-services/blob/main/lambdas/src/contact-listener/app/contact_listener_lambda.py)

- **`contact-filter`**: Event-driven function triggered by SQS. Checks `blocked_contacts` DynamoDB table, writes all messages to `all-contact-messages`, and forwards valid messages to the notify queue. [Source Code](https://github.com/johnsosoka/jscom-contact-services/blob/main/lambdas/src/contact-filter/app/contact_filter_lambda.py)

- **`contact-notifier`**: Event-driven function triggered by SQS. Formats and sends notifications via AWS SES (email) and Discord webhook. Uses Jinja2 templates for HTML email formatting. [Source Code](https://github.com/johnsosoka/jscom-contact-services/blob/main/lambdas/src/contact-notifier/app/contact_notifier_lambda.py)

#### Admin API Lambdas

- **`contact-admin`**: REST API Lambda providing admin endpoints for managing contact messages and blocked contacts. Uses AWS Lambda Powertools for routing and Pydantic v2 for data validation. Supports pagination, filtering, and statistics. [Source Code](https://github.com/johnsosoka/jscom-contact-services/blob/main/lambdas/src/contact-admin/app/contact_admin_lambda.py)

- **`contact-admin-authorizer`**: Custom Lambda authorizer for API Gateway v2. Validates `x-api-key` header against environment variable. Returns simple boolean authorization response. [Source Code](https://github.com/johnsosoka/jscom-contact-services/blob/main/lambdas/src/contact-admin-authorizer/app/contact_admin_authorizer_lambda.py)

### DynamoDB Tables

- `all-contact-messages`: This table stores all contact messages. It has the following attributes: `id`, `timestamp`, `sender_name`, `sender_email`, `message_body`, and `is_blocked`. It also has global secondary indexes on `sender_name`, `sender_email`, `is_blocked`, and `message_body`.

- `blocked_contacts`: This table tracks blocked contacts. It has the following attributes: `id`, `ip_address`, `user_agent`, and `is_blocked`. It also has global secondary indexes on `ip_address`, `user_agent`, `is_blocked`, and a composite index on `ip_address` and `user_agent`.

### SQS Queues

- `contact-message-queue`: This queue holds messages received from the `contact-listener` Lambda function.

- `contact-notify-queue`: This queue holds messages that have been filtered by the `contact-filter` Lambda function and are ready to be sent to the admin email by the `contact-notifier` Lambda function.

## API Methods

### Public Endpoints

#### Submit Contact Form
- `POST https://api.johnsosoka.com/v1/contact`: Submits a new contact form message.

**Request Body:**
```json
{
  "contact_name": "John Doe",
  "contact_email": "john.doe@example.com",
  "contact_message": "Hello, this is a test message."
}
```

**Consulting Contact Form** (includes additional fields):
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

### Admin Endpoints

All admin endpoints require authentication via API key in the `x-api-key` header.

#### Get System Statistics
- `GET https://api.johnsosoka.com/v1/contact/admin/stats`

**Headers:**
```
x-api-key: <your-api-key>
```

**Response:**
```json
{
  "status": 200,
  "data": {
    "total_messages": 42,
    "blocked_count": 0,
    "unblocked_count": 42,
    "total_blocked_ips": 0,
    "recent_messages_24h": 3,
    "consulting_messages": 5,
    "standard_messages": 37
  },
  "error": null
}
```

#### List Contact Messages
- `GET https://api.johnsosoka.com/v1/contact/admin/messages?limit=20&contact_type=standard`

**Query Parameters:**
- `limit` (optional): Number of messages to return (1-100, default: 20)
- `next_token` (optional): Pagination token from previous response
- `contact_type` (optional): Filter by type (`standard` or `consulting`)

**Headers:**
```
x-api-key: <your-api-key>
```

**Response:**
```json
{
  "status": 200,
  "data": {
    "messages": [
      {
        "id": "uuid-string",
        "contact_email": "john@example.com",
        "contact_message": "Hello!",
        "contact_name": "John Doe",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
        "timestamp": 1729305600,
        "is_blocked": 0,
        "contact_type": "standard"
      }
    ],
    "next_token": "base64-encoded-token",
    "total_count": 42
  },
  "error": null
}
```

#### Get Single Message
- `GET https://api.johnsosoka.com/v1/contact/admin/messages/{message_id}`

**Headers:**
```
x-api-key: <your-api-key>
```

**Response:**
```json
{
  "status": 200,
  "data": {
    "id": "uuid-string",
    "contact_email": "john@example.com",
    "contact_message": "Hello!",
    "contact_name": "John Doe",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "timestamp": 1729305600,
    "is_blocked": 0,
    "contact_type": "standard"
  },
  "error": null
}
```

#### List Blocked Contacts
- `GET https://api.johnsosoka.com/v1/contact/admin/blocked`

**Headers:**
```
x-api-key: <your-api-key>
```

**Response:**
```json
{
  "status": 200,
  "data": [
    {
      "id": "uuid-string",
      "ip_address": "192.168.1.100",
      "user_agent": "BadBot/1.0",
      "is_blocked": 1
    }
  ],
  "error": null
}
```

#### Block Contact
- `POST https://api.johnsosoka.com/v1/contact/admin/blocked`

**Headers:**
```
x-api-key: <your-api-key>
Content-Type: application/json
```

**Request Body:**
```json
{
  "ip_address": "192.168.1.100",
  "user_agent": "BadBot/1.0"
}
```

**Response:**
```json
{
  "status": 200,
  "data": {
    "id": "uuid-string",
    "ip_address": "192.168.1.100",
    "user_agent": "BadBot/1.0",
    "is_blocked": 1
  },
  "error": null
}
```

#### Unblock Contact
- `DELETE https://api.johnsosoka.com/v1/contact/admin/blocked/{contact_id}`

**Headers:**
```
x-api-key: <your-api-key>
```

**Response:**
```json
{
  "status": 200,
  "data": {
    "message": "Contact unblocked successfully"
  },
  "error": null
}
```

## Deployment

The application is deployed using Terraform. The Terraform configuration files are located in the `terraform` directory. The Terraform state is managed remotely in an S3 bucket with DynamoDB state locking.

### Prerequisites

1. AWS CLI configured with the `jscom` profile
2. Terraform installed (v1.0+)
3. API key for admin endpoints (generate with `openssl rand -hex 32`)
4. Discord webhook URL (optional, for Discord notifications)

### Configuration

1. Create a `terraform.tfvars` file in the `terraform/` directory:

```hcl
admin_api_key_value = "your-secure-api-key-here"
discord_webhook_url = "your-discord-webhook-url" # optional
```

**Security Note**: Never commit `terraform.tfvars` to version control. Use the provided `terraform.tfvars.example` as a template.

### Deploy

Navigate to the `terraform` directory and run:

```bash
cd terraform
export AWS_PROFILE=jscom

# Initialize Terraform (first time only)
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply
```

### Lambda Deployment

Lambda functions are built and deployed automatically by Terraform:
- Python dependencies are installed in Docker containers to ensure Linux compatibility
- Functions targeting x86_64 architecture (important for Apple Silicon Macs)
- Source code changes trigger automatic redeployment

### Testing Deployment

Test the public API:
```bash
curl -X POST https://api.johnsosoka.com/v1/contact \
  -H "Content-Type: application/json" \
  -d '{"contact_name": "Test", "contact_email": "test@example.com", "contact_message": "Test message"}'
```

Test the admin API:
```bash
curl -X GET https://api.johnsosoka.com/v1/contact/admin/stats \
  -H "x-api-key: your-api-key-here"
```

## Security

### API Key Management

The admin API key is managed as a Terraform variable and stored as an environment variable in the Lambda authorizer. Best practices:
- Generate strong API keys: `openssl rand -hex 32`
- Store in `terraform.tfvars` (excluded from git via `.gitignore`)
- Rotate keys periodically by updating the Terraform variable and redeploying
- Monitor CloudWatch logs for unauthorized access attempts

### IAM Permissions

Lambda functions follow the principle of least privilege:
- `contact-listener`: SQS SendMessage only
- `contact-filter`: SQS ReceiveMessage/DeleteMessage, DynamoDB Read/Write on specific tables
- `contact-notifier`: SQS ReceiveMessage/DeleteMessage, SES SendEmail
- `contact-admin`: DynamoDB Read/Write on specific tables only
- `contact-admin-authorizer`: No AWS permissions required (reads environment variable)

### Network Security

- All API endpoints use HTTPS (enforced by API Gateway)
- Admin endpoints protected by Lambda authorizer
- No public IP addresses or VPC required (serverless architecture)
