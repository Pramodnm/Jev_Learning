"""Data & Schema Specialist Agent powered by Gemini 3.7 Flash."""

import json
import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import Any, Dict, List
from app.agent_framework import BaseSpecialistAgent, agent_tool


class DataSpecialistAgent(BaseSpecialistAgent):
    """Specialist agent for data modeling, SQL queries, analytics, JSON schema design, and metrics."""

    def __init__(self, **kwargs):
        super().__init__(
            name="DataSpecialist",
            role_description="Expert data engineer specializing in SQL, database indexing, JSON schemas, analytics, and data transformations.",
            system_prompt=(
                "You are the Data Specialist Agent. You produce clean SQL queries, validate data structures, "
                "design normalized database schemas, and compute statistical summaries."
            ),
            **kwargs
        )

    @agent_tool(
        name="analyze_json_schema",
        description="Inspects JSON payloads to infer types, field presence, and generate JSON Schema definitions."
    )
    def analyze_json_schema(self, json_str: str) -> Dict[str, Any]:
        """Infer types and schema from JSON."""
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                inferred = {k: type(v).__name__ for k, v in data.items()}
                return {
                    "valid_json": True,
                    "top_level_type": "object",
                    "field_count": len(inferred),
                    "fields": inferred
                }
            elif isinstance(data, list):
                return {
                    "valid_json": True,
                    "top_level_type": "array",
                    "item_count": len(data),
                    "sample_item_type": type(data[0]).__name__ if data else "empty"
                }
            return {"valid_json": True, "top_level_type": type(data).__name__}
        except Exception as e:
            return {"valid_json": False, "error": str(e)}

    @agent_tool(
        name="compute_summary_stats",
        description="Calculates summary statistics (mean, min, max, count) for a list of numbers."
    )
    def compute_summary_stats(self, numbers: List[float]) -> Dict[str, Any]:
        """Compute basic summary statistics."""
        if not numbers:
            return {"count": 0, "error": "Empty list"}
        return {
            "count": len(numbers),
            "min": min(numbers),
            "max": max(numbers),
            "mean": sum(numbers) / len(numbers)
        }
