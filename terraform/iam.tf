###############################################################################
# IAM — Least-privilege roles for Ingest Lambda, API Lambda, and Scheduler
###############################################################################

data "aws_caller_identity" "current" {}

# -----------------------------------------------------------------------------
# Shared assume-role policy documents
# -----------------------------------------------------------------------------

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "scheduler_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

# =============================================================================
# 1. Ingest Lambda Role
# =============================================================================

resource "aws_iam_role" "ingest_lambda" {
  name               = "volcano-ingest-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# CloudWatch Logs — basic Lambda execution
data "aws_iam_policy_document" "ingest_lambda_logs" {
  statement {
    sid = "CloudWatchLogs"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/volcano-ingest:*"
    ]
  }
}

# S3 — write images and annotations to private bucket
data "aws_iam_policy_document" "ingest_lambda_s3" {
  statement {
    sid = "S3PrivateBucketWrite"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAnnotation",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.private_bucket.arn,
      "${aws_s3_bucket.private_bucket.arn}/*",
    ]
  }
}

resource "aws_iam_policy" "ingest_lambda_logs" {
  name   = "volcano-ingest-lambda-logs"
  policy = data.aws_iam_policy_document.ingest_lambda_logs.json
}

resource "aws_iam_policy" "ingest_lambda_s3" {
  name   = "volcano-ingest-lambda-s3"
  policy = data.aws_iam_policy_document.ingest_lambda_s3.json
}

resource "aws_iam_role_policy_attachment" "ingest_lambda_logs" {
  role       = aws_iam_role.ingest_lambda.name
  policy_arn = aws_iam_policy.ingest_lambda_logs.arn
}

resource "aws_iam_role_policy_attachment" "ingest_lambda_s3" {
  role       = aws_iam_role.ingest_lambda.name
  policy_arn = aws_iam_policy.ingest_lambda_s3.arn
}

# Optional: DynamoDB PutItem when enable_dynamodb is true
data "aws_iam_policy_document" "ingest_lambda_dynamodb" {
  count = var.enable_dynamodb ? 1 : 0

  statement {
    sid     = "DynamoDBPutItem"
    actions = ["dynamodb:PutItem"]
    resources = [
      "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/volcano-annotations"
    ]
  }
}

resource "aws_iam_policy" "ingest_lambda_dynamodb" {
  count  = var.enable_dynamodb ? 1 : 0
  name   = "volcano-ingest-lambda-dynamodb"
  policy = data.aws_iam_policy_document.ingest_lambda_dynamodb[0].json
}

resource "aws_iam_role_policy_attachment" "ingest_lambda_dynamodb" {
  count      = var.enable_dynamodb ? 1 : 0
  role       = aws_iam_role.ingest_lambda.name
  policy_arn = aws_iam_policy.ingest_lambda_dynamodb[0].arn
}

# =============================================================================
# 2. API Lambda Role
# =============================================================================

resource "aws_iam_role" "api_lambda" {
  name               = "volcano-api-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# CloudWatch Logs — basic Lambda execution
data "aws_iam_policy_document" "api_lambda_logs" {
  statement {
    sid = "CloudWatchLogs"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/volcano-api:*"
    ]
  }
}

# S3 — read images and annotations from private bucket
data "aws_iam_policy_document" "api_lambda_s3" {
  statement {
    sid = "S3PrivateBucketRead"
    actions = [
      "s3:GetObject",
      "s3:GetObjectAnnotation",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.private_bucket.arn,
      "${aws_s3_bucket.private_bucket.arn}/*",
    ]
  }
}

resource "aws_iam_policy" "api_lambda_logs" {
  name   = "volcano-api-lambda-logs"
  policy = data.aws_iam_policy_document.api_lambda_logs.json
}

resource "aws_iam_policy" "api_lambda_s3" {
  name   = "volcano-api-lambda-s3"
  policy = data.aws_iam_policy_document.api_lambda_s3.json
}

resource "aws_iam_role_policy_attachment" "api_lambda_logs" {
  role       = aws_iam_role.api_lambda.name
  policy_arn = aws_iam_policy.api_lambda_logs.arn
}

resource "aws_iam_role_policy_attachment" "api_lambda_s3" {
  role       = aws_iam_role.api_lambda.name
  policy_arn = aws_iam_policy.api_lambda_s3.arn
}

# Optional: DynamoDB Scan/Query when enable_dynamodb is true
data "aws_iam_policy_document" "api_lambda_dynamodb" {
  count = var.enable_dynamodb ? 1 : 0

  statement {
    sid = "DynamoDBRead"
    actions = [
      "dynamodb:Scan",
      "dynamodb:Query",
    ]
    resources = [
      "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/volcano-annotations"
    ]
  }
}

resource "aws_iam_policy" "api_lambda_dynamodb" {
  count  = var.enable_dynamodb ? 1 : 0
  name   = "volcano-api-lambda-dynamodb"
  policy = data.aws_iam_policy_document.api_lambda_dynamodb[0].json
}

resource "aws_iam_role_policy_attachment" "api_lambda_dynamodb" {
  count      = var.enable_dynamodb ? 1 : 0
  role       = aws_iam_role.api_lambda.name
  policy_arn = aws_iam_policy.api_lambda_dynamodb[0].arn
}

# =============================================================================
# 3. Scheduler Execution Role
# =============================================================================

resource "aws_iam_role" "scheduler" {
  count = var.enable_scheduler ? 1 : 0

  name               = "volcano-scheduler-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role.json
}

data "aws_iam_policy_document" "scheduler_invoke" {
  statement {
    sid     = "InvokeIngestLambda"
    actions = ["lambda:InvokeFunction"]
    resources = [
      "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:volcano-ingest"
    ]
  }
}

resource "aws_iam_policy" "scheduler_invoke" {
  count = var.enable_scheduler ? 1 : 0

  name   = "volcano-scheduler-invoke"
  policy = data.aws_iam_policy_document.scheduler_invoke.json
}

resource "aws_iam_role_policy_attachment" "scheduler_invoke" {
  count = var.enable_scheduler ? 1 : 0

  role       = aws_iam_role.scheduler[0].name
  policy_arn = aws_iam_policy.scheduler_invoke[0].arn
}
