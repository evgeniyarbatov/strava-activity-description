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
  default = "strava-activity-context-v2"
}

variable "ttl_days" {
  type    = number
  default = 2
}

variable "morning_lambda_schedule" {
  type    = string
  default = "cron(0 21-23,0 ? * * *)" # 04:00, 05:00, 06:00, 07:00 Ho Chi Minh time
}

variable "latitude" {
  type    = number
  default = 10.790609897658006
}

variable "longitude" {
  type    = number
  default = 106.6885402030355
}
