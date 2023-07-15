The README you provided is already quite detailed and provides a good overview of the project. However, adding an API Methods section with example JSON payloads would indeed be beneficial for users who want to interact with the API. Here's a revised version of the README with the suggested changes:

---

# JSCOM Contact Services

This repository contains the source code for the JSCOM Contact Services, a serverless application that handles contact form submissions. The application is built using AWS services, including API Gateway, Lambda, DynamoDB, and SQS, and is managed using Terraform.

## Architecture

The application consists of three AWS Lambda functions, an API Gateway, two DynamoDB tables, and two SQS queues.

The architecture follows this flow:

1. Contact form submissions are sent to the API Gateway.
2. The API Gateway triggers the `contact-listener` Lambda function.
3. The `contact-listener` Lambda function validates the incoming message and forwards it to the `contact-message-queue`.
4. The `contact-filter` Lambda function is triggered by the new message in the `contact-message-queue`. It checks if the sender is blocked. If not, the message is forwarded to the `contact-notify-queue`.
5. The `contact-notifier` Lambda function is triggered by the new message in the `contact-notify-queue` and sends an email to the admin.

## Resources

### Lambda Functions

All Lambda functions are written in Python.

- `contact-listener`: This function receives contact form submissions from the API Gateway, performs simple validation, and forwards the messages to the `contact-message-queue`. [Source Code](https://github.com/johnsosoka/jscom-contact-services/blob/main/lambdas/src/contact_listener_lambda.py)

- `contact-filter`: This function filters blocked contact messages from the `contact-message-queue`. It checks the `blocked_contacts` DynamoDB table to see if the sender is blocked. Valid messages are forwarded to the `contact-notify-queue`. [Source Code](https://github.com/johnsosoka/jscom-contact-services/blob/main/lambdas/src/contact_filter_lambda.py)

- `contact-notifier`: This function receives messages from the `contact-notify-queue`, formats them, and sends them to the admin email. [Source Code](https://github.com/johnsosoka/jscom-contact-services/blob/main/lambdas/src/contact_notifier_lambda.py)

### DynamoDB Tables

- `all-contact-messages`: This table stores all contact messages. It has the following attributes: `id`, `timestamp`, `sender_name`, `sender_email`, `message_body`, and `is_blocked`. It also has global secondary indexes on `sender_name`, `sender_email`, `is_blocked`, and `message_body`.

- `blocked_contacts`: This table tracks blocked contacts. It has the following attributes: `id`, `ip_address`, `user_agent`, and `is_blocked`. It also has global secondary indexes on `ip_address`, `user_agent`, `is_blocked`, and a composite index on `ip_address` and `user_agent`.

### SQS Queues

- `contact-message-queue`: This queue holds messages received from the `contact-listener` Lambda function.

- `contact-notify-queue`: This queue holds messages that have been filtered by the `contact-filter` Lambda function and are ready to be sent to the admin email by the `contact-notifier` Lambda function.

## API Methods

The API Gateway exposes the following endpoint:

- `POST https://api.johnsosoka.com/v1/contact`: Submits a new contact form message. The request body should be a JSON object with the following structure:

```json
{
  "sender_name": "John Doe",
  "sender_email": "john.doe@example.com",
  "message_body": "Hello, this is a test message."
}
```

## Deployment

The application is deployed using Terraform. The Terraform configuration files are located in the `terraform` directory. The Terraform state is managed remotely in an S3 bucket.

To deploy the application, navigate to the `terraform` directory and run the following commands:

```bash
terraform init
terraform apply
```
