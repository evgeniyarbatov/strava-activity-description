terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    encrypt      = true
    bucket       = "arbatov-terraform-state"
    use_lockfile = true
    key          = "strava-activity-description.tfstate"
    region       = "ap-southeast-1"
  }
}