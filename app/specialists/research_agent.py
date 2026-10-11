"""Research Specialist Agent powered by Gemini 3.7 Flash."""

import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import Any, Dict, List
from app.agent_framework import BaseSpecialistAgent, agent_tool


class ResearchSpecialistAgent(BaseSpecialistAgent):
    """Specialist agent for deep research, documentation synthesis, citations, and knowledge extraction."""

    def __init__(self, **kwargs):
        super().__init__(
            name="ResearchSpecialist",
            role_description="Expert researcher and technical writer specializing in knowledge synthesis, literature review, and documentation.",
            system_prompt=(
                "You are the Research Specialist Agent. You provide comprehensive, evidence-grounded research, "
                "structured summaries, architectural comparisons, and authoritative explanations."
            ),
            **kwargs
        )

    @agent_tool(
        name="lookup_topic_knowledge_base",
        description="Searches internal technical knowledge base for architectural patterns and documentation."
    )
    def lookup_topic_knowledge_base(self, query: str) -> Dict[str, Any]:
        """Search internal technical knowledge base."""
        kb_articles = {
            "jev": {
                "title": "TypeSafe Jev Decision Models",
                "summary": "System One decision model returning calibrated probabilities (noul, choice, score) in 70-500ms at $0.042/M tokens.",
                "primitives": ["Noul (yes/no)", "Choice (1 of N)", "Score (2-10 levels)"]
            },
            "gemini": {
                "title": "Google Gemini 3.7 Flash",
                "summary": "Frontier hybrid reasoning model with dynamic reasoning tokens, long context window, and high-speed execution.",
                "capabilities": ["Reasoning", "Multimodal", "Tool Calling", "Code Synthesis"]
            },
            "system_one": {
                "title": "System One vs System Two Architectures",
                "summary": "System One provides instant probabilistic routing; System Two performs deep generative execution and tool loops.",
                "benefits": "Reduces multi-agent routing cost by 90%+ and lowers latency from seconds to milliseconds."
            }
        }
        
        results = []
        for key, val in kb_articles.items():
            if key in query.lower() or any(w in query.lower() for w in val["title"].lower().split()):
                results.append(val)
                
        if not results:
            results.append({
                "title": f"General Knowledge for '{query}'",
                "summary": "Standard cloud architecture and software engineering principles apply."
            })
            
        return {"query": query, "matches": results}
