# Terraform

This directory provisions the DynamoDB table, IAM roles, Lambda function, and EventBridge schedules used to capture hourly weather and traffic context.

## Lambda

The Lambda handler in `lambda/lambda_function.py`:

- Calls OpenWeather for current conditions at the configured latitude/longitude.
- Calls TomTom for current traffic flow at the same point.
- Writes one `weather` item and one `traffic` item into the DynamoDB table with a TTL.
- Uses the Asia/Ho_Chi_Minh timezone to set the `date` and `hour` fields on stored items.

## When It Runs

EventBridge invokes the Lambda on two schedules defined in `schedule.tf`, using the `morning_lambda_schedule` and `night_lambda_schedule` cron expressions from `variables.tf`. The defaults are set to run hourly during 05:00-09:00 and 22:00-00:00 Hanoi time.
