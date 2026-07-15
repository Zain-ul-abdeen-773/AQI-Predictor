# ─────────────────────────────────────────────────────────────────────────────
# OPA Rego Policy: AWS Compliance Rules
# Pearls AQI Predictor — Infrastructure Validation
# ─────────────────────────────────────────────────────────────────────────────

package aws_compliance

# ── Deny public S3 buckets ──────────────────────────────────────────────────

violations[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_s3_bucket"
    resource.change.after.acl == "public-read"
    msg := sprintf("S3 bucket '%s' must not be publicly readable", [resource.address])
}

violations[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_s3_bucket"
    resource.change.after.acl == "public-read-write"
    msg := sprintf("S3 bucket '%s' must not be publicly writable", [resource.address])
}

# ── ECS tasks must run on FARGATE ───────────────────────────────────────────

violations[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_ecs_task_definition"
    not fargate_compatible(resource)
    msg := sprintf("ECS task '%s' must use FARGATE launch type", [resource.address])
}

fargate_compatible(resource) {
    resource.change.after.requires_compatibilities[_] == "FARGATE"
}

# ── SSM parameters must be encrypted ───────────────────────────────────────

violations[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_ssm_parameter"
    resource.change.after.type != "SecureString"
    msg := sprintf("SSM parameter '%s' must use SecureString type", [resource.address])
}

# ── CloudWatch log groups must have retention ───────────────────────────────

violations[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_cloudwatch_log_group"
    not resource.change.after.retention_in_days
    msg := sprintf("CloudWatch log group '%s' must have retention_in_days set", [resource.address])
}

violations[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_cloudwatch_log_group"
    resource.change.after.retention_in_days > 365
    msg := sprintf("CloudWatch log group '%s' retention exceeds 365 days", [resource.address])
}

# ── Lambda functions must have timeout ──────────────────────────────────────

violations[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_lambda_function"
    resource.change.after.timeout > 900
    msg := sprintf("Lambda function '%s' timeout exceeds 900 seconds", [resource.address])
}

# ── ECR repositories must have image scanning ──────────────────────────────

violations[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_ecr_repository"
    not resource.change.after.image_scanning_configuration.scan_on_push
    msg := sprintf("ECR repository '%s' must have scan_on_push enabled", [resource.address])
}

# ── All resources must have project tag ─────────────────────────────────────

violations[msg] {
    resource := input.resource_changes[_]
    requires_tags(resource.type)
    not resource.change.after.tags.Project
    msg := sprintf("Resource '%s' must have a 'Project' tag", [resource.address])
}

requires_tags(resource_type) {
    taggable := {
        "aws_lambda_function",
        "aws_ecs_cluster",
        "aws_ecr_repository",
        "aws_cloudwatch_log_group",
        "aws_ssm_parameter",
    }
    taggable[resource_type]
}
