################################
# Contact Listener Lambda
################################

module "contact-listener" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = var.contact_listener_lambda_name
  description        = "receives contact me messages from contact form, performs simple validation and forwards them to contact-message-queue"
  handler            = "contact_listener_lambda.lambda_handler"
  runtime            = "python3.8"
  source_path        = "../lambdas/src/contact_listener_lambda.py"
  attach_policy_json = true
  policy_json        = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.contact_message_queue.arn
      }
    ]
  })

  environment_variables = {
    CONTACT_MESSAGE_QUEUE_URL = aws_sqs_queue.contact_message_queue.id
  }

  tags = {
    project = local.project_name
  }
}

################################
# Contact Filter Lambda
################################

module "contact-filter" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = var.contact_filter_lambda_name
  description        = "Filters blocked contact me messages from contact-message-queue. Forwards valid messages to contact-notify-queue."
  handler            = "contact_filter_lambda.lambda_handler"
  runtime            = "python3.8"
  source_path        = "../lambdas/src/contact_filter_lambda.py"
  attach_policy_json = true
  policy_json        = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      # Permission to receive messages from contact queue
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.contact_message_queue.arn
      },
      # Permission to publish to contact_notify queue
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.contact_notify_queue.arn
      },
      # Permission write to contact_messages DynamoDB table
      {
        "Effect" : "Allow",
        "Action" : [
          #          "dynamodb:GetItem",
          "dynamodb:PutItem",
          #          "dynamodb:UpdateItem",
          #          "dynamodb:DeleteItem"
        ],
        "Resource" : aws_dynamodb_table.all_contact_messages.arn
      },
      # Permission to read blocked contact info
      {
        "Effect" : "Allow",
        "Action" : [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ],
        "Resource" : aws_dynamodb_table.blocked_contacts.arn
      }
    ]
  })

  environment_variables = {
    BLOCKED_CONTACTS_TABLE_NAME     = aws_dynamodb_table.blocked_contacts.name
    ALL_CONTACT_MESSAGES_TABLE_NAME = aws_dynamodb_table.all_contact_messages.name
    # Messages to be mailed to admin
    CONTACT_NOTIFY_QUEUE_URL        = aws_sqs_queue.contact_notify_queue.id
    CONTACT_MESSAGE_QUEUE_URL      = aws_sqs_queue.contact_message_queue.id
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
# Contact Notifier Lambda
################################

module "contact-notifier" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = var.contact_notifier_lambda_name
  description        = "Receive messages from contact-notify-queue, formats and send messages to admin email."
  handler            = "contact_notifier_lambda.lambda_handler"
  runtime            = "python3.8"
  source_path        = "../lambdas/src/contact_notifier_lambda.py"
  attach_policy_json = true
  environment_variables = {
    CONTACT_NOTIFY_QUEUE = aws_sqs_queue.contact_notify_queue.id
  }
  policy_json        = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      # Permission to receive messages from contact queue
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.contact_notify_queue.arn
      },
      # Permission to send mail
      {
        "Effect": "Allow",
        "Action": [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ],
        "Resource": "*"
      }
    ]
  })

  tags = {
    project = local.project_name
  }
}

resource "aws_lambda_event_source_mapping" "contact_notifier_mapping" {
  event_source_arn = aws_sqs_queue.contact_notify_queue.arn
  function_name    = module.contact-notifier.lambda_function_arn
}