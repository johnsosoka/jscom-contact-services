---
allowed-tools:
  - Bash(curl:*)
description: Send an HTTP request
---

Perform a regression test against the production endpoints.

If a specific endpoint is provided as an argument, test only that endpoint. Otherwise, perform a complete regression test of all endpoints.

# Context & Task

Leverage curl and the aws cli to perform end-to-end tests against the production API endpoints to ensure they are functioning as expected.

## Test Discovery

1. **Identify endpoints:** Review README.md and CLAUDE.md to find all production API endpoints
   - Public endpoints: Contact form submission endpoints
   - Admin endpoints: All admin CRUD operations (stats, list messages, get message, list/block/unblock contacts)

2. **Gather credentials:** The API key for admin endpoints is in `terraform/terraform.tfvars`

3. **Identify Lambda functions:** Lambda function names can be found in:
   - CLAUDE.md documentation
   - `terraform/lambdas.tf` configuration
   - Expected functions: contact-listener, contact-filter, contact-notifier, contact-admin, contact-admin-authorizer

## Test Execution

### Public API Tests
1. Test standard contact form submission with valid payload
2. Test consulting contact form submission with all optional fields
3. Test invalid payloads (missing required fields) - expect 400 errors

### Admin API Tests
1. Test authentication:
   - Valid API key should return 200
   - Invalid API key should return 403
2. Test all read-only endpoints:
   - GET /v1/contact/admin/stats
   - GET /v1/contact/admin/messages (test with limit and contact_type parameters)
   - GET /v1/contact/admin/messages/{id} (use an ID from the list results)
   - GET /v1/contact/admin/blocked

### Production Safety Guidelines
- Use clearly marked test email addresses (e.g., test@example.com)
- Use test names that indicate they're regression tests
- **DO NOT** create blocked contacts in production (skip POST /blocked and DELETE /blocked tests)
- Note: Test messages will be sent to actual notification channels (email/Discord)

### Lambda Log Verification
After running tests, wait 1-2 minutes for async processing, then check CloudWatch logs:
1. Use `aws logs tail` with `--since 30m` to capture recent activity
2. Verify each Lambda function was invoked successfully
3. Check for error messages or warnings
4. Verify the complete message flow: listener → filter → notifier
5. Verify admin Lambda processed admin requests

Commands:
```bash
aws logs tail /aws/lambda/contact-listener --since 30m --format short --profile jscom | head -50
aws logs tail /aws/lambda/contact-filter --since 30m --format short --profile jscom | head -50
aws logs tail /aws/lambda/contact-notifier --since 30m --format short --profile jscom | head -50
aws logs tail /aws/lambda/contact-admin --since 30m --format short --profile jscom | head -50
aws logs tail /aws/lambda/contact-admin-authorizer --since 30m --format short --profile jscom | head -50
```

## Report Generation

Create a comprehensive test report in `test/prod_test_report.md` with the following sections:

1. **Executive Summary:** Overall test results and system health
2. **Test Environment:** API URL, region, profile, test timestamp
3. **Test Results Overview:** Table showing tests run, passed, failed
4. **Detailed Test Results:** For each endpoint tested:
   - Request details (method, URL, payload)
   - Response details (status code, body)
   - Lambda invocation details from CloudWatch
   - Performance metrics (duration, memory usage)
5. **CloudWatch Logs Analysis:** Summary of log health for each Lambda
6. **Performance Summary:** Cold start vs warm start metrics
7. **System Health Indicators:** Message counts, notification status, security status
8. **Issues and Observations:** Any failures, warnings, or notable behaviors
9. **Recommendations:** Suggested improvements or concerns

## Expected Outcomes

All tests should pass with:
- Public API returns 200 for valid requests
- Admin API returns 200 for authorized requests, 403 for unauthorized
- All Lambda functions execute without errors
- Complete message flow from submission through notification
- Proper structured logging in all functions
