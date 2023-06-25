resource "aws_sqs_queue" "contact_message_queue" {
  name = "contact-message-queue"
}

resource "aws_sqs_queue" "contact_notify_queue" {
  name = "contact-notify-queue"
}
