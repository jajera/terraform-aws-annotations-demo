###############################################################################
# EventBridge Scheduler — Optional one-time trigger for Ingest Lambda
###############################################################################

resource "aws_scheduler_schedule" "ingest" {
  count = var.enable_scheduler ? 1 : 0

  name = "volcano-ingest-once"

  schedule_expression          = "at(${var.schedule_time})"
  schedule_expression_timezone = "UTC"

  flexible_time_window {
    mode = "OFF"
  }

  action_after_completion = "DELETE"

  target {
    arn      = aws_lambda_function.ingest.arn
    role_arn = aws_iam_role.scheduler[0].arn
  }
}
