resource "aws_dynamodb_table" "annotations" {
  count = var.enable_dynamodb ? 1 : 0

  name         = "volcano-annotations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "image_key"
  range_key    = "captured_utc"

  attribute {
    name = "image_key"
    type = "S"
  }

  attribute {
    name = "captured_utc"
    type = "S"
  }
}
