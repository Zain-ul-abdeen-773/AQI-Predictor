# ─────────────────────────────────────────────────────────────────────────────
# Terraform Outputs
# ─────────────────────────────────────────────────────────────────────────────

output "ecr_repository_url" {
  description = "ECR repository URL for container images"
  value       = aws_ecr_repository.aqi_predictor.repository_url
}

output "lambda_function_arn" {
  description = "ARN of the feature pipeline Lambda function"
  value       = aws_lambda_function.feature_pipeline.arn
}

output "lambda_function_name" {
  description = "Name of the feature pipeline Lambda function"
  value       = aws_lambda_function.feature_pipeline.function_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS training cluster"
  value       = aws_ecs_cluster.training.arn
}

output "ecs_task_definition_arn" {
  description = "ARN of the training pipeline task definition"
  value       = aws_ecs_task_definition.training_pipeline.arn
}

output "feature_schedule_arn" {
  description = "ARN of the hourly feature pipeline EventBridge rule"
  value       = aws_cloudwatch_event_rule.feature_schedule.arn
}

output "training_log_group" {
  description = "CloudWatch log group for training pipeline"
  value       = aws_cloudwatch_log_group.training_pipeline.name
}

# ── App Runner Outputs ───────────────────────────────────────────────────

output "app_runner_url" {
  description = "Public URL of the FastAPI Dashboard via AWS App Runner"
  value       = "https://${aws_apprunner_service.api.service_url}"
}

output "training_schedule_arn" {
  description = "ARN of the daily training pipeline EventBridge rule"
  value       = aws_cloudwatch_event_rule.training_schedule.arn
}

output "ssm_parameter_prefix" {
  description = "SSM Parameter Store prefix for API keys"
  value       = "/${var.project_name}/${var.environment}"
}
