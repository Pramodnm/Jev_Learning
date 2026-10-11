"""DevOps Specialist Agent powered by Gemini 3.7 Flash."""

import re
import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import Any, Dict, List
from app.agent_framework import BaseSpecialistAgent, agent_tool


class DevOpsSpecialistAgent(BaseSpecialistAgent):
    """Specialist agent for cloud infrastructure, Kubernetes, CI/CD pipelines, Docker, and alert triage."""

    def __init__(self, **kwargs):
        super().__init__(
            name="DevOpsSpecialist",
            role_description="Expert DevOps & SRE engineer specializing in Kubernetes, CI/CD pipelines, Terraform, Docker, and infrastructure reliability.",
            system_prompt=(
                "You are the DevOps Specialist Agent. You analyze infrastructure manifests, troubleshoot CI/CD pipelines, "
                "triage alerts, and provide robust deployment configurations."
            ),
            **kwargs
        )

    @agent_tool(
        name="validate_kubernetes_yaml",
        description="Validates a Kubernetes manifest structure for required fields (apiVersion, kind, metadata.name, spec)."
    )
    def validate_kubernetes_yaml(self, manifest_text: str) -> Dict[str, Any]:
        """Validate basic Kubernetes YAML structure."""
        has_api_version = bool(re.search(r"apiVersion:\s*[\w\.\/]+", manifest_text))
        has_kind = bool(re.search(r"kind:\s*\w+", manifest_text))
        has_metadata = "metadata:" in manifest_text
        has_spec = "spec:" in manifest_text
        
        is_valid = has_api_version and has_kind and has_metadata
        return {
            "is_valid_structure": is_valid,
            "has_apiVersion": has_api_version,
            "has_kind": has_kind,
            "has_metadata": has_metadata,
            "has_spec": has_spec,
            "recommendations": [] if is_valid else ["Ensure apiVersion, kind, and metadata are specified."]
        }

    @agent_tool(
        name="diagnose_ci_build_log",
        description="Parses build and test logs to categorize errors into dependency, test failure, timeout, or syntax."
    )
    def diagnose_ci_build_log(self, log_snippet: str) -> Dict[str, Any]:
        """Analyze CI/CD log snippets."""
        log_lower = log_snippet.lower()
        category = "unknown"
        if "pip install" in log_lower or "nomodulefound" in log_lower or "could not resolve dependency" in log_lower:
            category = "dependency_resolution_failure"
        elif "assert" in log_lower or "failed test" in log_lower or "test suite failed" in log_lower:
            category = "test_assertion_failure"
        elif "timed out" in log_lower or "deadline exceeded" in log_lower:
            category = "execution_timeout"
        elif "syntaxerror" in log_lower or "indentationerror" in log_lower:
            category = "syntax_error"

        return {
            "detected_category": category,
            "sample_lines": [line.strip() for line in log_snippet.splitlines() if line.strip()][:5]
        }
