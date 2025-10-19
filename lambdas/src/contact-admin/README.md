# Contact Admin Lambda

Admin REST API Lambda function for managing contact messages and blocked contacts in the jscom-contact-services system.

## Overview

This Lambda provides administrative endpoints for:
- Viewing and searching contact messages with pagination
- Retrieving system statistics and analytics
- Managing the blocked contacts list
- Viewing individual message details

## Architecture

### Technology Stack
- **Runtime**: Python 3.13 on Amazon Linux 2023
- **Framework**: AWS Lambda Powertools (APIGatewayRestResolver)
- **Validation**: Pydantic v2 for type-safe models
- **Database**: DynamoDB (boto3 resource API)
- **Logging**: AWS Lambda Powertools Logger

### Project Structure
```
contact-admin/
├── app/
│   ├── contact_admin_lambda.py          # Main Lambda handler
│   ├── models/
│   │   ├── __init__.py
│   │   ├── domain_models.py             # ContactMessage, BlockedContact
│   │   ├── request_models.py            # API request schemas
│   │   └── response_models.py           # API response schemas
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── messages.py                  # Message CRUD operations
│   │   └── blocked_contacts.py          # Blocked contact operations
│   └── utils/
│       ├── __init__.py
│       └── dynamodb_helper.py           # DynamoDB conversion utilities
├── requirements.txt
├── .venv/                                # Virtual environment (local dev)
└── README.md
```

## API Endpoints

### GET /admin/messages
List contact messages with pagination and filtering.

**Query Parameters:**
- `limit` (int): Max messages per page (1-100, default 50)
- `next_token` (str): Pagination token
- `contact_type` (str): Filter by 'standard' or 'consulting'

**Response (200):**
```json
{
  "status": 200,
  "data": {
    "messages": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "contact_email": "john@example.com",
        "contact_message": "Interested in services",
        "contact_name": "John Doe",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
        "timestamp": 1697840000,
        "is_blocked": 0,
        "contact_type": "standard"
      }
    ],
    "next_token": "eyJpZCI6ICIuLi4ifQ==",
    "count": 50
  },
  "error": null
}
```

### GET /admin/messages/{id}
Retrieve a specific contact message.

**Path Parameters:**
- `message_id` (str): Unique message identifier

**Response (200):**
```json
{
  "status": 200,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "contact_email": "john@example.com",
    "contact_message": "Message content",
    "contact_name": "John Doe",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "timestamp": 1697840000,
    "is_blocked": 0,
    "contact_type": "standard"
  },
  "error": null
}
```

**Response (404):**
```json
{
  "status": 404,
  "data": null,
  "error": "Message not found: {message_id}"
}
```

### GET /admin/stats
Get system statistics and analytics.

**Response (200):**
```json
{
  "status": 200,
  "data": {
    "total_messages": 1250,
    "blocked_count": 45,
    "unblocked_count": 1205,
    "total_blocked_ips": 12,
    "recent_messages_24h": 23,
    "consulting_messages": 320,
    "standard_messages": 930
  },
  "error": null
}
```

### GET /admin/blocked
List all blocked contacts.

**Response (200):**
```json
{
  "status": 200,
  "data": {
    "blocked_contacts": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "ip_address": "192.168.1.100",
        "user_agent": "BadBot/1.0",
        "is_blocked": 1
      }
    ],
    "count": 12
  },
  "error": null
}
```

### POST /admin/blocked
Add an IP address to the blocked list.

**Request Body:**
```json
{
  "ip_address": "192.168.1.100",
  "user_agent": "BadBot/1.0"
}
```

**Response (201):**
```json
{
  "status": 201,
  "data": {
    "blocked_contact": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "ip_address": "192.168.1.100",
      "user_agent": "BadBot/1.0",
      "is_blocked": 1
    },
    "message": "Contact blocked successfully"
  },
  "error": null
}
```

**Response (400) - Already Blocked:**
```json
{
  "status": 400,
  "data": null,
  "error": "IP address 192.168.1.100 is already blocked"
}
```

### DELETE /admin/blocked/{id}
Remove an IP address from the blocked list.

**Path Parameters:**
- `blocked_id` (str): ID of the blocked contact record

**Response (200):**
```json
{
  "status": 200,
  "data": {
    "message": "Contact unblocked successfully"
  },
  "error": null
}
```

**Response (404):**
```json
{
  "status": 404,
  "data": null,
  "error": "Blocked contact not found: {blocked_id}"
}
```

## Environment Variables

Required environment variables for the Lambda function:

- `ALL_CONTACT_MESSAGES_TABLE_NAME`: DynamoDB table name for contact messages
- `BLOCKED_CONTACTS_TABLE_NAME`: DynamoDB table name for blocked contacts

## Local Development

### Setup Virtual Environment

```bash
cd /Users/john/code/websites/jscom-contact-services/lambdas/src/contact-admin
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Tests

```bash
# From the lambdas directory
cd /Users/john/code/websites/jscom-contact-services/lambdas
source src/contact-admin/.venv/bin/activate
python -m pytest test/test_contact_admin.py -v
```

## Dependencies

```
aws-lambda-powertools[all]>=2.0.0  # Lambda utilities and event handling
pydantic>=2.0.0                     # Type-safe data validation
```

## Key Implementation Details

### Pydantic v2 Models

All models use Pydantic v2 with modern Python 3.11+ type hints:
- `str | None` instead of `Optional[str]`
- `list[ContactMessage]` instead of `List[ContactMessage]`
- Full type coverage throughout the codebase

### AWS Lambda Powertools Integration

Uses APIGatewayRestResolver for clean route definitions:
```python
@app.get("/admin/messages")
def handle_list_messages() -> dict[str, Any]:
    # Handler implementation
```

### Pagination

Messages are paginated using DynamoDB's `LastEvaluatedKey`:
- Pagination tokens are base64-encoded JSON
- Client provides `next_token` to retrieve subsequent pages
- Empty `next_token` indicates no more results

### Error Handling

Consistent error response structure:
- Pydantic ValidationError → 400 response
- ValueError → 400 response
- Generic exceptions → 500 response
- All errors logged via AWS Lambda Powertools Logger

### DynamoDB Conversion

Helper utilities (`dynamodb_helper.py`) handle bidirectional conversion:
- `item_to_contact_message()`: DynamoDB item → ContactMessage
- `item_to_blocked_contact()`: DynamoDB item → BlockedContact
- `contact_message_to_item()`: ContactMessage → DynamoDB item
- `blocked_contact_to_item()`: BlockedContact → DynamoDB item

### Statistics Calculation

The stats endpoint scans both DynamoDB tables:
- Handles pagination for large datasets
- Calculates metrics in-memory after retrieval
- Recent messages filtered by timestamp (last 24 hours)

## Deployment

This Lambda is deployed via Terraform. The infrastructure configuration will be added to `/Users/john/code/websites/jscom-contact-services/terraform/lambdas.tf`.

### Terraform Configuration (Example)

```hcl
module "contact_admin_lambda" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "contact-admin"
  handler       = "contact_admin_lambda.lambda_handler"
  runtime       = "python3.13"
  
  source_path = "${path.module}/../lambdas/src/contact-admin/app"
  
  build_in_docker = true
  
  environment_variables = {
    ALL_CONTACT_MESSAGES_TABLE_NAME = aws_dynamodb_table.all_contact_messages.name
    BLOCKED_CONTACTS_TABLE_NAME     = aws_dynamodb_table.blocked_contacts.name
  }
  
  attach_policy_statements = true
  policy_statements = {
    dynamodb = {
      effect = "Allow"
      actions = [
        "dynamodb:GetItem",
        "dynamodb:Scan",
        "dynamodb:Query",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ]
      resources = [
        aws_dynamodb_table.all_contact_messages.arn,
        aws_dynamodb_table.blocked_contacts.arn
      ]
    }
  }
}
```

## Future Improvements

1. **Authentication/Authorization**: Add API key or JWT-based authentication
2. **Caching**: Implement caching for stats endpoint (Redis/ElastiCache)
3. **Query Optimization**: Use DynamoDB indexes for better query performance
4. **Batch Operations**: Add endpoints for bulk blocking/unblocking
5. **Audit Logging**: Track who made administrative changes
6. **Rate Limiting**: Implement request throttling for admin endpoints
7. **Search**: Add full-text search capabilities for messages
8. **Export**: Add CSV/JSON export functionality for messages
9. **Filtering**: Add more advanced filtering options (date range, IP range)
10. **Metrics**: Emit custom CloudWatch metrics for monitoring

## Design Decisions

### Use of boto3 Resource API
Chose DynamoDB resource API over client API for cleaner, more Pythonic code. The resource API handles type conversions automatically.

### Scan vs Query Operations
Currently uses scan operations for flexibility. For production at scale, consider adding GSIs (Global Secondary Indexes) and using query operations instead.

### Generic ApiResponse Wrapper
Implemented `ApiResponse[T]` generic type to ensure consistent response structure across all endpoints while maintaining type safety.

### Separate Handler Modules
Split handlers into `messages.py` and `blocked_contacts.py` for clear separation of concerns and maintainability.

### In-Memory Statistics
Stats endpoint loads all data into memory for calculation. For large datasets, consider:
- Caching computed statistics
- Using DynamoDB table metrics
- Pre-computing statistics with a scheduled Lambda

## Security Considerations

1. **Input Validation**: All inputs validated via Pydantic models
2. **SQL Injection**: Not applicable (DynamoDB NoSQL)
3. **IAM Permissions**: Lambda should have least-privilege IAM role
4. **API Authentication**: Add authentication before production deployment
5. **Rate Limiting**: Implement to prevent abuse
6. **CORS**: Configure CORS headers if accessed from browser
7. **Audit Trail**: Log all administrative actions

## Monitoring

Key metrics to monitor:
- API Gateway 4xx/5xx error rates
- Lambda duration and throttling
- DynamoDB read/write capacity utilization
- Pagination token decode failures
- Failed validation attempts

## Support

For issues or questions:
1. Check CloudWatch Logs for Lambda execution logs
2. Review API Gateway access logs
3. Verify environment variables are set correctly
4. Ensure IAM permissions are configured
