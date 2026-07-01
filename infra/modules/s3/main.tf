data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "uploads" {
  bucket = "${var.project_name}-${var.aws_region}-${data.aws_caller_identity.current.account_id}-uploads"
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  versioning_configuration {
    status = "Enabled"
  }
}