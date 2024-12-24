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
  api_id             = local.api_gateway_id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = module.contact-listener.lambda_function_invoke_arn
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
