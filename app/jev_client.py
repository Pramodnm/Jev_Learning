"""TypeSafe Jev System One Decision Client.

Implements the three core System One decision primitives:
1. Noul: Calibrated yes/no probabilities (0.0 to 1.0)
2. Choice: Categorical selection with confidence and probability distributions
3. Score: Ordinal ranking across 2-10 levels with continuous weighted scoring

Also provides high-level intent routing and confidence gating for agentic workflows.
"""

from __future__ import annotations
import json
import sys
import time
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import httpx
from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import settings


# ---------------------------------------------------------------------------
# Primitives Data Models
# ---------------------------------------------------------------------------

class QuestionType(str, Enum):
    NOUL = "noul"
    CHOICE = "choice"
    SCORE = "score"


class NoulQuestion(BaseModel):
    type: QuestionType = QuestionType.NOUL
    instructions: Union[str, Dict[str, Any], List[Any]]
    criteria: Optional[Dict[str, Any]] = None


class ChoiceQuestion(BaseModel):
    type: QuestionType = QuestionType.CHOICE
    instructions: Union[str, Dict[str, Any], List[Any]]
    criteria: Dict[str, Any]  # Option -> description


class ScoreQuestion(BaseModel):
    type: QuestionType = QuestionType.SCORE
    instructions: Union[str, Dict[str, Any], List[Any]]
    criteria: List[Any]  # 2 to 10 ordered level descriptions


class NoulAnswer(BaseModel):
    type: str = "noul"
    noul: float = Field(..., ge=0.0, le=1.0)


class ChoiceAnswer(BaseModel):
    type: str = "choice"
    choice: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    probabilities: Dict[str, float] = Field(default_factory=dict)


class ScoreAnswer(BaseModel):
    type: str = "score"
    score: float
    confidence: float = Field(..., ge=0.0, le=1.0)
    legend: Dict[str, str] = Field(default_factory=dict)
    probabilities: Dict[str, float] = Field(default_factory=dict)


class SystemOneEvaluationResponse(BaseModel):
    model: str
    answers: Dict[str, Union[NoulAnswer, ChoiceAnswer, ScoreAnswer, Dict[str, Any]]]
    latency_ms: float
    raw_response: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Routing Policy Enums & Models
# ---------------------------------------------------------------------------

class RouteAction(str, Enum):
    AUTO = "auto"          # Autonomous dispatch to agent
    CONFIRM = "confirm"    # Require human/user confirmation before executing
    REVIEW = "review"      # Low confidence / ambiguous: escalate to human or fallback


class RoutingDecision(BaseModel):
    target_agent: str
    action: RouteAction
    confidence: float
    probabilities: Dict[str, float]
    safety_hazard_prob: Optional[float] = None
    complexity_score: Optional[float] = None
    reasoning: str
    latency_ms: float


# ---------------------------------------------------------------------------
# TypeSafe Jev Client Implementation
# ---------------------------------------------------------------------------

class JevClient:
    """Client for interacting with TypeSafe Jev decision models via OmniRouter."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.base_url = (base_url or settings.base_url).rstrip("/")
        self.api_key = api_key or settings.api_key
        self.model = model or settings.jev_model
        self.openai_client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            http_client=httpx.Client(timeout=30.0)
        )

    def evaluate(
        self,
        state: Union[str, Dict[str, Any], List[Any]],
        questions: Dict[str, Union[NoulQuestion, ChoiceQuestion, ScoreQuestion, Dict[str, Any]]]
    ) -> SystemOneEvaluationResponse:
        """Evaluate a state against a dictionary of typed System One questions."""
        start_time = time.perf_counter()

        # Format state into string if dict/list
        state_str = json.dumps(state, indent=2) if isinstance(state, (dict, list)) else str(state)

        # Prepare normalized question definitions
        normalized_q: Dict[str, Dict[str, Any]] = {}
        for q_id, q_val in questions.items():
            if isinstance(q_val, BaseModel):
                normalized_q[q_id] = q_val.model_dump(exclude_none=True)
            elif isinstance(q_val, dict):
                normalized_q[q_id] = q_val
            else:
                raise ValueError(f"Invalid question definition for '{q_id}': {q_val}")

        # Attempt 1: Call with Jev model via OmniRouter
        try:
            return self._evaluate_via_chat_completion(state_str, normalized_q, start_time)
        except Exception as e:
            # Fallback evaluation parser
            return self._evaluate_with_fallback(state_str, normalized_q, start_time, error_context=str(e))

    def _evaluate_via_chat_completion(
        self,
        state_str: str,
        questions: Dict[str, Dict[str, Any]],
        start_time: float
    ) -> SystemOneEvaluationResponse:
        """Call Jev Router with structured prompt adhering to TypeSafe RLCD output rules."""
        
        # Build System One decision schema prompt
        prompt_lines = [
            "You are TypeSafe Jev, a calibrated System One decision model.",
            "Evaluate the given STATE against the typed QUESTIONS.",
            "You MUST respond ONLY with a valid JSON object whose keys match the question IDs.",
            "",
            "Rules for Question Types:",
            "1. 'noul' (yes/no): Return {\"type\": \"noul\", \"noul\": <float between 0.0 and 1.0>}",
            "2. 'choice': Return {\"type\": \"choice\", \"choice\": \"<winning_key>\", \"confidence\": <float 0..1>, \"probabilities\": {<key>: <float>}}",
            "3. 'score': Return {\"type\": \"score\", \"score\": <float index 0..N-1>, \"confidence\": <float 0..1>, \"legend\": {<idx>: \"<desc>\"}, \"probabilities\": {<idx>: <float>}}",
            "",
            "STATE TO EVALUATE:",
            state_str,
            "",
            "QUESTIONS SPECIFICATION:",
            json.dumps(questions, indent=2),
            "",
            "Return JSON only. No explanations, no markdown formatting outside JSON."
        ]

        messages = [
            {"role": "user", "content": "\n".join(prompt_lines)}
        ]

        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"} if "router" not in self.model else None
        )

        content = response.choices[0].message.content or "{}"
        
        # Parse JSON
        content_cleaned = content.strip()
        if content_cleaned.startswith("```json"):
            content_cleaned = content_cleaned[7:]
        if content_cleaned.startswith("```"):
            content_cleaned = content_cleaned[3:]
        if content_cleaned.endswith("```"):
            content_cleaned = content_cleaned[:-3]
        content_cleaned = content_cleaned.strip()

        parsed_data = {}
        try:
            parsed_data = json.loads(content_cleaned)
        except json.JSONDecodeError:
            # If router returned plain choice string
            parsed_data = self._parse_plain_router_output(content_cleaned, questions)

        answers: Dict[str, Any] = {}
        for q_id, q_def in questions.items():
            ans = parsed_data.get(q_id, {})
            q_type = q_def.get("type", "choice")
            if q_type == "choice":
                choice_val = ans.get("choice") or ans.get("selected") or list(q_def.get("criteria", {}).keys())[0]
                conf = float(ans.get("confidence", 0.90))
                probs = ans.get("probabilities", {choice_val: conf})
                answers[q_id] = ChoiceAnswer(
                    type="choice",
                    choice=str(choice_val),
                    confidence=min(1.0, max(0.0, conf)),
                    probabilities=probs
                )
            elif q_type == "noul":
                noul_val = float(ans.get("noul", 0.5))
                answers[q_id] = NoulAnswer(
                    type="noul",
                    noul=min(1.0, max(0.0, noul_val))
                )
            elif q_type == "score":
                score_val = float(ans.get("score", 0.0))
                conf = float(ans.get("confidence", 0.85))
                legend = ans.get("legend", {str(i): str(v) for i, v in enumerate(q_def.get("criteria", []))})
                probs = ans.get("probabilities", {str(int(score_val)): conf})
                answers[q_id] = ScoreAnswer(
                    type="score",
                    score=score_val,
                    confidence=conf,
                    legend=legend,
                    probabilities=probs
                )

        latency = (time.perf_counter() - start_time) * 1000.0
        return SystemOneEvaluationResponse(
            model=self.model,
            answers=answers,
            latency_ms=round(latency, 2),
            raw_response={"raw_content": content}
        )

    def _parse_plain_router_output(self, text: str, questions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Parse unformatted text from router model into structured answers."""
        result = {}
        for q_id, q_def in questions.items():
            if q_def.get("type") == "choice":
                options = list(q_def.get("criteria", {}).keys())
                chosen = options[0]
                for opt in options:
                    if opt.lower() in text.lower():
                        chosen = opt
                        break
                result[q_id] = {
                    "type": "choice",
                    "choice": chosen,
                    "confidence": 0.88,
                    "probabilities": {chosen: 0.88}
                }
            elif q_def.get("type") == "noul":
                is_yes = any(w in text.lower() for w in ["yes", "true", "positive", "1"])
                result[q_id] = {
                    "type": "noul",
                    "noul": 0.90 if is_yes else 0.10
                }
            elif q_def.get("type") == "score":
                result[q_id] = {
                    "type": "score",
                    "score": 1.0,
                    "confidence": 0.80
                }
        return result

    def _evaluate_with_fallback(
        self,
        state_str: str,
        questions: Dict[str, Dict[str, Any]],
        start_time: float,
        error_context: str
    ) -> SystemOneEvaluationResponse:
        """Deterministic heuristic fallback if model endpoint is unreachable."""
        answers: Dict[str, Any] = {}
        state_lower = state_str.lower()

        for q_id, q_def in questions.items():
            q_type = q_def.get("type", "choice")
            if q_type == "choice":
                criteria = q_def.get("criteria", {})
                scores = {}
                for opt, desc in criteria.items():
                    opt_score = 0.1
                    desc_words = str(desc).lower().split()
                    for word in desc_words:
                        if len(word) > 3 and word in state_lower:
                            opt_score += 0.3
                    if opt.lower() in state_lower:
                        opt_score += 0.5
                    scores[opt] = opt_score
                
                total = sum(scores.values()) or 1.0
                probs = {k: round(v / total, 3) for k, v in scores.items()}
                best_opt = max(probs, key=probs.get)
                conf = probs[best_opt]

                answers[q_id] = ChoiceAnswer(
                    type="choice",
                    choice=best_opt,
                    confidence=conf,
                    probabilities=probs
                )
            elif q_type == "noul":
                answers[q_id] = NoulAnswer(type="noul", noul=0.50)
            elif q_type == "score":
                answers[q_id] = ScoreAnswer(
                    type="score",
                    score=1.0,
                    confidence=0.75,
                    legend={"0": "Low", "1": "Medium", "2": "High"},
                    probabilities={"1": 0.75}
                )

        latency = (time.perf_counter() - start_time) * 1000.0
        return SystemOneEvaluationResponse(
            model=f"{self.model}-fallback",
            answers=answers,
            latency_ms=round(latency, 2),
            raw_response={"fallback_reason": error_context}
        )

    def route_agent(
        self,
        task_state: Union[str, Dict[str, Any]],
        candidate_agents: Dict[str, str],
        include_safety: bool = True,
        include_complexity: bool = True
    ) -> RoutingDecision:
        """Route a task to the most appropriate specialist agent using Jev System One."""
        
        # Speculative Fan-out Questions
        questions: Dict[str, Any] = {
            "target_agent": ChoiceQuestion(
                instructions="Which specialist agent is best qualified to handle this user query/task?",
                criteria=candidate_agents
            )
        }

        if include_safety:
            questions["is_safety_hazard"] = NoulQuestion(
                instructions="Does this request contain harmful, malicious, or unsafe instructions?",
                criteria={"true": "Harmful or destructive command", "false": "Safe standard request"}
            )

        if include_complexity:
            questions["task_complexity"] = ScoreQuestion(
                instructions="Rate the architectural and reasoning complexity required for this task.",
                criteria=[
                    "Level 0: Direct factual lookup or trivial one-liner",
                    "Level 1: Moderate coding, multi-step calculation, or standard refactor",
                    "Level 2: Deep architectural design, multi-file synthesis, or complex debugging"
                ]
            )

        # Execute single roundtrip speculative evaluation
        eval_resp = self.evaluate(state=task_state, questions=questions)

        # Extract results
        agent_answer: ChoiceAnswer = eval_resp.answers["target_agent"]
        target_agent = agent_answer.choice
        confidence = agent_answer.confidence
        probs = agent_answer.probabilities

        safety_prob = None
        if include_safety and "is_safety_hazard" in eval_resp.answers:
            safety_prob = eval_resp.answers["is_safety_hazard"].noul

        complexity_val = None
        if include_complexity and "task_complexity" in eval_resp.answers:
            complexity_val = eval_resp.answers["task_complexity"].score

        # Apply Calibrated Routing Policy
        if safety_prob is not None and safety_prob > 0.70:
            action = RouteAction.REVIEW
            reasoning = f"Safety risk detected (hazard probability: {safety_prob:.2f}). Escalating to human oversight."
        elif confidence >= settings.confidence_threshold_auto:
            action = RouteAction.AUTO
            reasoning = f"High confidence ({confidence:.2%}) in specialist assignment '{target_agent}'."
        elif confidence >= settings.confidence_threshold_review:
            action = RouteAction.CONFIRM
            reasoning = f"Moderate confidence ({confidence:.2%}). Confirmation recommended before autonomous dispatch."
        else:
            action = RouteAction.REVIEW
            reasoning = f"Low confidence ({confidence:.2%}). Ambiguous intent across options {list(probs.keys())}."

        return RoutingDecision(
            target_agent=target_agent,
            action=action,
            confidence=confidence,
            probabilities=probs,
            safety_hazard_prob=safety_prob,
            complexity_score=complexity_val,
            reasoning=reasoning,
            latency_ms=eval_resp.latency_ms
        )
