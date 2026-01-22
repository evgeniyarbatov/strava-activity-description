# ------------------------------
# IAM Role for Lambda
# ------------------------------
resource "aws_iam_role" "lambda_role" {
  name = "artdirector_bot_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Basic Lambda execution permissions
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# DynamoDB full access
resource "aws_iam_role_policy_attachment" "ddb_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

# EventBridge full access
resource "aws_iam_role_policy_attachment" "eventbridge_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEventBridgeFullAccess"
}

# ------------------------------
# Lambda Function
# ------------------------------
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_lambda_function" "bot_backend" {
  function_name = "artdirector_telegram_backend"
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  role = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      TELEGRAM_TOKEN = var.telegram_token
      OWNER_CHAT_ID  = var.owner_chat_id
    }
  }

  timeout = 15
}

# ------------------------------
# Public Lambda Function URL
# ------------------------------
resource "aws_lambda_function_url" "public_url" {
  function_name = aws_lambda_function.bot_backend.function_name

  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_headers = ["*"]
    allow_methods = ["POST"]
  }
}

# ------------------------------
# DynamoDB table
# ------------------------------
resource "aws_dynamodb_table" "portfolio" {
  name         = "PortfolioSites"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "url"

  attribute {
    name = "url"
    type = "S"
  }
}

# ------------------------------
# Outputs
# ------------------------------
output "lambda_function_url" {
  value = aws_lambda_function_url.public_url.function_url
}
