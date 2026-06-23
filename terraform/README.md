# Terraform

This directory provisions the DynamoDB table, IAM roles, Lambda function, and EventBridge schedules used to capture hourly weather and traffic context.

## API Keys

Copy the sample env files and add your keys before running `terraform apply`:

```bash
cp ../openweather.env.sample ../openweather.env
cp ../tomtom.env.sample ../tomtom.env
```

The real `.env` files are gitignored; only the `.env.sample` templates are checked in.

## Lambda

The Lambda handler in `lambda/lambda_function.py`:

- Calls OpenWeather for current conditions at the configured latitude/longitude.
- Calls TomTom for current traffic flow at the same point.
- Writes one `weather` item and one `traffic` item into the DynamoDB table with a TTL.
- Uses the Asia/Ho_Chi_Minh timezone to set the `date` and `hour` fields on stored items.

## When It Runs

EventBridge invokes the Lambda on the morning schedule defined in `schedule.tf`, using the `morning_lambda_schedule` cron expression from `variables.tf`. The default runs hourly during 04:00-07:00 Ho Chi Minh time.
