# ─────────────────────────────────────────────────────────────────────────────
# Terraform Provider Configuration
# Pearls AQI Predictor — Serverless Infrastructure
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "pearls-aqi-terraform-state"
    key            = "sargodha-aqi/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "terraform-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "PearlsAQIPredictor"
      Environment = var.environment
      ManagedBy   = "Terraform"
      City        = "Sargodha"
    }
  }
}
