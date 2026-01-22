
resource "aws_cloudwatch_event_rule" "morning" {
  name                = "${var.lambda_name}-morning-schedule"
  schedule_expression = var.morning_lambda_schedule
}

resource "aws_cloudwatch_event_rule" "night" {
  name                = "${var.lambda_name}-night-schedule"
  schedule_expression = var.night_lambda_schedule
}

resource "aws_cloudwatch_event_target" "morning" {
  rule      = aws_cloudwatch_event_rule.morning.name
  target_id = "${var.lambda_name}-morning-schedule"
  arn       = aws_lambda_function.lambda.arn
}

resource "aws_cloudwatch_event_target" "night" {
  rule      = aws_cloudwatch_event_rule.night.name
  target_id = "${var.lambda_name}-night-schedule"
  arn       = aws_lambda_function.lambda.arn
}

resource "aws_lambda_permission" "morning" {
  statement_id  = "AllowExecutionFromEventBridgeMorning"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.morning.arn
}

resource "aws_lambda_permission" "night" {
  statement_id  = "AllowExecutionFromEventBridgeNight"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.night.arn
}
