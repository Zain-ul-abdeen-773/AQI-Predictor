# ─────────────────────────────────────────────────────────────────────────────
# Main Terraform Configuration
# Pearls AQI Predictor — Serverless AWS Infrastructure
#
# Resources:
# - SSM Parameter Store for API keys
# - EventBridge schedules for automated pipelines
# - Lambda function for feature pipeline (hourly)
# - ECS Fargate task for training pipeline (daily)
# - ECR repository for container images
# - CloudWatch log groups for monitoring
# ─────────────────────────────────────────────────────────────────────────────

# ── SSM Parameter Store (Encrypted API Keys) ─────────────────────────────

resource "aws_ssm_parameter" "aqicn_api_key" {
  name        = "/${var.project_name}/${var.environment}/AQICN_API_KEY"
  description = "AQICN API token for air quality data ingestion"
  type        = "SecureString"
  value       = var.aqicn_api_key

  tags = {
    Component = "DataPipeline"
  }
}

resource "aws_ssm_parameter" "openweather_api_key" {
  name        = "/${var.project_name}/${var.environment}/OPENWEATHER_API_KEY"
  description = "OpenWeatherMap API key for meteorological data"
  type        = "SecureString"
  value       = var.openweather_api_key

  tags = {
    Component = "DataPipeline"
  }
}

resource "aws_ssm_parameter" "hopsworks_api_key" {
  name        = "/${var.project_name}/${var.environment}/HOPSWORKS_API_KEY"
  description = "Hopsworks Feature Store API key"
  type        = "SecureString"
  value       = var.hopsworks_api_key

  tags = {
    Component = "FeatureStore"
  }
}

# ── ECR Repository ───────────────────────────────────────────────────────

resource "aws_ecr_repository" "aqi_predictor" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"
  force_delete         = false

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "cleanup" {
  repository = aws_ecr_repository.aqi_predictor.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}

# ── IAM Roles ────────────────────────────────────────────────────────────

# Lambda execution role
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter/${var.project_name}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:GetAuthorizationToken",
        ]
        Resource = "*"
      }
    ]
  })
}

# ECS task execution role
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${var.project_name}-ecs-task-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter/${var.project_name}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:GetAuthorizationToken",
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.project_name}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ── Lambda Function (Feature Pipeline — Hourly) ─────────────────────────

resource "aws_lambda_function" "feature_pipeline" {
  function_name = "${var.project_name}-feature-pipeline"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.aqi_predictor.repository_url}:feature-latest"
  timeout       = var.lambda_timeout_seconds
  memory_size   = var.lambda_memory_mb

  image_config {
    command = ["data_pipeline.ingest.handler"]
  }

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      SSM_PREFIX     = "/${var.project_name}/${var.environment}"
      PIPELINE_TYPE  = "feature"
    }
  }

  depends_on = [aws_ecr_repository.aqi_predictor]
}

# ── ECS Cluster & Task (Training Pipeline — Daily) ──────────────────────

resource "aws_ecs_cluster" "training" {
  name = "${var.project_name}-training"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "training_pipeline" {
  family                   = "${var.project_name}-training"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_cpu
  memory                   = var.ecs_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name      = "training-pipeline"
    image     = "${aws_ecr_repository.aqi_predictor.repository_url}:training-latest"
    essential = true

    command = ["python", "-m", "training_pipeline.train"]

    environment = [
      { name = "ENVIRONMENT", value = var.environment },
      { name = "SSM_PREFIX", value = "/${var.project_name}/${var.environment}" },
      { name = "PIPELINE_TYPE", value = "training" },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.project_name}/training"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "training"
      }
    }
  }])
}

# ── EventBridge Schedules ────────────────────────────────────────────────

resource "aws_cloudwatch_event_rule" "feature_schedule" {
  name                = "${var.project_name}-feature-hourly"
  description         = "Trigger feature pipeline every hour"
  schedule_expression = var.feature_pipeline_schedule
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "feature_lambda" {
  rule      = aws_cloudwatch_event_rule.feature_schedule.name
  target_id = "feature-pipeline"
  arn       = aws_lambda_function.feature_pipeline.arn
}

resource "aws_lambda_permission" "eventbridge_feature" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.feature_pipeline.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.feature_schedule.arn
}

resource "aws_cloudwatch_event_rule" "training_schedule" {
  name                = "${var.project_name}-training-daily"
  description         = "Trigger training pipeline daily"
  schedule_expression = var.training_pipeline_schedule
  state               = "ENABLED"
}

# ── CloudWatch Log Groups ────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "feature_pipeline" {
  name              = "/aws/lambda/${var.project_name}-feature-pipeline"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "training_pipeline" {
  name              = "/ecs/${var.project_name}/training"
  retention_in_days = 30
}

# ── App Runner Service (FastAPI Dashboard) ────────────────────────────────

resource "aws_iam_role" "apprunner_build_role" {
  name = "${var.project_name}-apprunner-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "build.apprunner.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr_policy" {
  role       = aws_iam_role.apprunner_build_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

resource "aws_apprunner_service" "api" {
  service_name = "${var.project_name}-api"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_build_role.arn
    }
    image_repository {
      image_identifier      = "${aws_ecr_repository.aqi_predictor.repository_url}:latest"
      image_repository_type = "ECR"
      image_configuration {
        port = var.app_runner_port
      }
    }
    auto_deployments_enabled = true
  }

  instance_configuration {
    cpu    = "1024"
    memory = "2048"
  }

  depends_on = [
    aws_iam_role_policy_attachment.apprunner_ecr_policy
  ]
}
