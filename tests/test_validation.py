"""Unit tests for LangGraph/LangChain infrastructure validation agents.

Tests the state graph, individual agent nodes (Linter, Security, Policy,
and Remediation), and the CLI entry point.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from infrastructure.validation_agents.validate import (
    AgentState,
    ValidationGraph,
    build_langgraph_validator,
    decision_node,
    linter_node,
    main,
    policy_node,
    remediation_node,
    security_node,
)
from infrastructure.validation_agents.agents.linter import LinterAgent
from infrastructure.validation_agents.agents.policy import PolicyAgent
from infrastructure.validation_agents.agents.remediation import RemediationAgent
from infrastructure.validation_agents.agents.security import SecurityAgent


@pytest.fixture
def dummy_tf_dir(tmp_path: Path) -> Path:
    """Create a temporary Terraform directory with dummy HCL files."""
    tf_dir = tmp_path / "terraform"
    tf_dir.mkdir()

    main_tf = tf_dir / "main.tf"
    main_tf.write_text("""
resource "aws_s3_bucket" "test" {
  bucket = "test-bucket"
}
""")
    return tf_dir


def test_agent_state_defaults() -> None:
    """Test default values of AgentState."""
    state = AgentState()
    assert state.terraform_dir == ""
    assert state.terraform_code == ""
    assert state.lint_results == {}
    assert state.security_issues == {}
    assert state.policy_compliance == {}
    assert state.remediation_plan == {}
    assert state.approval_status is None
    assert state.summary == ""
    assert state.all_issues == []


def test_linter_agent(dummy_tf_dir: Path) -> None:
    """Test LinterAgent execution on dummy directory."""
    agent = LinterAgent(dummy_tf_dir)
    result = agent.run()
    assert "agent" in result
    assert result["agent"] == "linter"
    assert "checks" in result
    assert "passed" in result
    assert "summary" in result


def test_security_agent(dummy_tf_dir: Path) -> None:
    """Test SecurityAgent execution on dummy directory."""
    agent = SecurityAgent(dummy_tf_dir)
    result = agent.run()
    assert "agent" in result
    assert result["agent"] == "security"
    assert "checks" in result
    assert "passed" in result


def test_policy_agent(dummy_tf_dir: Path) -> None:
    """Test PolicyAgent execution on dummy directory."""
    agent = PolicyAgent(dummy_tf_dir)
    result = agent.run()
    assert "agent" in result
    assert result["agent"] == "policy"
    assert "checks" in result
    assert "passed" in result


def test_remediation_agent() -> None:
    """Test RemediationAgent with sample issues."""
    issues = [
        "[CUSTOM] Wildcard resource in IAM policy",
        "check_no_public_s3 bucket has public acl",
    ]
    agent = RemediationAgent(terraform_code='resource "aws_s3_bucket" "test" {}', issues=issues)
    result = agent.run()
    assert result["agent"] == "remediation"
    assert len(result["remediations"]) == 2
    assert "summary" in result
    assert result["passed"] is True


def test_validation_nodes(dummy_tf_dir: Path) -> None:
    """Test sequential execution of graph nodes."""
    state = AgentState(terraform_dir=str(dummy_tf_dir), terraform_code='resource "aws_s3_bucket" "test" {}')

    state = linter_node(state)
    assert state.lint_results["agent"] == "linter"

    state = security_node(state)
    assert state.security_issues["agent"] == "security"

    state = policy_node(state)
    assert state.policy_compliance["agent"] == "policy"

    state = remediation_node(state)
    assert state.remediation_plan["agent"] == "remediation"

    state = decision_node(state)
    assert state.approval_status is not None
    assert "INFRASTRUCTURE VALIDATION REPORT" in state.summary


def test_build_and_execute_graph(dummy_tf_dir: Path) -> None:
    """Test execution via build_langgraph_validator."""
    graph = build_langgraph_validator()
    initial_state = AgentState(terraform_dir=str(dummy_tf_dir), terraform_code='resource "aws_s3_bucket" "test" {}')

    if isinstance(graph, ValidationGraph):
        final_state = graph.execute(initial_state)
    else:
        result = graph.invoke(initial_state)
        final_state = AgentState(**result) if isinstance(result, dict) else result

    assert final_state.approval_status is not None
    assert "INFRASTRUCTURE VALIDATION REPORT" in final_state.summary


def test_main_function(dummy_tf_dir: Path) -> None:
    """Test the main CLI pipeline execution."""
    # Run main on dummy_tf_dir
    approved = main(str(dummy_tf_dir))
    assert isinstance(approved, bool)

    report_path = dummy_tf_dir / "validation_report.json"
    assert report_path.exists()

    report_data = json.loads(report_path.read_text(encoding="utf-8"))
    assert "approval_status" in report_data
    assert "lint_results" in report_data
    assert "security_issues" in report_data
    assert "policy_compliance" in report_data
    assert "remediation_plan" in report_data
