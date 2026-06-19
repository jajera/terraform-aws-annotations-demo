output "private_bucket_name" {
  description = "Name of the private bucket for copied images"
  value       = aws_s3_bucket.private_bucket.bucket
}

output "api_invoke_url" {
  description = "HTTP API invoke URL for the volcano images API"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "amplify_app_id" {
  description = "Amplify application ID"
  value       = aws_amplify_app.frontend.id
}

output "amplify_app_url" {
  description = "Amplify Hosting URL for the main branch"
  value       = "https://${aws_amplify_branch.main.branch_name}.${aws_amplify_app.frontend.default_domain}"
}

output "scheduler_enabled" {
  description = "Whether a one-time ingest schedule was created"
  value       = var.enable_scheduler
}

output "schedule_time" {
  description = "UTC time for the one-time ingest schedule (when enabled)"
  value       = var.enable_scheduler ? var.schedule_time : null
}
