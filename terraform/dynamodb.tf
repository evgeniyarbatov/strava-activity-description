resource "aws_dynamodb_table" "activity_context" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  range_key    = "date"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "date"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}