#
#
#resource "aws_cloudwatch_log_group" "api_gateway_log_group" {
#  name = "/aws/gateway/contact_me_api_gateway_logs"
#
#  tags = {
#    site = "johnsosoka-com"
#  }
#}
#
#module "api_gateway" {
#  source = "terraform-aws-modules/apigateway-v2/aws"
#
#  name          = "${var.listener_api_name}-gateway"
#  description   = "api gateway setup for contact me submissions"
#  protocol_type = "HTTP"
#
#  cors_configuration = {
#    allow_headers = ["*"]
#    allow_methods = ["*"]
#    allow_origins = ["*"]
#  }
#
#  create_api_domain_name           = true
#
##
##  # Custom domain
#  domain_name                 = "api.johnsosoka.com"
#  domain_name_certificate_arn = data.terraform_remote_state.jscom_common_data.outputs.jscom_acm_cert
#
#  # Access logs
#  default_stage_access_log_destination_arn = aws_cloudwatch_log_group.api_gateway_log_group.arn
#  default_stage_access_log_format          = "$context.identity.sourceIp - - [$context.requestTime] \"$context.httpMethod $context.routeKey $context.protocol\" $context.status $context.responseLength $context.requestId $context.integrationErrorMessage"
#
#  # Routes and integrations
#  integrations = {
#    "POST /contact" = {
#      lambda_arn             = module.contact-listener.lambda_function_arn
#      payload_format_version = "2.0"
#
#      timeout_milliseconds   = 12000
#    }
#
#    "$default" = {
#      lambda_arn = module.contact-listener.lambda_function_arn
#    }
#  }
#
#  tags = {
#    Name = "jscom contact services"
#  }
#}
#
## Invoke Permissions
#resource "aws_lambda_permission" "contact_listener_lambda_permission" {
#  statement_id  = "AllowContactServiceAPIInvoke"
#  action        = "lambda:InvokeFunction"
#  function_name = module.contact-listener.lambda_function_name
#  principal     = "apigateway.amazonaws.com"
#
#  # The /*/*/* part allows invocation from any stage, method and resource path
#  # within API Gateway REST API.
#  source_arn = "${module.api_gateway.apigatewayv2_api_execution_arn}/*/*/*"
#}
#
#resource "aws_route53_record" "api_gateway_dns" {
#  name    = "api.johnsosoka.com"
#  type    = "A"
#  zone_id = data.terraform_remote_state.jscom_common_data.outputs.root_johnsosokacom_zone_id
#
#  alias {
#    evaluate_target_health = true
#    name                   = module.api_gateway.apigatewayv2_domain_name_target_domain_name
#    zone_id                 = module.api_gateway.apigatewayv2_domain_name_hosted_zone_id
#  }
#}