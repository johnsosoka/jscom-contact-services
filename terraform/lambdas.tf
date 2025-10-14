################################
# Contact Listener
################################

module "contact-listener" {
  source        = "terraform-aws-modules/lambda/aws"
  function_name = var.contact_listener_lambda_name
  description   = "Receives contact form messages; validates and forwards to SQS."
  runtime       = "python3.13"               # AL2023
  handler       = "contact_listener_lambda.lambda_handler"  # app/contact_listener_lambda.py
  build_in_docker = true                      # build deps for Linux

  source_path = [{
    path             = "${path.module}/../lambdas/src/contact-listener/app"
    pip_requirements = "${path.module}/../lambdas/src/contact-listener/requirements.txt"
  }]

  attach_policy_json = true
  policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:SendMessage"]
      Resource = aws_sqs_queue.contact_message_queue.arn
    }]
  })

  environment_variables = {
    CONTACT_MESSAGE_QUEUE_URL = aws_sqs_queue.contact_message_queue.id
  }

  tags = {
    project = local.project_name
  }
}

################################
# Contact Filter
################################

module "contact-filter" {
  source        = "terraform-aws-modules/lambda/aws"
  function_name = var.contact_filter_lambda_name
  description   = "Filters SQS messages; writes DDB; forwards valid to notify queue."
  runtime       = "python3.13"
  handler       = "contact_filter_lambda.lambda_handler"     # app/contact_filter_lambda.py
  build_in_docker = true

  source_path = [{
    path             = "${path.module}/../lambdas/src/contact-filter/app"
    pip_requirements = "${path.module}/../lambdas/src/contact-filter/requirements.txt"
  }]

  attach_policy_json = true
  policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes"]
        Resource = aws_sqs_queue.contact_message_queue.arn
      },
      {
        Effect = "Allow"
        Action = ["sqs:SendMessage"]
        Resource = aws_sqs_queue.contact_notify_queue.arn
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem"]
        Resource = aws_dynamodb_table.all_contact_messages.arn
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem","dynamodb:Query","dynamodb:Scan"]
        Resource = aws_dynamodb_table.blocked_contacts.arn
      }
    ]
  })

  environment_variables = {
    BLOCKED_CONTACTS_TABLE_NAME     = aws_dynamodb_table.blocked_contacts.name
    ALL_CONTACT_MESSAGES_TABLE_NAME = aws_dynamodb_table.all_contact_messages.name
    CONTACT_NOTIFY_QUEUE_URL        = aws_sqs_queue.contact_notify_queue.id
    CONTACT_MESSAGE_QUEUE_URL       = aws_sqs_queue.contact_message_queue.id
  }

  tags = {
    project = local.project_name
  }
}

resource "aws_lambda_event_source_mapping" "contact_filter_mapping" {
  event_source_arn = aws_sqs_queue.contact_message_queue.arn
  function_name    = module.contact-filter.lambda_function_arn
}

################################
# Contact Notifier
################################
module "contact-notifier" {
  source        = "terraform-aws-modules/lambda/aws"
  function_name = var.contact_notifier_lambda_name
  description   = "Consumes notify queue and sends SES emails."
  runtime       = "python3.13"
  handler       = "contact_notifier_lambda.lambda_handler"   # app/contact_notifier_lambda.py
  build_in_docker = true

  source_path = [{
    path             = "${path.module}/../lambdas/src/contact-notifier/app"
    pip_requirements = "${path.module}/../lambdas/src/contact-notifier/requirements.txt"
  }]

  attach_policy_json = true
  policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes"]
        Resource = aws_sqs_queue.contact_notify_queue.arn
      },
      {
        Effect  = "Allow"
        Action  = ["ses:SendEmail","ses:SendRawEmail"]
        Resource = "*"
      }
    ]
  })

  environment_variables = {
    CONTACT_NOTIFY_QUEUE = aws_sqs_queue.contact_notify_queue.id
    EMAIL_ENABLED        = var.email_notifications_enabled
    EMAIL_SENDER         = var.email_sender
    EMAIL_RECIPIENT      = var.email_recipient
  }
  tags = {
    project = local.project_name
  }
}

resource "aws_lambda_event_source_mapping" "contact_notifier_mapping" {
  event_source_arn = aws_sqs_queue.contact_notify_queue.arn
  function_name    = module.contact-notifier.lambda_function_arn
}