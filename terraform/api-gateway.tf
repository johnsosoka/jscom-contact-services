################################
# Contact Listener Integration
################################

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "contact_lambda_execution_role" {
  name               = "lambda_execution_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_apigatewayv2_integration" "contact_integration" {
  api_id                 = local.api_gateway_id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = module.contact-listener.lambda_function_invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "test_route" {
  api_id    = local.api_gateway_id
  route_key = "POST /v1/contact"
  target    = "integrations/${aws_apigatewayv2_integration.contact_integration.id}"
}

# Invoke Permissions

resource "aws_lambda_permission" "lambda_permission" {
  statement_id  = "AllowContactServiceAPIInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.contact-listener.lambda_function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/*/* part allows invocation from any stage, method and resource path
  # within API Gateway REST API.
  source_arn = "${local.execution_arn}/*/*/*"
}

################################
# Admin Lambda Authorizer
################################

# Lambda authorizer function for API key validation
module "contact-admin-authorizer" {
  source          = "terraform-aws-modules/lambda/aws"
  function_name   = "contact-admin-authorizer"
  description     = "Lambda authorizer for admin API key validation"
  runtime         = "python3.13"
  handler         = "contact_admin_authorizer_lambda.lambda_handler"
  build_in_docker = false

  source_path = [{
    path             = "${path.module}/../lambdas/src/contact-admin-authorizer/app"
    pip_requirements = false
  }]

  environment_variables = {
    ADMIN_API_KEY = var.admin_api_key_value
  }

  tags = {
    project = local.project_name
  }
}

# API Gateway v2 authorizer using Lambda
resource "aws_apigatewayv2_authorizer" "api_key_authorizer" {
  api_id          = local.api_gateway_id
  authorizer_type = "REQUEST"
  name            = "${local.project_name}-admin-authorizer"
  authorizer_uri  = module.contact-admin-authorizer.lambda_function_invoke_arn

  authorizer_payload_format_version = "2.0"
  enable_simple_responses           = true

  identity_sources = ["$request.header.x-api-key"]
}

# Permission for API Gateway to invoke the authorizer Lambda
resource "aws_lambda_permission" "authorizer_permission" {
  statement_id  = "AllowAPIGatewayInvokeAuthorizer"
  action        = "lambda:InvokeFunction"
  function_name = module.contact-admin-authorizer.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${local.execution_arn}/authorizers/${aws_apigatewayv2_authorizer.api_key_authorizer.id}"
}

################################
# Admin Lambda Integration
################################

resource "aws_apigatewayv2_integration" "admin_integration" {
  api_id                 = local.api_gateway_id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = module.contact-admin.lambda_function_invoke_arn
  payload_format_version = "2.0"
}

# Catch-all route for admin endpoints: ANY /admin/{proxy+}
resource "aws_apigatewayv2_route" "admin_route" {
  api_id    = local.api_gateway_id
  route_key = "ANY /admin/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.admin_integration.id}"

  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.api_key_authorizer.id
}

# Lambda permission for API Gateway to invoke admin Lambda
resource "aws_lambda_permission" "admin_lambda_permission" {
  statement_id  = "AllowAdminAPIInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.contact-admin.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${local.execution_arn}/*/*/*"
}
