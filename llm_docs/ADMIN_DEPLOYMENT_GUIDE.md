# Contact Admin Lambda Deployment Guide

This guide covers deploying the new contact-admin Lambda function and its supporting infrastructure.

## Overview

The contact-admin Lambda provides a REST API for administrative operations:
- View contact messages (with pagination and filtering)
- Retrieve individual messages
- Get system statistics
- List blocked contacts
- Block/unblock IP addresses

## Architecture Components

### New Infrastructure

1. **contact-admin Lambda**: Main admin API handler using AWS Lambda Powertools
2. **contact-admin-authorizer Lambda**: API key validator for securing admin endpoints
3. **API Gateway Route**: `ANY /admin/{proxy+}` catches all admin requests
4. **Lambda Authorizer**: Custom authorizer validates x-api-key header

### Security Model

- API Gateway v2 (HTTP API) with custom Lambda authorizer
- API key passed via `x-api-key` header
- Simple boolean authorization responses
- All admin routes protected by authorizer

## Prerequisites

1. AWS CLI configured with `jscom` profile
2. Terraform >= 1.0
3. Existing jscom-blog API Gateway (referenced via remote state)
4. Python 3.13 Lambda runtime support in your AWS region

## Configuration Steps

### 1. Generate API Key

Generate a secure API key for admin access:

```bash
# Generate a 32-character hex key
openssl rand -hex 32
```

Save this key securely - you'll need it for both Terraform and API requests.

### 2. Create terraform.tfvars

Copy the example file and add your secrets:

```bash
cd /Users/john/code/websites/jscom-contact-services/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and add:

```hcl
# Required: Your generated API key
admin_api_key_value = "your-generated-api-key-here"

# Required: Discord webhook URL (from existing setup)
discord_webhook_url = "https://discord.com/api/webhooks/..."
```

**IMPORTANT**: Never commit `terraform.tfvars` to version control. Add to `.gitignore`.

### 3. Verify Lambda Code

Ensure the contact-admin Lambda code exists:

```bash
ls -la /Users/john/code/websites/jscom-contact-services/lambdas/src/contact-admin/app/
```

Should contain:
- `contact_admin_lambda.py` (main handler)
- `models.py` (Pydantic models)
- `handlers.py` (business logic)
- `__init__.py` (package marker)

And:
```bash
cat /Users/john/code/websites/jscom-contact-services/lambdas/src/contact-admin/requirements.txt
```

Should contain:
```
aws-lambda-powertools[all]>=2.0.0
pydantic>=2.0.0
```

## Deployment

### 1. Initialize Terraform (if needed)

```bash
cd /Users/john/code/websites/jscom-contact-services/terraform
export AWS_PROFILE=jscom
terraform init
```

### 2. Review Changes

```bash
terraform plan
```

Expected new resources:
- `module.contact-admin` - Admin Lambda function
- `module.admin-authorizer` - Authorizer Lambda function
- `aws_apigatewayv2_integration.admin_integration` - API Gateway integration
- `aws_apigatewayv2_route.admin_route` - Route for /admin/*
- `aws_apigatewayv2_authorizer.api_key_authorizer` - Custom authorizer
- `aws_lambda_permission.admin_lambda_permission` - Invoke permission
- `aws_lambda_permission.authorizer_permission` - Authorizer invoke permission

### 3. Apply Infrastructure

```bash
terraform apply
```

Review the plan and type `yes` to proceed.

### 4. Retrieve API Information

After successful deployment:

```bash
# Get admin API endpoint
terraform output admin_api_endpoint

# Get available routes
terraform output admin_routes

# Get Lambda function name
terraform output contact_admin_function_name
```

## Testing the API

### Test Authorizer

Test that the authorizer blocks unauthorized requests:

```bash
# Without API key (should return 401 or 403)
curl -X GET https://api.johnsosoka.com/admin/stats

# With invalid API key (should return 401 or 403)
curl -X GET https://api.johnsosoka.com/admin/stats \
  -H "x-api-key: invalid-key"
```

### Test Admin Endpoints

Replace `YOUR_API_KEY` with your actual API key:

```bash
# Get system statistics
curl -X GET https://api.johnsosoka.com/admin/stats \
  -H "x-api-key: YOUR_API_KEY"

# List contact messages (first 50)
curl -X GET https://api.johnsosoka.com/admin/messages \
  -H "x-api-key: YOUR_API_KEY"

# List messages with pagination
curl -X GET "https://api.johnsosoka.com/admin/messages?limit=10" \
  -H "x-api-key: YOUR_API_KEY"

# Filter by contact type
curl -X GET "https://api.johnsosoka.com/admin/messages?contact_type=consulting" \
  -H "x-api-key: YOUR_API_KEY"

# Get specific message
curl -X GET https://api.johnsosoka.com/admin/messages/MESSAGE_ID \
  -H "x-api-key: YOUR_API_KEY"

# List blocked contacts
curl -X GET https://api.johnsosoka.com/admin/blocked \
  -H "x-api-key: YOUR_API_KEY"

# Block an IP address
curl -X POST https://api.johnsosoka.com/admin/blocked \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "ip_address": "192.168.1.100",
    "user_agent": "BadBot/1.0"
  }'

# Unblock a contact
curl -X DELETE https://api.johnsosoka.com/admin/blocked/BLOCKED_ID \
  -H "x-api-key: YOUR_API_KEY"
```

## Monitoring and Debugging

### CloudWatch Logs

Lambda functions log to CloudWatch Logs:

```bash
# View admin Lambda logs
aws logs tail /aws/lambda/contact-admin --follow --profile jscom

# View authorizer Lambda logs
aws logs tail /aws/lambda/contact-admin-authorizer --follow --profile jscom
```

### Test Lambda Directly

Test the Lambda function directly (bypasses API Gateway):

```bash
# Test with AWS CLI
aws lambda invoke \
  --function-name contact-admin \
  --payload '{"rawPath": "/admin/stats", "requestContext": {"http": {"method": "GET"}}}' \
  --profile jscom \
  response.json

cat response.json
```

### Common Issues

#### Issue: 401/403 Unauthorized

**Cause**: Invalid or missing API key

**Solution**:
- Verify API key in terraform.tfvars matches your request header
- Check authorizer Lambda logs for validation errors
- Ensure x-api-key header is present (lowercase)

#### Issue: 500 Internal Server Error

**Cause**: Lambda execution error

**Solution**:
- Check CloudWatch Logs for the contact-admin Lambda
- Verify DynamoDB table permissions
- Check environment variables are set correctly

#### Issue: API Gateway returns wrong payload format

**Cause**: Mismatch between Lambda code (REST API format) and API Gateway v2

**Solution**: The Lambda code uses `APIGatewayRestResolver` from Powertools but the infrastructure uses API Gateway v2 (HTTP API). This may cause event format issues. Consider:
- Switching Lambda to use `APIGatewayHttpResolver` (recommended)
- Or converting API Gateway to REST API (v1)

## API Response Formats

All admin endpoints return JSON with this structure:

```json
{
  "status": 200,
  "data": { ... },
  "error": null
}
```

Error responses:
```json
{
  "status": 400,
  "data": null,
  "error": "Validation error: ..."
}
```

## Security Best Practices

1. **Rotate API Keys**: Change admin_api_key_value periodically
2. **Restrict Access**: Only share API key with authorized administrators
3. **Monitor Usage**: Review CloudWatch Logs regularly
4. **Use HTTPS**: Always use https:// for API requests
5. **Secure Storage**: Store API key in password manager or secrets manager

## Updating the Infrastructure

To modify Lambda code or infrastructure:

```bash
cd /Users/john/code/websites/jscom-contact-services/terraform
export AWS_PROFILE=jscom

# Make your changes to Lambda code or Terraform files

# Review changes
terraform plan

# Apply updates
terraform apply
```

Terraform will automatically rebuild and redeploy Lambda functions when source code changes.

## Rollback Procedure

If deployment fails or causes issues:

```bash
# View Terraform state
terraform show

# Destroy admin resources (keeps existing contact form infrastructure)
terraform destroy -target=module.contact-admin \
  -target=module.admin-authorizer \
  -target=aws_apigatewayv2_route.admin_route

# Or rollback to previous Terraform state
terraform state pull > backup.tfstate
# (Manually restore from backup if needed)
```

## Additional Resources

- Lambda Powertools Documentation: https://docs.powertools.aws.dev/lambda/python/
- API Gateway v2 Authorizers: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html
- Terraform AWS Lambda Module: https://github.com/terraform-aws-modules/terraform-aws-lambda

## Support

For issues or questions:
1. Check CloudWatch Logs for Lambda execution errors
2. Review Terraform plan output before applying
3. Verify API key configuration in terraform.tfvars
4. Test authorizer independently using AWS CLI
