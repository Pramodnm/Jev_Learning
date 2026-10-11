"""Multi-Agent Orchestrator.

Combines TypeSafe Jev System One decision routing with Google Gemini 3.7 Flash
specialist agent execution in a Two-Stage Structured Decision & Execution (SDE) Cascade.
"""

from __future__ import annotations
import sys
import time
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.agent_framework import AgentRunResult, BaseSpecialistAgent
from app.config import settings
from app.jev_client import JevClient, RouteAction, RoutingDecision, ScoreAnswer
from app.specialists import (
    CodeSpecialistAgent,
    DataSpecialistAgent,
    DevOpsSpecialistAgent,
    ResearchSpecialistAgent,
)


class OrchestrationResult(BaseModel):
    user_query: str
    routing_decision: RoutingDecision
    selected_agent: str
    action_taken: RouteAction
    agent_output: Optional[str] = None
    tool_executions: List[Dict[str, Any]] = Field(default_factory=list)
    quality_score: Optional[ScoreAnswer] = None
    total_latency_ms: float = 0.0
    telemetry: Dict[str, Any] = Field(default_factory=dict)


class MultiAgentOrchestrator:
    """Orchestrates System One Jev routing with System Two Gemini 3.7 Flash execution."""

    def __init__(self, jev_client: Optional[JevClient] = None):
        self.jev = jev_client or JevClient()
        self.agents: Dict[str, BaseSpecialistAgent] = {
            "code_specialist": CodeSpecialistAgent(),
            "research_specialist": ResearchSpecialistAgent(),
            "devops_specialist": DevOpsSpecialistAgent(),
            "data_specialist": DataSpecialistAgent()
        }

    def get_candidate_agent_map(self) -> Dict[str, str]:
        """Returns map of agent identifiers to detailed rubrics for Jev Choice question."""
        return {
            "code_specialist": "Writing, debugging, optimizing, or reviewing Python code, algorithms, and application software.",
            "research_specialist": "Synthesizing documentation, explaining concepts, comparing architectures, and knowledge lookup.",
            "devops_specialist": "Kubernetes manifests, Docker containers, CI/CD pipelines, cloud configs, and infrastructure alerts.",
            "data_specialist": "SQL databases, JSON schema validation, statistical calculations, and data pipeline design."
        }

    def process_request(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        force_agent: Optional[str] = None,
        enable_quality_scoring: bool = True
    ) -> OrchestrationResult:
        """Execute full end-to-end orchestration pipeline."""
        total_start = time.perf_counter()

        # Step 1: System One Decision Routing (Jev)
        if force_agent and force_agent in self.agents:
            routing = RoutingDecision(
                target_agent=force_agent,
                action=RouteAction.AUTO,
                confidence=1.0,
                probabilities={force_agent: 1.0},
                reasoning=f"Agent manually overridden to '{force_agent}'.",
                latency_ms=0.0
            )
        else:
            agent_rubrics = self.get_candidate_agent_map()
            routing = self.jev.route_agent(
                task_state=query,
                candidate_agents=agent_rubrics,
                include_safety=True,
                include_complexity=True
            )

        selected_agent_key = routing.target_agent
        if selected_agent_key not in self.agents:
            # Fallback to research specialist if unrecognized
            selected_agent_key = "research_specialist"

        # Step 2: Gating Policy Evaluation
        if routing.action == RouteAction.REVIEW:
            total_latency = (time.perf_counter() - total_start) * 1000.0
            return OrchestrationResult(
                user_query=query,
                routing_decision=routing,
                selected_agent=selected_agent_key,
                action_taken=RouteAction.REVIEW,
                agent_output=f"Task paused for human review: {routing.reasoning}",
                total_latency_ms=round(total_latency, 2),
                telemetry={
                    "jev_latency_ms": routing.latency_ms,
                    "agent_latency_ms": 0.0,
                    "quality_latency_ms": 0.0
                }
            )

        # Step 3: System Two Specialist Execution (Gemini 3.7 Flash)
        specialist = self.agents[selected_agent_key]
        agent_res: AgentRunResult = specialist.execute_task(user_prompt=query, context=context)

        # Step 4: Post-Execution Verification / Quality Scoring (Jev System One)
        quality_score = None
        quality_start = time.perf_counter()
        if enable_quality_scoring and agent_res.output:
            score_eval = self.jev.evaluate(
                state={
                    "user_query": query,
                    "agent_output": agent_res.output[:1500]  # Cap for fast evaluation
                },
                questions={
                    "answer_quality": {
                        "type": "score",
                        "instructions": "Rate how accurately and thoroughly the agent output answers the user query.",
                        "criteria": [
                            "Incomplete, incorrect, or unhelpful",
                            "Partially correct but missing key details",
                            "Thorough, accurate, and high quality"
                        ]
                    }
                }
            )
            quality_score = score_eval.answers.get("answer_quality")
        quality_latency = (time.perf_counter() - quality_start) * 1000.0

        total_latency = (time.perf_counter() - total_start) * 1000.0

        return OrchestrationResult(
            user_query=query,
            routing_decision=routing,
            selected_agent=selected_agent_key,
            action_taken=routing.action,
            agent_output=agent_res.output,
            tool_executions=agent_res.tool_executions,
            quality_score=quality_score,
            total_latency_ms=round(total_latency, 2),
            telemetry={
                "jev_routing_latency_ms": routing.latency_ms,
                "agent_execution_latency_ms": agent_res.latency_ms,
                "agent_reasoning_tokens": agent_res.reasoning_tokens,
                "agent_total_tokens": agent_res.total_tokens,
                "quality_scoring_latency_ms": round(quality_latency, 2)
            }
        )
