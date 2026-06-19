resource "aws_s3_bucket" "private_bucket" {
  bucket        = var.private_bucket_name
  force_destroy = true
}
