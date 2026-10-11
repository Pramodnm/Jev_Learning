"""FastAPI OpenAPI Server for Jev Decision & Multi-Agent Orchestration.

Exposes OpenAPI-compliant REST endpoints for:
1. POST /v1/systemone: Native TypeSafe System One evaluation endpoint
2. POST /v1/agent/route: Fast Jev intent routing and confidence gating
3. POST /v1/agent/dispatch: Full end-to-end multi-agent orchestration
4. GET /v1/health: Health check and model registry status
"""
import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.jev_client import (
    ChoiceQuestion,
    JevClient,
    NoulQuestion,
    RouteAction,
    RoutingDecision,
    ScoreQuestion,
    SystemOneEvaluationResponse,
)
from app.orchestrator import MultiAgentOrchestrator, OrchestrationResult


app = FastAPI(
    title="TypeSafe Jev + Gemini Multi-Agent API",
    description="OpenAPI-compatible service for System One Calibrated Decision Routing and Gemini Specialist Execution.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jev_client = JevClient()
orchestrator = MultiAgentOrchestrator(jev_client=jev_client)


# ---------------------------------------------------------------------------
# Request & Response Models
# ---------------------------------------------------------------------------

class SystemOneRequest(BaseModel):
    state: Any = Field(..., description="Content or state to evaluate (string, dict, or list).")
    questions: Dict[str, Any] = Field(..., description="Map of question IDs to typed question objects.")


class RouteRequest(BaseModel):
    task: str = Field(..., description="User prompt or task description to route.")
    candidates: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional custom map of candidate agents and rubric descriptions."
    )
    include_safety: bool = Field(default=True, description="Perform Noul safety hazard evaluation.")
    include_complexity: bool = Field(default=True, description="Perform Score complexity evaluation.")


class DispatchRequest(BaseModel):
    query: str = Field(..., description="User prompt or task to execute.")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional structured task context.")
    force_agent: Optional[str] = Field(default=None, description="Manually bypass routing and force agent.")
    enable_quality_scoring: bool = Field(default=True, description="Post-execution quality scoring with Jev.")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/v1/health", tags=["System"])
def health_check():
    """Healthcheck endpoint returning system configuration."""
    return {
        "status": "healthy",
        "omnirouter_base_url": settings.base_url,
        "jev_model": settings.jev_model,
        "specialist_model": settings.specialist_model,
        "confidence_threshold_auto": settings.confidence_threshold_auto,
        "confidence_threshold_review": settings.confidence_threshold_review
    }


@app.post("/v1/systemone", response_model=SystemOneEvaluationResponse, tags=["Jev System One"])
def evaluate_system_one(req: SystemOneRequest):
    """Native TypeSafe System One evaluation endpoint (Noul, Choice, Score)."""
    try:
        return jev_client.evaluate(state=req.state, questions=req.questions)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System One evaluation failed: {str(e)}"
        )


@app.post("/v1/agent/route", response_model=RoutingDecision, tags=["Agent Routing"])
def route_agent_task(req: RouteRequest):
    """Evaluate task intent and return target specialist with calibrated confidence."""
    candidates = req.candidates or orchestrator.get_candidate_agent_map()
    return jev_client.route_agent(
        task_state=req.task,
        candidate_agents=candidates,
        include_safety=req.include_safety,
        include_complexity=req.include_complexity
    )


@app.post("/v1/agent/dispatch", response_model=OrchestrationResult, tags=["Multi-Agent Orchestration"])
def dispatch_task(req: DispatchRequest):
    """Full end-to-end orchestration: Jev routing -> Gemini specialist -> Jev verification."""
    return orchestrator.process_request(
        query=req.query,
        context=req.context,
        force_agent=req.force_agent,
        enable_quality_scoring=req.enable_quality_scoring
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api:app", host=settings.server_host, port=settings.server_port, reload=True)
