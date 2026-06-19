###############################################################################
# Amplify Hosting — React SPA (Vite) with VITE_API_URL wiring
###############################################################################

# -----------------------------------------------------------------------------
# Amplify App
# -----------------------------------------------------------------------------

resource "aws_amplify_app" "frontend" {
  name     = var.amplify_app_name
  platform = "WEB"

  build_spec = <<-EOT
    version: 1
    frontend:
      phases:
        preBuild:
          commands:
            - cd amplify && npm ci
        build:
          commands:
            - cd amplify && npm run build
      artifacts:
        baseDirectory: amplify/dist
        files:
          - '**/*'
      cache:
        paths:
          - amplify/node_modules/**/*
  EOT

  environment_variables = {
    VITE_API_URL = aws_apigatewayv2_stage.default.invoke_url
  }
}

# -----------------------------------------------------------------------------
# Amplify Branch: main
# -----------------------------------------------------------------------------

resource "aws_amplify_branch" "main" {
  app_id      = aws_amplify_app.frontend.id
  branch_name = "main"
}
