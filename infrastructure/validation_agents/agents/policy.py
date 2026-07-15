"""OPA policy evaluation agent for compliance checking.

Evaluates Terraform configurations against OPA (Open Policy Agent)
policies written in Rego syntax to enforce organizational compliance.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class PolicyAgent:
    """Open Policy Agent (OPA) compliance evaluation agent.

    Runs Rego policies against Terraform plan/configuration to enforce:
    - No public S3 buckets
    - All ECS tasks must run on FARGATE
    - SSM parameter values must be encrypted
    - All resources must have required tags
    - IAM roles must follow least-privilege principle

    Attributes:
        terraform_dir: Path to Terraform configuration directory.
        policies_dir: Path to Rego policy files.
    """

    def __init__(
        self,
        terraform_dir: str | Path,
        policies_dir: str | Path | None = None,
    ) -> None:
        self.terraform_dir = Path(terraform_dir)
        self.policies_dir = Path(policies_dir) if policies_dir else (
            Path(__file__).parent.parent / "policies"
        )

    def run(self) -> Dict[str, Any]:
        """Execute OPA policy evaluation.

        Returns:
            Dict with policy compliance results.
        """
        results: Dict[str, Any] = {
            "agent": "policy",
            "checks": [],
            "issues": [],
            "passed": True,
        }

        # Run OPA evaluation
        opa_result = self._run_opa_eval()
        results["checks"].append(opa_result)

        # Run built-in policy checks (fallback when OPA not installed)
        builtin_result = self._run_builtin_policies()
        results["checks"].append(builtin_result)

        # Aggregate
        for check in results["checks"]:
            results["issues"].extend(check.get("details", []))
            if not check.get("passed", True):
                results["passed"] = False

        results["summary"] = (
            f"Policy: {'PASSED' if results['passed'] else 'FAILED'} "
            f"({len(results['issues'])} violations)"
        )

        logger.info(results["summary"])
        return results

    def _run_opa_eval(self) -> Dict[str, Any]:
        """Run OPA evaluation against Rego policies."""
        rego_files = list(self.policies_dir.glob("*.rego"))

        if not rego_files:
            return {
                "name": "opa_eval",
                "passed": True,
                "details": ["No Rego policy files found"],
                "message": "Skipped (no policies)",
            }

        try:
            # Convert Terraform to JSON for OPA input
            tf_json = self._terraform_to_json()
            if not tf_json:
                return {
                    "name": "opa_eval",
                    "passed": True,
                    "details": ["Could not generate Terraform JSON — using builtin checks"],
                    "message": "Skipped (no TF JSON)",
                }

            violations: List[str] = []

            for rego_file in rego_files:
                result = subprocess.run(
                    [
                        "opa", "eval",
                        "--data", str(rego_file),
                        "--input", "-",
                        "data.aws_compliance.violations",
                        "--format", "json",
                    ],
                    input=tf_json,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    try:
                        output = json.loads(result.stdout)
                        result_values = output.get("result", [])
                        for r in result_values:
                            expressions = r.get("expressions", [])
                            for expr in expressions:
                                value = expr.get("value", [])
                                if isinstance(value, list):
                                    violations.extend(value)
                    except json.JSONDecodeError:
                        pass

            passed = len(violations) == 0
            return {
                "name": "opa_eval",
                "passed": passed,
                "details": violations,
                "message": f"OPA: {len(violations)} violations" if violations else "Compliant",
            }

        except FileNotFoundError:
            return {
                "name": "opa_eval",
                "passed": True,
                "details": ["OPA not installed — using builtin policy checks"],
                "message": "Skipped (OPA not installed)",
            }
        except Exception as e:
            return {
                "name": "opa_eval",
                "passed": False,
                "details": [str(e)],
                "message": f"Error: {e}",
            }

    def _terraform_to_json(self) -> str | None:
        """Convert Terraform configuration to JSON for OPA input."""
        try:
            result = subprocess.run(
                ["terraform", "show", "-json"],
                cwd=str(self.terraform_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except Exception:
            pass
        return None

    def _run_builtin_policies(self) -> Dict[str, Any]:
        """Run built-in compliance policy checks by parsing Terraform files."""
        violations: List[str] = []

        for tf_file in self.terraform_dir.glob("*.tf"):
            content = tf_file.read_text()

            # Policy 1: No public S3 buckets
            if "aws_s3_bucket" in content and "acl" in content:
                if '"public-read"' in content or '"public-read-write"' in content:
                    violations.append(
                        f"POLICY_S3_PUBLIC: Public S3 bucket detected in {tf_file.name}"
                    )

            # Policy 2: ECS tasks must use FARGATE
            if "aws_ecs_task_definition" in content:
                if "FARGATE" not in content:
                    violations.append(
                        f"POLICY_ECS_FARGATE: ECS task not using FARGATE in {tf_file.name}"
                    )

            # Policy 3: SSM parameters must be SecureString
            if "aws_ssm_parameter" in content:
                # Check each SSM parameter block
                blocks = content.split("resource")
                for block in blocks:
                    if "aws_ssm_parameter" in block:
                        if '"String"' in block and '"SecureString"' not in block:
                            violations.append(
                                f"POLICY_SSM_ENCRYPT: Unencrypted SSM parameter in {tf_file.name}"
                            )

            # Policy 4: All resources must have tags
            if "resource" in content:
                resource_blocks = content.split('resource "')
                for block in resource_blocks[1:]:  # Skip first split
                    resource_type = block.split('"')[0]
                    # Skip resources that don't support tags
                    no_tag_resources = {
                        "aws_iam_role_policy", "aws_iam_role_policy_attachment",
                        "aws_lambda_permission", "aws_ecr_lifecycle_policy",
                        "aws_cloudwatch_event_target",
                    }
                    if resource_type not in no_tag_resources:
                        if "tags" not in block and "default_tags" not in content:
                            violations.append(
                                f"POLICY_TAGS: Resource '{resource_type}' missing tags in {tf_file.name}"
                            )

            # Policy 5: CloudWatch log retention must be set
            if "aws_cloudwatch_log_group" in content:
                if "retention_in_days" not in content:
                    violations.append(
                        f"POLICY_LOG_RETENTION: Log group missing retention policy in {tf_file.name}"
                    )

        passed = len(violations) == 0
        return {
            "name": "builtin_policies",
            "passed": passed,
            "details": violations,
            "message": f"Builtin: {len(violations)} violations" if violations else "All policies satisfied",
        }
