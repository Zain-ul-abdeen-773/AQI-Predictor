# ─────────────────────────────────────────────────────────────────────────────
# Terraform Variables
# Pearls AQI Predictor — Parameterized Configuration
# ─────────────────────────────────────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
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

# ── App Runner Configuration ────────────────────────────────────────────────

variable "app_runner_instance_role" {
  description = "IAM Role for App Runner to access ECR"
  type        = string
  default     = "AppRunnerECRAccessRole"
}

variable "app_runner_port" {
  description = "Port for App Runner to listen on"
  type        = number
  default     = 8000
}

# ── CI/CD Configuration ───────────────────────────────────────────────────

variable "github_repository" {
  description = "GitHub repository (owner/repo)"
  type        = string
  default     = "Zain-ul-abdeen-773/AQI-Predictor"
}

variable "github_branch" {
  description = "GitHub branch to deploy"
  type        = string
  default     = "main"
}
