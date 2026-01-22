data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda.zip"
  excludes = [
    "__pycache__",
    "**/__pycache__/**",
    "*.pyc",
  ]
}

resource "aws_lambda_function" "lambda" {
  function_name = var.lambda_name
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  role = aws_iam_role.lambda_role.arn

  timeout = 60

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.activity_context.name
      TTL_DAYS       = var.ttl_days

      OPENWEATHER_API_KEY = var.openweather_api_key
      TOMTOM_API_KEY      = var.tomtom_api_key

      LATITUDE  = var.latitude
      LONGITUDE = var.longitude
    }
  }
}
