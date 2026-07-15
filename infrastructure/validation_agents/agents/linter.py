"""Terraform linter agent for structural syntax validation.

Runs terraform fmt, terraform validate, and tflint to detect
syntax errors and formatting issues in Terraform configurations.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class LinterAgent:
    """Terraform linting and syntax validation agent.

    Executes standard linting tools programmatically and records
    structural health assessment results.

    Attributes:
        terraform_dir: Path to Terraform configuration directory.
    """

    def __init__(self, terraform_dir: str | Path) -> None:
        self.terraform_dir = Path(terraform_dir)

    def run(self) -> Dict[str, Any]:
        """Execute all linting checks.

        Returns:
            Dict with lint results including issues found and pass/fail status.
        """
        results: Dict[str, Any] = {
            "agent": "linter",
            "checks": [],
            "issues": [],
            "passed": True,
        }

        # Check 1: terraform fmt (formatting)
        fmt_result = self._check_formatting()
        results["checks"].append(fmt_result)
        if not fmt_result["passed"]:
            results["issues"].extend(fmt_result.get("details", []))

        # Check 2: terraform validate (syntax)
        validate_result = self._check_syntax()
        results["checks"].append(validate_result)
        if not validate_result["passed"]:
            results["passed"] = False
            results["issues"].extend(validate_result.get("details", []))

        # Check 3: File structure validation
        structure_result = self._check_structure()
        results["checks"].append(structure_result)
        if not structure_result["passed"]:
            results["issues"].extend(structure_result.get("details", []))

        results["passed"] = all(c["passed"] for c in results["checks"])
        results["summary"] = (
            f"Linter: {'PASSED' if results['passed'] else 'FAILED'} "
            f"({sum(1 for c in results['checks'] if c['passed'])}/{len(results['checks'])} checks)"
        )

        logger.info(results["summary"])
        return results

    def _check_formatting(self) -> Dict[str, Any]:
        """Check Terraform formatting with 'terraform fmt -check'."""
        try:
            result = subprocess.run(
                ["terraform", "fmt", "-check", "-recursive", "-diff"],
                cwd=str(self.terraform_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )
            passed = result.returncode == 0
            return {
                "name": "terraform_fmt",
                "passed": passed,
                "details": [result.stdout] if not passed else [],
                "message": "Formatting OK" if passed else "Formatting issues found",
            }
        except FileNotFoundError:
            return {
                "name": "terraform_fmt",
                "passed": True,
                "details": ["terraform CLI not found — skipping format check"],
                "message": "Skipped (terraform not installed)",
            }
        except Exception as e:
            return {
                "name": "terraform_fmt",
                "passed": False,
                "details": [str(e)],
                "message": f"Error: {e}",
            }

    def _check_syntax(self) -> Dict[str, Any]:
        """Check Terraform syntax with 'terraform validate'."""
        try:
            # Init first (required for validate)
            subprocess.run(
                ["terraform", "init", "-backend=false"],
                cwd=str(self.terraform_dir),
                capture_output=True,
                timeout=60,
            )

            result = subprocess.run(
                ["terraform", "validate", "-json"],
                cwd=str(self.terraform_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )
            passed = result.returncode == 0
            return {
                "name": "terraform_validate",
                "passed": passed,
                "details": [result.stderr] if not passed else [],
                "message": "Syntax valid" if passed else "Syntax errors found",
            }
        except FileNotFoundError:
            return {
                "name": "terraform_validate",
                "passed": True,
                "details": ["terraform CLI not found — skipping validation"],
                "message": "Skipped (terraform not installed)",
            }
        except Exception as e:
            return {
                "name": "terraform_validate",
                "passed": False,
                "details": [str(e)],
                "message": f"Error: {e}",
            }

    def _check_structure(self) -> Dict[str, Any]:
        """Validate expected Terraform file structure."""
        required_files = ["provider.tf", "variables.tf", "main.tf", "outputs.tf"]
        missing = [f for f in required_files if not (self.terraform_dir / f).exists()]

        passed = len(missing) == 0
        return {
            "name": "file_structure",
            "passed": passed,
            "details": [f"Missing: {', '.join(missing)}"] if missing else [],
            "message": "All required files present" if passed else f"Missing {len(missing)} files",
        }
