variable "contact_me_topic_name" {
  default = "johnsosoka-com-contact-me-submission"
}

variable "lambda_name" {
  default = "contact-me-listener-svc"
}

variable "listener_api_name" {
  default = "contact-me-listener-api"
}

variable "contact_listener_invoke_path" {
  default = "/services/form/contact"
}