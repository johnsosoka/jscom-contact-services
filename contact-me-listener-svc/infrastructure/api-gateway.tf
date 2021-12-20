data "terraform_remote_state" "jscom_common_data" {
  backend = "s3"
  config = {
    bucket = "johnsosoka-com-tf-backend"
    key = "project/johnsosoka.com-blog/state/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_cloudwatch_log_group" "api_gateway_log_group" {
  name = "/aws/gateway/contact_me_api_gateway_logs"

  tags = {
    site = "johnsosoka-com"
  }
}

# TODO not receiving query params....
module "api_gateway" {
  source = "terraform-aws-modules/apigateway-v2/aws"

  name          = "${var.listener_api_name}-gateway"
  description   = "api gateway setup for contact me submissions"
  protocol_type = "HTTP"

  cors_configuration = {
    allow_headers = ["*"]
    allow_methods = ["*"]
    allow_origins = ["*"]
  }

  create_api_domain_name           = true


  # Custom domain
  domain_name                 = "api.johnsosoka.com"
  domain_name_certificate_arn = data.terraform_remote_state.jscom_common_data.outputs.jscom_acm_cert

  # Access logs
  default_stage_access_log_destination_arn = aws_cloudwatch_log_group.api_gateway_log_group.arn
  default_stage_access_log_format          = "$context.identity.sourceIp - - [$context.requestTime] \"$context.httpMethod $context.routeKey $context.protocol\" $context.status $context.responseLength $context.requestId $context.integrationErrorMessage"

  # Routes and integrations
  integrations = {
    "POST /services/form/contact" = {
      lambda_arn             = module.lambda_function.lambda_function_invoke_arn
      payload_format_version = "2.0"

      timeout_milliseconds   = 12000
    }

    "$default" = {
      lambda_arn = module.lambda_function.lambda_function_invoke_arn #TODO double check this value
    }
  }

  tags = {
    Name = "http-api-gateway jscom-contact-me-listener-svc"
  }
}

# Invoke Permissions



resource "aws_lambda_permission" "lambda_permission" {
  statement_id  = "AllowContactServiceAPIInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_function.lambda_function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/*/* part allows invocation from any stage, method and resource path
  # within API Gateway REST API.
  source_arn = "${module.api_gateway.apigatewayv2_api_execution_arn}/*/*/*"
}

# TODO retest after a time. If not working

//resource "aws_route53_record" "api_gateway_dns" {
//  name    = "api.johnsosoka.com"
//  type    = "A"
//  zone_id = aws_route53_zone.zone.id # TODO output variable.
//
//  alias {
//    evaluate_target_health = true
//    #name                   = aws_api_gateway_domain_name.api_domain.regional_domain_name
//    name                   = module.api_gateway.apigatewayv2_domain_name_target_domain_name
//    #zone_id                = aws_api_gateway_domain_name.api_domain.regional_zone_id
//    zone_id                 = module.api_gateway.apigatewayv2_domain_name_hosted_zone_id
//  }
//}