###############################################################################
# Post-apply Amplify deployment — avoids the default "Welcome" placeholder page
###############################################################################

locals {
  amplify_deploy_files = concat(
    [for f in fileset("${path.module}/../amplify/src", "**/*") : "src/${f}"],
    ["index.html", "vite.config.js", "package-lock.json"],
  )
  amplify_source_hash = sha256(join("", [
    for f in local.amplify_deploy_files : filesha256("${path.module}/../amplify/${f}")
  ]))
}

resource "terraform_data" "amplify_deploy" {
  count = var.deploy_amplify_on_apply ? 1 : 0

  triggers_replace = [
    aws_apigatewayv2_stage.default.invoke_url,
    local.amplify_source_hash,
  ]

  depends_on = [
    aws_amplify_app.frontend,
    aws_amplify_branch.main,
    aws_apigatewayv2_stage.default,
  ]

  provisioner "local-exec" {
    command     = "${path.module}/../scripts/deploy-amplify.sh"
    working_dir = path.module
    environment = {
      AMPLIFY_APP_ID = aws_amplify_app.frontend.id
      AMPLIFY_BRANCH = aws_amplify_branch.main.branch_name
      VITE_API_URL   = aws_apigatewayv2_stage.default.invoke_url
      AWS_REGION     = var.aws_region
    }
  }
}
