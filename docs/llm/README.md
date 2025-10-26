# LLM Documentation Index

This directory contains detailed documentation designed for LLM agents working on jscom-contact-services.

## Documentation Files

### [lambda-development-guide.md](lambda-development-guide.md)
Comprehensive guide for developing Python Lambda functions in this repository, including:
- Project structure patterns
- Testing strategies and frameworks
- Dependency management
- Common patterns and best practices
- Deployment workflows

### [terraform-patterns.md](terraform-patterns.md)
Terraform-specific patterns and practices for this project:
- Module usage patterns
- Remote state management
- Lambda deployment configuration
- API Gateway integration patterns
- Resource naming conventions

### [api-integration-guide.md](api-integration-guide.md)
Guide for integrating with and extending the API:
- API Gateway v2 patterns
- Adding new endpoints
- Lambda authorizer configuration
- Request/response patterns
- Testing API changes

### [troubleshooting-runbook.md](troubleshooting-runbook.md)
Step-by-step troubleshooting procedures for common issues:
- Message processing failures
- Authentication issues
- Notification delivery problems
- DynamoDB query optimization
- Terraform state issues

## Quick Start for LLMs

1. **First time working on this repo?** Start with the main [CLAUDE.md](../../CLAUDE.md) in the repository root
2. **Working on Lambda functions?** See [lambda-development-guide.md](lambda-development-guide.md)
3. **Modifying infrastructure?** See [terraform-patterns.md](terraform-patterns.md)
4. **Adding API endpoints?** See [api-integration-guide.md](api-integration-guide.md)
5. **Debugging issues?** See [troubleshooting-runbook.md](troubleshooting-runbook.md)

## Context for Specialized Agents

### For Python Engineers
Focus on:
- Lambda function development patterns in [lambda-development-guide.md](lambda-development-guide.md)
- Pydantic models and type safety in contact-admin Lambda
- AWS SDK patterns (boto3) for DynamoDB and SQS
- Testing patterns with pytest and moto

### For Cloud Ops/DevOps Engineers
Focus on:
- Terraform patterns in [terraform-patterns.md](terraform-patterns.md)
- Lambda deployment and Docker build configuration
- API Gateway integration in [api-integration-guide.md](api-integration-guide.md)
- Monitoring and observability patterns
- Troubleshooting runbook for production issues

### For Full-Stack Engineers
You'll need both:
- API integration patterns for frontend/backend communication
- Lambda development for business logic
- Terraform basics for infrastructure understanding
- End-to-end testing approaches

## Project-Specific Conventions

### File Naming
- Lambda handler files: `<service>_lambda.py` (e.g., `contact_listener_lambda.py`)
- Test files: `test_<service>.py` (e.g., `test_contact_admin.py`)
- Terraform files: Resource-specific (e.g., `lambdas.tf`, `dynamoDB.tf`)

### Code Organization
- Lambda source: `lambdas/src/<function-name>/app/`
- Centralized tests: `lambdas/test/`
- Function-specific tests: `lambdas/src/<function-name>/test/` (optional)
- Infrastructure: `terraform/`

### Branching Strategy
- Main branch: `main`
- Feature branches: `feature/<description>`
- Bugfix branches: `bugfix/<description>`
- Housekeeping: `housekeeping/<description>`

### Commit Message Style
Review recent commits with `git log --oneline -10` to match the style. Generally:
- Start with verb (Add, Update, Fix, Remove, Refactor)
- Be concise and descriptive
- Reference issue numbers when applicable

## Related Repositories

- **jscom-tf-modules**: Shared Terraform modules (lambda-authorizer, static-website, base-api)
- **jscom-blog**: Owns the shared API Gateway instance
- **jscom-core-infrastructure**: Shared AWS infrastructure (Route53, ACM)

## Notes for Agent Teams

When a lead agent delegates work to specialized subagents:

1. **Scaffolding First**: Lead agent should set up basic structure before delegation
2. **Context Handoff**: Point subagent to relevant documentation in this directory
3. **Review Process**: Lead agent reviews subagent work for consistency
4. **Documentation Updates**: Update `llm_docs/` with findings and reports

## Maintenance

This documentation should be updated when:
- New Lambda functions are added
- API endpoints change significantly
- Terraform patterns evolve
- Common troubleshooting patterns emerge
- New testing frameworks are adopted
