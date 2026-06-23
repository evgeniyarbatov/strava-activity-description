
resource "aws_cloudwatch_event_rule" "morning" {
  name                = "${var.lambda_name}-morning-schedule"
  schedule_expression = var.morning_lambda_schedule
}

resource "aws_cloudwatch_event_target" "morning" {
  rule      = aws_cloudwatch_event_rule.morning.name
  target_id = "${var.lambda_name}-morning-schedule"
  arn       = aws_lambda_function.lambda.arn
}

resource "aws_lambda_permission" "morning" {
  statement_id  = "AllowExecutionFromEventBridgeMorning"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.morning.arn
}


