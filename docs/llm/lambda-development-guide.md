# Lambda Development Guide

Guide for developing and maintaining Python Lambda functions in jscom-contact-services.

## Project Standards

### Python Version
- **Runtime**: Python 3.13 on Amazon Linux 2023
- **Type Hints**: Modern Python 3.11+ syntax (`str | None` instead of `Optional[str]`)
- **Async**: Not required - all functions are synchronous

### Project Structure Pattern

Each Lambda function follows this structure:

```
lambdas/src/<function-name>/
├── app/                          # Source code (deployed to Lambda)
│   ├── <function>_lambda.py     # Main handler file
│   ├── handlers/                 # Optional: Handler modules
│   ├── models/                   # Optional: Data models
│   └── utils/                    # Optional: Utility functions
├── test/                         # Optional: Function-specific unit tests
├── requirements.txt              # Python dependencies
├── .venv/                        # Virtual environment (local dev only)
└── README.md                     # Optional: Function documentation
```

**Note:** Only the `app/` directory contents are deployed to Lambda. Test files and virtual environments are excluded.

## Development Workflow

### Setting Up Local Environment

```bash
# Navigate to Lambda function
cd lambdas/src/<function-name>

# Create virtual environment (if not exists)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest moto boto3
```

### Handler Pattern

All Lambda handlers follow this signature:

```python
import json
from typing import Any

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler.

    Args:
        event: Event data from trigger (API Gateway, SQS, etc.)
        context: Lambda runtime information

    Returns:
        Response dict (format depends on trigger type)
    """
    # Implementation here
    pass
```

### Event Source Patterns

#### API Gateway v2 (HTTP API)

```python
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # Extract request data
    body = json.loads(event.get('body', '{}'))
    headers = event.get('headers', {})

    # Extract request context
    request_context = event.get('requestContext', {})
    http_context = request_context.get('http', {})
    ip_address = http_context.get('sourceIp')
    user_agent = http_context.get('userAgent')

    # Process request
    result = process_request(body, ip_address, user_agent)

    # Return API Gateway v2 response
    return {
        'statusCode': 200,
        'body': json.dumps(result),
        'headers': {
            'Content-Type': 'application/json'
        }
    }
```

#### SQS Event Source

```python
import boto3

sqs = boto3.client('sqs')

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # Process each message
    for record in event['Records']:
        # Parse message body
        message_body = json.loads(record['body'])
        receipt_handle = record['receiptHandle']

        try:
            # Process message
            process_message(message_body)

            # Manually delete message from queue
            queue_url = os.environ['QUEUE_URL']
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
        except Exception as e:
            # Log error and continue
            print(f"Error processing message: {e}")
            # Message will remain in queue for retry

    return {'statusCode': 200}
```

### AWS SDK Patterns

#### DynamoDB

**Using Resource API (Recommended for CRUD):**

```python
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

# Put item
table.put_item(Item={
    'id': str(uuid.uuid4()),
    'name': 'John Doe',
    'email': 'john@example.com',
    'timestamp': int(time.time())
})

# Get item
response = table.get_item(Key={'id': item_id})
item = response.get('Item')

# Scan with pagination
response = table.scan(Limit=50)
items = response['Items']
next_token = response.get('LastEvaluatedKey')

# Query with filter
response = table.scan(
    FilterExpression='contact_type = :type',
    ExpressionAttributeValues={':type': 'consulting'}
)
```

**Using Client API (Recommended for advanced queries):**

```python
import boto3

dynamodb = boto3.client('dynamodb')

response = dynamodb.query(
    TableName=table_name,
    KeyConditionExpression='pk = :pk',
    ExpressionAttributeValues={':pk': {'S': 'USER#123'}}
)
```

#### SQS

```python
import boto3

sqs = boto3.client('sqs')

# Send message
sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps(message_data)
)

# Delete message
sqs.delete_message(
    QueueUrl=queue_url,
    ReceiptHandle=receipt_handle
)
```

#### SES (Email)

```python
import boto3

ses = boto3.client('ses')

ses.send_email(
    Source='sender@example.com',
    Destination={'ToAddresses': ['recipient@example.com']},
    Message={
        'Subject': {'Data': 'Subject Line'},
        'Body': {
            'Html': {'Data': '<html><body>HTML content</body></html>'}
        }
    }
)
```

## Testing

### Test Organization

Tests can be in two locations:

1. **Centralized tests**: `lambdas/test/test_<function>.py` (most common)
2. **Function-specific tests**: `lambdas/src/<function>/test/` (optional)

### Testing Patterns

#### Basic Unit Test with Mocking

```python
import json
import pytest
from unittest.mock import patch, MagicMock

def test_lambda_handler_success():
    # Import function
    from contact_listener_lambda import lambda_handler

    # Create event
    event = {
        'body': json.dumps({
            'contact_name': 'Test User',
            'contact_email': 'test@example.com',
            'contact_message': 'Test message'
        }),
        'requestContext': {
            'http': {
                'sourceIp': '192.168.1.1',
                'userAgent': 'Mozilla/5.0'
            }
        }
    }

    # Mock AWS SDK calls
    with patch('boto3.client') as mock_boto3:
        mock_sqs = MagicMock()
        mock_boto3.return_value = mock_sqs

        # Invoke handler
        response = lambda_handler(event, None)

        # Assertions
        assert response['statusCode'] == 200
        mock_sqs.send_message.assert_called_once()
```

#### Using moto for AWS Service Mocking

```python
import boto3
import pytest
from moto import mock_dynamodb, mock_sqs

@mock_dynamodb
@mock_sqs
def test_filter_lambda_with_aws_mocks():
    # Set up mock DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-table',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )

    # Set up mock SQS queue
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.create_queue(QueueName='test-queue')['QueueUrl']

    # Set environment variables
    import os
    os.environ['TABLE_NAME'] = 'test-table'
    os.environ['QUEUE_URL'] = queue_url

    # Import and test function
    from contact_filter_lambda import lambda_handler

    event = {
        'Records': [
            {
                'body': json.dumps({'message': 'test'}),
                'receiptHandle': 'test-handle'
            }
        ]
    }

    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
```

#### Testing API Gateway Integration

```python
def test_api_gateway_v2_event():
    event = {
        'version': '2.0',
        'routeKey': 'POST /v1/contact',
        'rawPath': '/v1/contact',
        'headers': {
            'content-type': 'application/json'
        },
        'requestContext': {
            'http': {
                'method': 'POST',
                'path': '/v1/contact',
                'sourceIp': '192.168.1.1',
                'userAgent': 'Mozilla/5.0'
            }
        },
        'body': json.dumps({
            'contact_name': 'Test',
            'contact_email': 'test@example.com',
            'contact_message': 'Test message'
        })
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'message' in body
```

### Running Tests

```bash
# Run all tests
cd lambdas
python -m pytest test/ -v

# Run specific test file
python -m pytest test/test_contact_listener.py -v

# Run specific test function
python -m pytest test/test_contact_listener.py::test_lambda_handler_success -v

# Run with coverage
python -m pytest test/ -v --cov=src --cov-report=html
```

## Common Patterns

### Environment Variable Access

```python
import os

# Required variables
QUEUE_URL = os.environ['QUEUE_URL']
TABLE_NAME = os.environ['TABLE_NAME']

# Optional variables with defaults
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
TIMEOUT = int(os.environ.get('TIMEOUT', '30'))
```

### Error Handling

```python
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        # Process request
        result = process_request(event)

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    except ValueError as e:
        # Client error (400)
        logger.error(f"Validation error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }

    except Exception as e:
        # Server error (500)
        logger.exception(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
```

### Logging

```python
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # Log incoming event (sanitize sensitive data)
    logger.info(f"Processing event: {json.dumps(event, default=str)}")

    # Log business logic
    logger.info(f"Processing message from {ip_address}")

    # Log errors
    try:
        process_message()
    except Exception as e:
        logger.exception(f"Failed to process message: {e}")
```

### Using AWS Lambda Powertools (Admin Lambda)

```python
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
app = APIGatewayRestResolver()

@app.get("/admin/messages")
def list_messages() -> dict[str, Any]:
    """List contact messages with pagination."""
    logger.info("Listing messages")
    # Implementation
    return {'status': 200, 'data': messages}

@logger.inject_lambda_context
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    return app.resolve(event, context)
```

## Dependencies Management

### Adding New Dependencies

1. Add to `requirements.txt`:
   ```
   boto3>=1.28.0
   requests>=2.31.0
   ```

2. Install locally:
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Terraform will automatically install dependencies during deployment using Docker

### Dependency Best Practices

- **Pin major versions**: `package>=1.0.0,<2.0.0`
- **boto3 is included** in Lambda runtime - specify if you need specific version
- **Keep dependencies minimal** - each dependency increases cold start time
- **Test with mocked AWS services** using `moto` to avoid AWS costs

## Deployment

### Via Terraform (Standard)

```bash
cd terraform
export AWS_PROFILE=jscom
terraform apply
```

Terraform automatically:
1. Builds deployment package using Docker
2. Installs dependencies for Linux runtime
3. Creates Lambda function or updates existing
4. Configures environment variables
5. Sets up event source mappings (SQS, etc.)

### Manual Testing (AWS CLI)

```bash
# Invoke Lambda directly
aws lambda invoke \
  --function-name contact-listener \
  --payload '{"test": "data"}' \
  --profile jscom \
  response.json

cat response.json
```

### Docker Build Configuration

Terraform uses Docker to build Lambda deployment packages:

```hcl
module "contact-listener" {
  source = "terraform-aws-modules/lambda/aws"

  runtime         = "python3.13"
  build_in_docker = true

  # Force x86_64 on ARM64 hosts (Apple Silicon)
  docker_additional_options = ["--platform", "linux/amd64"]

  source_path = [{
    path             = "${path.module}/../lambdas/src/contact-listener/app"
    pip_requirements = "${path.module}/../lambdas/src/contact-listener/requirements.txt"
  }]
}
```

## Debugging

### CloudWatch Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/contact-listener --follow --profile jscom

# View logs from last hour
aws logs tail /aws/lambda/contact-listener --since 1h --profile jscom

# Filter logs
aws logs tail /aws/lambda/contact-listener --filter-pattern "ERROR" --profile jscom
```

### Local Invocation

Create test event file:

```json
{
  "body": "{\"contact_name\":\"Test\",\"contact_email\":\"test@example.com\",\"contact_message\":\"Test\"}",
  "requestContext": {
    "http": {
      "sourceIp": "192.168.1.1",
      "userAgent": "Mozilla/5.0"
    }
  }
}
```

Invoke locally:

```python
import json
from contact_listener_lambda import lambda_handler

with open('test_event.json') as f:
    event = json.load(f)

response = lambda_handler(event, None)
print(json.dumps(response, indent=2))
```

## Best Practices

### Performance

- **Reuse AWS SDK clients** outside handler function (connection pooling)
- **Minimize cold starts** by keeping deployment package small
- **Use environment variables** instead of loading config files
- **Batch DynamoDB operations** when possible
- **Set appropriate memory/timeout** in Terraform (default: 128MB, 3s)

### Security

- **Never log sensitive data** (emails, API keys, passwords)
- **Use IAM roles** for AWS access (no hardcoded credentials)
- **Validate all inputs** before processing
- **Use environment variables** for configuration
- **Enable AWS X-Ray** for tracing (via Lambda Powertools)

### Code Quality

- **Type hints everywhere** - use modern Python 3.11+ syntax
- **Docstrings for public functions** - explain purpose and parameters
- **Keep handler functions small** - extract business logic to separate functions
- **Single responsibility** - each function does one thing well
- **DRY principle** - extract common code to utils modules

### Monitoring

- **Log all errors** with context
- **Log key business events** (message received, contact blocked, etc.)
- **Use structured logging** (JSON format) for better querying
- **Set up CloudWatch alarms** for error rates
- **Enable AWS X-Ray tracing** for performance analysis

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'package'`

**Solution:**
1. Check `requirements.txt` includes the package
2. Verify `build_in_docker = true` in Terraform
3. Run `terraform apply` to rebuild deployment package

### Timeout Errors

**Problem:** Lambda times out before completing

**Solution:**
1. Increase timeout in Terraform: `timeout = 30`
2. Optimize code (reduce DynamoDB scans, batch operations)
3. Check CloudWatch Logs for bottlenecks

### Permission Errors

**Problem:** `AccessDenied` or `UnauthorizedOperation`

**Solution:**
1. Check IAM policy in `terraform/lambdas.tf`
2. Verify resource ARNs are correct
3. Ensure policy includes required actions (e.g., `dynamodb:PutItem`)

### Environment Variable Not Found

**Problem:** `KeyError: 'QUEUE_URL'`

**Solution:**
1. Check environment variables in Terraform module
2. Verify Terraform apply completed successfully
3. Check Lambda configuration in AWS Console

## Related Documentation

- [Terraform Patterns](terraform-patterns.md) - Infrastructure configuration
- [API Integration Guide](api-integration-guide.md) - API Gateway patterns
- [Troubleshooting Runbook](troubleshooting-runbook.md) - Common issues
