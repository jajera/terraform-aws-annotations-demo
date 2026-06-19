###############################################################################
# API Gateway — HTTP API with GET /images route and CORS
###############################################################################

# -----------------------------------------------------------------------------
# HTTP API
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_api" "volcano_images" {
  name          = "volcano-images-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET"]
    allow_headers = ["Content-Type"]
  }
}

# -----------------------------------------------------------------------------
# Lambda Integration (AWS_PROXY)
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_integration" "api_lambda" {
  api_id                 = aws_apigatewayv2_api.volcano_images.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

# -----------------------------------------------------------------------------
# Route: GET /images
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_route" "get_images" {
  api_id    = aws_apigatewayv2_api.volcano_images.id
  route_key = "GET /images"
  target    = "integrations/${aws_apigatewayv2_integration.api_lambda.id}"
}

# -----------------------------------------------------------------------------
# Stage: $default with auto-deploy
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.volcano_images.id
  name        = "$default"
  auto_deploy = true
}

# -----------------------------------------------------------------------------
# Lambda permission — allow API Gateway to invoke API Lambda
# -----------------------------------------------------------------------------

resource "aws_lambda_permission" "apigw_invoke_api" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.volcano_images.execution_arn}/*/*"
}
