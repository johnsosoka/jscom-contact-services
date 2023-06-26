resource "aws_sqs_queue" "contact_message_queue" {
  name = "contact-message-queue"
  tags = {
    project = local.project_name
  }
}

resource "aws_sqs_queue" "contact_notify_queue" {
  name = "contact-notify-queue"
  tags = {
    project = local.project_name
  }
}
