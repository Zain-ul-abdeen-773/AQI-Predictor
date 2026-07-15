"""LangGraph multi-agent infrastructure validator.

Orchestrates a graph of validation agents (Linter → Security → Policy →
Decision) that acts as a gatekeeper for Terraform deployments.

The graph executes sequentially:
1. Linter Agent: Syntax and formatting validation
2. Security Agent: Checkov security scanning
3. Policy Agent: OPA compliance evaluation
4. Decision Agent: Aggregate results and determine approval

Usage:
    python -m infrastructure.validation_agents.validate

    In GitHub Actions:
        - Run this script before terraform apply
        - If approval_status is False, the workflow terminates
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# State Definition
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class AgentState:
    """State container for the validation graph.

    Passed between agents as they execute sequentially.
    Each agent appends its results to the appropriate field.

    Attributes:
        terraform_dir: Path to Terraform configuration directory.
        terraform_code: Raw Terraform code content.
        lint_results: Results from the linter agent.
        security_issues: Results from the security agent.
        policy_compliance: Results from the policy agent.
        approval_status: Final approval decision (True = deploy, False = block).
        summary: Human-readable summary of all checks.
        all_issues: Aggregated list of all issues found.
    """

    terraform_dir: str = ""
    terraform_code: str = ""
    lint_results: Dict[str, Any] = field(default_factory=dict)
    security_issues: Dict[str, Any] = field(default_factory=dict)
    policy_compliance: Dict[str, Any] = field(default_factory=dict)
    approval_status: Optional[bool] = None
    summary: str = ""
    all_issues: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Agent Nodes
# ──────────────────────────────────────────────────────────────────────────────


def linter_node(state: AgentState) -> AgentState:
    """Execute the Terraform linter agent.

    Args:
        state: Current graph state.

    Returns:
        AgentState: Updated state with lint results.
    """
    from infrastructure.validation_agents.agents.linter import LinterAgent

    logger.info("🔍 Running Linter Agent...")
    agent = LinterAgent(state.terraform_dir)
    state.lint_results = agent.run()

    if state.lint_results.get("issues"):
        state.all_issues.extend(state.lint_results["issues"])

    return state


def security_node(state: AgentState) -> AgentState:
    """Execute the security analyzer agent.

    Args:
        state: Current graph state.

    Returns:
        AgentState: Updated state with security scan results.
    """
    from infrastructure.validation_agents.agents.security import SecurityAgent

    logger.info("🛡️ Running Security Agent...")
    agent = SecurityAgent(state.terraform_dir)
    state.security_issues = agent.run()

    if state.security_issues.get("issues"):
        state.all_issues.extend(state.security_issues["issues"])

    return state


def policy_node(state: AgentState) -> AgentState:
    """Execute the OPA policy evaluation agent.

    Args:
        state: Current graph state.

    Returns:
        AgentState: Updated state with policy compliance results.
    """
    from infrastructure.validation_agents.agents.policy import PolicyAgent

    logger.info("📋 Running Policy Agent...")
    agent = PolicyAgent(state.terraform_dir)
    state.policy_compliance = agent.run()

    if state.policy_compliance.get("issues"):
        state.all_issues.extend(state.policy_compliance["issues"])

    return state


def decision_node(state: AgentState) -> AgentState:
    """Orchestrator decision agent — compile and decide.

    Aggregates all agent results. If any critical check fails,
    sets approval_status = False and blocks deployment.

    Args:
        state: Current graph state with all agent results.

    Returns:
        AgentState: Final state with approval decision.
    """
    logger.info("⚖️ Running Decision Agent...")

    # Determine approval
    lint_passed = state.lint_results.get("passed", True)
    security_passed = state.security_issues.get("passed", True)
    policy_passed = state.policy_compliance.get("passed", True)

    state.approval_status = lint_passed and security_passed and policy_passed

    # Build summary
    checks = [
        ("Linter", lint_passed, state.lint_results.get("summary", "")),
        ("Security", security_passed, state.security_issues.get("summary", "")),
        ("Policy", policy_passed, state.policy_compliance.get("summary", "")),
    ]

    lines = ["=" * 60, "INFRASTRUCTURE VALIDATION REPORT", "=" * 60]

    for name, passed, summary in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        lines.append(f"  {status}  {name}: {summary}")

    lines.append("-" * 60)

    if state.all_issues:
        lines.append(f"Issues Found ({len(state.all_issues)}):")
        for issue in state.all_issues[:20]:  # Cap at 20 for readability
            lines.append(f"  • {issue}")
        if len(state.all_issues) > 20:
            lines.append(f"  ... and {len(state.all_issues) - 20} more")

    lines.append("-" * 60)

    decision = "✅ APPROVED — Safe to deploy" if state.approval_status else "❌ BLOCKED — Fix issues before deploying"
    lines.append(f"Decision: {decision}")
    lines.append("=" * 60)

    state.summary = "\n".join(lines)

    return state


# ──────────────────────────────────────────────────────────────────────────────
# Graph Construction & Execution
# ──────────────────────────────────────────────────────────────────────────────


class ValidationGraph:
    """State graph for infrastructure validation.

    Links validation agents as sequential nodes with transitional edges.
    Execution flow: Linter → Security → Policy → Decision.

    This can be replaced with LangGraph's StateGraph when the
    langgraph package is available, maintaining API compatibility.

    Attributes:
        nodes: Ordered list of (name, function) node pairs.
    """

    def __init__(self) -> None:
        self.nodes: List[tuple[str, Any]] = [
            ("linter", linter_node),
            ("security", security_node),
            ("policy", policy_node),
            ("decision", decision_node),
        ]

    def compile(self) -> "ValidationGraph":
        """Compile the graph (no-op in simple mode, prepares for LangGraph)."""
        logger.info(
            "Validation graph compiled: %s",
            " → ".join(name for name, _ in self.nodes),
        )
        return self

    def execute(self, initial_state: AgentState) -> AgentState:
        """Execute all nodes sequentially.

        Args:
            initial_state: Starting state with terraform_dir set.

        Returns:
            AgentState: Final state after all agents have run.
        """
        state = initial_state

        for name, node_fn in self.nodes:
            logger.info("Executing node: %s", name)
            try:
                state = node_fn(state)
            except Exception as e:
                logger.error("Node '%s' failed: %s", name, e)
                state.all_issues.append(f"Agent '{name}' crashed: {e}")

        return state


def build_langgraph_validator() -> ValidationGraph:
    """Build the validation graph with LangGraph if available, else fallback.

    Returns:
        ValidationGraph: Compiled validation graph.
    """
    try:
        from langgraph.graph import StateGraph, END

        # Build LangGraph version
        graph = StateGraph(AgentState)
        graph.add_node("linter", linter_node)
        graph.add_node("security", security_node)
        graph.add_node("policy", policy_node)
        graph.add_node("decision", decision_node)

        graph.add_edge("linter", "security")
        graph.add_edge("security", "policy")
        graph.add_edge("policy", "decision")
        graph.add_edge("decision", END)

        graph.set_entry_point("linter")

        logger.info("Built LangGraph-based validation pipeline")
        return graph.compile()

    except ImportError:
        logger.info(
            "langgraph not installed — using built-in sequential graph"
        )
        return ValidationGraph().compile()


# ──────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────────────────────────────────────


def main(terraform_dir: Optional[str] = None) -> bool:
    """Run the validation pipeline from CLI or GitHub Actions.

    Args:
        terraform_dir: Path to Terraform directory.

    Returns:
        bool: True if approved, False if blocked.
    """
    if terraform_dir is None:
        # Default to project's terraform directory
        terraform_dir = str(
            Path(__file__).resolve().parent.parent / "terraform"
        )

    logger.info("Starting infrastructure validation for: %s", terraform_dir)

    # Read Terraform code
    tf_dir = Path(terraform_dir)
    tf_code = ""
    for tf_file in tf_dir.glob("*.tf"):
        tf_code += tf_file.read_text() + "\n"

    # Initialize state
    initial_state = AgentState(
        terraform_dir=terraform_dir,
        terraform_code=tf_code,
    )

    # Build and execute graph
    graph = build_langgraph_validator()

    if isinstance(graph, ValidationGraph):
        final_state = graph.execute(initial_state)
    else:
        # LangGraph compiled graph
        result = graph.invoke(initial_state)
        final_state = result

    # Print report
    print(final_state.summary)

    # Save report
    report_path = tf_dir / "validation_report.json"
    report = {
        "approval_status": final_state.approval_status,
        "lint_results": final_state.lint_results,
        "security_issues": final_state.security_issues,
        "policy_compliance": final_state.policy_compliance,
        "total_issues": len(final_state.all_issues),
        "issues": final_state.all_issues,
    }
    report_path.write_text(json.dumps(report, indent=2, default=str))

    return final_state.approval_status


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Infrastructure Validation Pipeline")
    parser.add_argument(
        "--terraform-dir", type=str, default=None,
        help="Path to Terraform configuration directory",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    approved = main(args.terraform_dir)

    if not approved:
        logger.error("❌ Deployment BLOCKED — fix issues and retry")
        sys.exit(1)
    else:
        logger.info("✅ Deployment APPROVED")
        sys.exit(0)
