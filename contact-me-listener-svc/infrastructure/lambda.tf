module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = var.lambda_name
  description   = "contact me submission listener"
  handler       = "handler.lambda_handler"
  runtime       = "python3.8"
  source_path = "../src/"
  attach_policy_json = true
  policy_json        = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": "arn:aws:sns:*:*:*"
        }
    ]
}
EOF

  environment_variables = {
    TOPIC_ARN = aws_sns_topic.contact_me_topic.arn
  }

  tags = {
    Name = "contact-me-listener-svc"
  }
}
