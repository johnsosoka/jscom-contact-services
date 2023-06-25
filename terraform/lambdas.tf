################################
# Contact Listener Lambda
################################

module "contact-listener" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = var.contact_listener_lambda_name
  description   = "contact me submission listener"
  handler       = "app.lambda_handler"
  runtime       = "python3.8"
  source_path = "../contact-listener/"
  attach_policy_json = true
  policy_json        = jsonencode({
    Version = "2012-10-17"
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

#  tags = {
#    Name = "jscom-contact-services"
#  }
}

################################
# Contact Filter Lambda
################################

module "contact-filter" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = var.contact_filter_lambda_name
  description        = "contact me submission filter lambda"
  handler            = "app.lambda_handler"
  runtime            = "python3.8"
  source_path        = "../contact-filter/"
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
  description        = "contact me notifier lambda"
  handler            = "app.lambda_handler"
  runtime            = "python3.8"
  source_path        = "../contact-notifier/"
  attach_policy_json = true
  environment_variables = {
    CONTACT_MESSAGE_QUEUE_URL = aws_sqs_queue.contact_message_queue.id
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
}

resource "aws_lambda_event_source_mapping" "contact_notifier_mapping" {
  event_source_arn = aws_sqs_queue.contact_notify_queue.arn
  function_name    = module.contact-notifier.lambda_function_arn
}