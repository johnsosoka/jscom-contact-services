variable "contact_listener_lambda_name" {
  default = "contact-listener"
}

variable "contact_filter_lambda_name" {
  default = "contact-filter"
}

variable "contact_notifier_lambda_name" {
  default = "contact-notifier"
}

variable "listener_api_name" {
  default = "contact-me-listener-api"
}

# Notification method configuration
variable "email_notifications_enabled" {
  description = "Enable email notifications via SES"
  type        = string
  default     = "true"
}

variable "email_sender" {
  description = "Email address to send notifications from"
  type        = string
  default     = "mail@johnsosoka.com"
}

variable "email_recipient" {
  description = "Email address to send notifications to"
  type        = string
  default     = "im@johnsosoka.com"
}

variable "discord_notifications_enabled" {
  description = "Enable Discord webhook notifications"
  type        = string
  default     = "true"
}

variable "discord_webhook_url" {
  description = "Discord webhook URL for notifications"
  type        = string
  sensitive   = true
}
