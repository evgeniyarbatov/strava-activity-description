variable "aws_region" {
  type    = string
  default = "ap-southeast-1"
}

variable "lambda_name" {
  type    = string
  default = "strava-activity-context"
}

variable "dynamodb_table_name" {
  type    = string
  default = "strava-activity-context"
}

variable "morning_lambda_schedule" {
  type    = string
  default = "cron(0 22-23,0 ? * * *)" # 05:00, 06:00, 07:00 Hanoi time
}

variable "night_lambda_schedule" {
  type    = string
  default = "cron(0 15-17 ? * * *)" # 22:00, 23:00, 00:00 Hanoi time
}