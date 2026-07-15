"""Security analyzer agent using Checkov for Terraform scanning.

Invokes Checkov CLI to detect credentials leaks, permissive IAM roles,
non-encrypted parameters, and other security misconfigurations.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SecurityAgent:
    """Checkov-based security scanning agent for Terraform.

    Scans Terraform configurations for security vulnerabilities including:
    - Credentials and secrets in plain text
    - Permissive IAM policies
    - Unencrypted storage and parameters
    - Public-facing resources without proper controls

    Attributes:
        terraform_dir: Path to Terraform configuration directory.
    """

    def __init__(self, terraform_dir: str | Path) -> None:
        self.terraform_dir = Path(terraform_dir)

    def run(self) -> Dict[str, Any]:
        """Execute Checkov security scan.

        Returns:
            Dict with security scan results, issues, and pass/fail status.
        """
        results: Dict[str, Any] = {
            "agent": "security",
            "checks": [],
            "issues": [],
            "passed": True,
        }

        # Run Checkov scan
        checkov_result = self._run_checkov()
        results["checks"].append(checkov_result)

        # Run custom security checks
        custom_result = self._run_custom_checks()
        results["checks"].append(custom_result)

        # Aggregate results
        all_issues: List[str] = []
        for check in results["checks"]:
            all_issues.extend(check.get("details", []))
            if not check.get("passed", True):
                results["passed"] = False

        results["issues"] = all_issues
        results["summary"] = (
            f"Security: {'PASSED' if results['passed'] else 'FAILED'} "
            f"({len(all_issues)} issues found)"
        )

        logger.info(results["summary"])
        return results

    def _run_checkov(self) -> Dict[str, Any]:
        """Run Checkov security scanner against Terraform files."""
        try:
            result = subprocess.run(
                [
                    "checkov",
                    "--directory", str(self.terraform_dir),
                    "--framework", "terraform",
                    "--output", "json",
                    "--quiet",
                    "--compact",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

            try:
                checkov_output = json.loads(result.stdout)
                failed_checks = []

                if isinstance(checkov_output, list):
                    for framework_result in checkov_output:
                        failed = framework_result.get("results", {}).get("failed_checks", [])
                        for check in failed:
                            failed_checks.append(
                                f"[{check.get('check_id', 'unknown')}] "
                                f"{check.get('check_result', {}).get('result', 'FAILED')}: "
                                f"{check.get('name', 'unknown check')} "
                                f"in {check.get('file_path', 'unknown')}"
                            )

                passed = len(failed_checks) == 0
                return {
                    "name": "checkov_scan",
                    "passed": passed,
                    "details": failed_checks,
                    "message": f"Checkov: {len(failed_checks)} security issues" if failed_checks else "No issues",
                }

            except json.JSONDecodeError:
                return {
                    "name": "checkov_scan",
                    "passed": result.returncode == 0,
                    "details": [result.stderr] if result.stderr else [],
                    "message": "Checkov completed (non-JSON output)",
                }

        except FileNotFoundError:
            logger.info("Checkov not installed — running custom security checks only")
            return {
                "name": "checkov_scan",
                "passed": True,
                "details": ["Checkov not installed — skipped"],
                "message": "Skipped (checkov not installed)",
            }
        except Exception as e:
            return {
                "name": "checkov_scan",
                "passed": False,
                "details": [str(e)],
                "message": f"Error: {e}",
            }

    def _run_custom_checks(self) -> Dict[str, Any]:
        """Run custom security checks on Terraform files."""
        issues: List[str] = []

        for tf_file in self.terraform_dir.glob("*.tf"):
            content = tf_file.read_text()

            # Check for hardcoded secrets
            secret_patterns = [
                ("password", "Hardcoded password detected"),
                ("secret_key", "Hardcoded secret key detected"),
                ("access_key", "Hardcoded access key detected"),
                ('api_key = "', "Hardcoded API key detected (should use variable)"),
            ]
            for pattern, message in secret_patterns:
                if pattern in content.lower() and "variable" not in content.lower().split(pattern)[0][-50:]:
                    # Skip if it's a variable reference
                    if f"var." not in content.split(pattern)[0][-20:]:
                        issues.append(f"[CUSTOM] {message} in {tf_file.name}")

            # Check for overly permissive IAM
            if '"*"' in content and "Action" in content:
                if "Resource" in content and '"*"' in content:
                    # Check if it's necessary (like ecr:GetAuthorizationToken)
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if '"*"' in line and "Resource" in line:
                            context = "\n".join(lines[max(0, i-5):i+1])
                            if "GetAuthorizationToken" not in context:
                                issues.append(
                                    f"[CUSTOM] Wildcard resource in IAM policy ({tf_file.name})"
                                )

            # Check for unencrypted SSM parameters
            if "aws_ssm_parameter" in content and "SecureString" not in content:
                if "type" in content:
                    issues.append(
                        f"[CUSTOM] SSM parameter may not be encrypted in {tf_file.name}"
                    )

        passed = len(issues) == 0
        return {
            "name": "custom_security_checks",
            "passed": passed,
            "details": issues,
            "message": f"Custom: {len(issues)} issues" if issues else "No custom issues",
        }
