###############################################################################
# Lambda deployment packages — bundle boto3 >= 1.43 (S3 Annotations API)
###############################################################################

locals {
  lambda_modules = ["ingest_annotate", "api"]
  lambda_source_hash = sha256(join("", concat(
    [filesha256("${path.module}/../lambda/requirements.txt")],
    [filesha256("${path.module}/../lambda/shared/s3_annotations.py")],
    flatten([
      for mod in local.lambda_modules : [
        for f in fileset("${path.module}/../lambda/${mod}", "*.py") :
        filesha256("${path.module}/../lambda/${mod}/${f}")
      ]
    ]),
  )))
}

data "external" "lambda_packages" {
  program = ["bash", "${path.module}/../scripts/build-lambda-packages.sh"]

  query = {
    source_hash = local.lambda_source_hash
  }
}

resource "aws_lambda_function" "ingest" {
  function_name    = "volcano-ingest"
  role             = aws_iam_role.ingest_lambda.arn
  runtime          = "python3.14"
  handler          = "handler.handler"
  filename         = "${path.module}/.build/ingest_annotate.zip"
  source_code_hash = data.external.lambda_packages.result.ingest_hash
  timeout          = 900
  memory_size      = 256

  environment {
    variables = {
      PRIVATE_BUCKET       = aws_s3_bucket.private_bucket.id
      GEONET_PREFIX        = "camera/volcano/images"
      CAMERA_PATH          = var.camera_path
      DYNAMODB_TABLE       = var.enable_dynamodb ? "volcano-annotations" : ""
      ANNOTATION_NAMESPACE = "environment"
      CAMERA_TZ_OFFSET_HOURS = "12"
      INGEST_LOOKBACK_DAYS   = "7"
    }
  }
}

resource "aws_lambda_function" "api" {
  function_name    = "volcano-api"
  role             = aws_iam_role.api_lambda.arn
  runtime          = "python3.14"
  handler          = "handler.handler"
  filename         = "${path.module}/.build/api.zip"
  source_code_hash = data.external.lambda_packages.result.api_hash
  timeout          = 29
  memory_size      = 512

  environment {
    variables = {
      PRIVATE_BUCKET           = aws_s3_bucket.private_bucket.id
      DYNAMODB_TABLE           = var.enable_dynamodb ? "volcano-annotations" : ""
      PRESIGN_EXPIRY_SECONDS   = "900"
      ANNOTATION_FETCH_WORKERS = "48"
    }
  }
}
