# ─────────────────────────────────────────────────────────────────────────────
# Terraform Variables
# Pearls AQI Predictor — Parameterized Configuration
# ─────────────────────────────────────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "project_name" {
  description = "Project identifier used for resource naming"
  type        = string
  default     = "pearls-aqi"
}

# ── API Keys (stored in SSM Parameter Store) ──────────────────────────────

variable "aqicn_api_key" {
  description = "AQICN API token for air quality data"
  type        = string
  sensitive   = true
}

variable "openweather_api_key" {
  description = "OpenWeatherMap API key"
  type        = string
  sensitive   = true
}

variable "hopsworks_api_key" {
  description = "Hopsworks Feature Store API key"
  type        = string
  sensitive   = true
}

# ── Schedule Configuration ────────────────────────────────────────────────

variable "feature_pipeline_schedule" {
  description = "EventBridge schedule for feature pipeline (rate expression)"
  type        = string
  default     = "rate(1 hour)"
}

variable "training_pipeline_schedule" {
  description = "EventBridge schedule for training pipeline (rate expression)"
  type        = string
  default     = "rate(1 day)"
}

# ── Compute Configuration ────────────────────────────────────────────────

variable "lambda_memory_mb" {
  description = "Memory allocation for Lambda function (MB)"
  type        = number
  default     = 512
  validation {
    condition     = var.lambda_memory_mb >= 128 && var.lambda_memory_mb <= 10240
    error_message = "Lambda memory must be between 128 and 10240 MB."
  }
}

variable "lambda_timeout_seconds" {
  description = "Lambda function timeout (seconds)"
  type        = number
  default     = 300
}

variable "ecs_cpu" {
  description = "ECS Fargate task CPU units"
  type        = number
  default     = 1024
}

variable "ecs_memory" {
  description = "ECS Fargate task memory (MB)"
  type        = number
  default     = 4096
}

variable "ecr_repository_name" {
  description = "ECR repository name for container images"
  type        = string
  default     = "pearls-aqi-predictor"
}
