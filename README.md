The README you provided is already quite detailed and provides a good overview of the project. However, adding an API Methods section with example JSON payloads would indeed be beneficial for users who want to interact with the API. Here's a revised version of the README with the suggested changes:

---

# JSCOM Contact Services

This repository contains the source code for the JSCOM Contact Services, a serverless application that handles contact form submissions. The application is built using AWS services, including API Gateway, Lambda, DynamoDB, and SQS, and is managed using Terraform.

## Architecture

The application consists of four AWS Lambda functions, an API Gateway, two DynamoDB tables, and two SQS queues.

The architecture follows this flow:

### Contact Form Flow
1. Contact form submissions are sent to the API Gateway.
2. The API Gateway triggers the `contact-listener` Lambda function.
3. The `contact-listener` Lambda function validates the incoming message and forwards it to the `contact-message-queue`.
4. The `contact-filter` Lambda function is triggered by the new message in the `contact-message-queue`. It checks if the sender is blocked. If not, the message is forwarded to the `contact-notify-queue`.
5. The `contact-notifier` Lambda function is triggered by the new message in the `contact-notify-queue` and sends an email to the admin.

### Admin API Flow
1. Admin requests are sent to the API Gateway with an API key for authentication.
2. A custom Lambda authorizer validates the API key.
3. Authenticated requests are routed to the `contact-admin` Lambda function.
4. The admin Lambda performs CRUD operations on DynamoDB tables and returns results.

## Resources

### Lambda Functions

All Lambda functions are written in Python.

- `contact-listener`: This function receives contact form submissions from the API Gateway, performs simple validation, and forwards the messages to the `contact-message-queue`. [Source Code](https://github.com/johnsosoka/jscom-contact-services/blob/main/lambdas/src/contact-listener/app/contact_listener_lambda.py)

- `contact-filter`: This function filters blocked contact messages from the `contact-message-queue`. It checks the `blocked_contacts` DynamoDB table to see if the sender is blocked. Valid messages are forwarded to the `contact-notify-queue`. [Source Code](https://github.com/johnsosoka/jscom-contact-services/blob/main/lambdas/src/contact-filter/app/contact_filter_lambda.py)

- `contact-notifier`: This function receives messages from the `contact-notify-queue`, formats them, and sends them to the admin email. [Source Code](https://github.com/johnsosoka/jscom-contact-services/blob/main/lambdas/src/contact-notifier/app/contact_notifier_lambda.py)

- `contact-admin`: This function provides admin API endpoints for managing contact messages and blocked contacts. Requires API key authentication. [Source Code](https://github.com/johnsosoka/jscom-contact-services/blob/main/lambdas/src/contact-admin/app/contact_admin_lambda.py)

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
- `GET https://api.johnsosoka.com/admin/stats`

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
- `GET https://api.johnsosoka.com/admin/messages?limit=20&contact_type=standard`

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
- `GET https://api.johnsosoka.com/admin/messages/{message_id}`

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
- `GET https://api.johnsosoka.com/admin/blocked`

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
- `POST https://api.johnsosoka.com/admin/blocked`

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
- `DELETE https://api.johnsosoka.com/admin/blocked/{contact_id}`

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

The application is deployed using Terraform. The Terraform configuration files are located in the `terraform` directory. The Terraform state is managed remotely in an S3 bucket.

To deploy the application, navigate to the `terraform` directory and run the following commands:

```bash
terraform init
terraform apply
```
