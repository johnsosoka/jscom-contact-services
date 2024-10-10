resource "aws_cloudwatch_log_group" "api_gateway_log_group" {
  name = "/aws/gateway/contact_me_api_gateway_logs"

  tags = {
    site = "johnsosoka-com"
  }
}

// ACM & Cloudfront.
resource "aws_acm_certificate" "api_acm_cert" {
  // We want a wildcard cert so we can host subdomains later.
  domain_name       = "api.johnsosoka.com"
  validation_method = "EMAIL"

}

module "api_gateway" {
  source  = "terraform-aws-modules/apigateway-v2/aws"
  version = "2.2.2"

  name          = "${var.listener_api_name}-gateway"
  description   = "api gateway setup for contact me submissions"
  protocol_type = "HTTP"

  cors_configuration = {
    allow_headers = ["*"]
    allow_methods = ["*"]
    allow_origins = ["*"]
  }

  # Custom domain
  create_api_domain_name      = true
  domain_name                 = "api.johnsosoka.com"
  domain_name_certificate_arn = data.terraform_remote_state.jscom_common_data.outputs.jscom_acm_cert_global

  # Access logs
  default_stage_access_log_destination_arn = aws_cloudwatch_log_group.api_gateway_log_group.arn
  default_stage_access_log_format          = "$context.identity.sourceIp - - [$context.requestTime] \"$context.httpMethod $context.routeKey $context.protocol\" $context.status $context.responseLength $context.requestId $context.integrationErrorMessage"

  # Routes and integrations
  integrations = {
    "POST /v1/contact" = {
      lambda_arn             = module.contact-listener.lambda_function_invoke_arn
      payload_format_version = "2.0"

      timeout_milliseconds   = 12000
    }

    "$default" = {
      lambda_arn = module.contact-listener.lambda_function_invoke_arn
    }
  }

  tags = {
    Name = "jscom-contact-services"
  }
}

# Invoke Permissions

resource "aws_lambda_permission" "lambda_permission" {
  statement_id  = "AllowContactServiceAPIInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.contact-listener.lambda_function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/*/* part allows invocation from any stage, method and resource path
  # within API Gateway REST API.
  source_arn = "${module.api_gateway.apigatewayv2_api_execution_arn}/*/*/*"
}

resource "aws_route53_record" "api_gateway_dns" {
  name    = "api.johnsosoka.com"
  type    = "A"
  zone_id = data.terraform_remote_state.jscom_common_data.outputs.root_johnsosokacom_zone_id

  alias {
    evaluate_target_health = true
    name                   =  module.api_gateway.apigatewayv2_domain_name_target_domain_name
    zone_id                 = module.api_gateway.apigatewayv2_domain_name_hosted_zone_id
  }
}
