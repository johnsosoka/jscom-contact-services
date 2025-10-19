################################
# Lambda Outputs
################################

output "contact_listener_function_name" {
  description = "Name of the contact listener Lambda function"
  value       = module.contact-listener.lambda_function_name
}

output "contact_filter_function_name" {
  description = "Name of the contact filter Lambda function"
  value       = module.contact-filter.lambda_function_name
}

output "contact_notifier_function_name" {
  description = "Name of the contact notifier Lambda function"
  value       = module.contact-notifier.lambda_function_name
}

output "contact_admin_function_name" {
  description = "Name of the admin Lambda function"
  value       = module.contact-admin.lambda_function_name
}

output "contact_admin_function_arn" {
  description = "ARN of the admin Lambda function"
  value       = module.contact-admin.lambda_function_arn
}

################################
# API Gateway Outputs
################################

output "admin_api_endpoint" {
  description = "Base URL for admin API endpoints"
  value       = "https://${local.api_domain_name}/admin"
}

output "admin_routes" {
  description = "Available admin API routes"
  value = {
    list_messages   = "GET /admin/messages"
    get_message     = "GET /admin/messages/{id}"
    get_stats       = "GET /admin/stats"
    list_blocked    = "GET /admin/blocked"
    block_contact   = "POST /admin/blocked"
    unblock_contact = "DELETE /admin/blocked/{id}"
  }
}

################################
# DynamoDB Outputs
################################

output "all_contact_messages_table_name" {
  description = "Name of the all contact messages DynamoDB table"
  value       = aws_dynamodb_table.all_contact_messages.name
}

output "blocked_contacts_table_name" {
  description = "Name of the blocked contacts DynamoDB table"
  value       = aws_dynamodb_table.blocked_contacts.name
}

################################
# SQS Outputs
################################

output "contact_message_queue_url" {
  description = "URL of the contact message SQS queue"
  value       = aws_sqs_queue.contact_message_queue.id
}

output "contact_notify_queue_url" {
  description = "URL of the contact notify SQS queue"
  value       = aws_sqs_queue.contact_notify_queue.id
}
