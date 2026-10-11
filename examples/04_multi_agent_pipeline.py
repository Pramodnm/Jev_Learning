"""Example 4: Full Multi-Agent SDE Pipeline.

Demonstrates:
1. Jev System One routing decision (fast classifier)
2. Confidence gating
3. Gemini 3.7 Flash Specialist Execution (with OpenAPI tools)
4. Jev Post-Execution Quality Grading
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.orchestrator import MultiAgentOrchestrator


def main():
    print("=" * 70)
    print("Example 4: Full Multi-Agent SDE Pipeline (Jev + Gemini 3.7 Flash)")
    print("=" * 70)

    orchestrator = MultiAgentOrchestrator()

    user_query = (
        "Write a Python script that calculates Fibonacci numbers using memoization, "
        "and validate the syntax of the generated code."
    )

    print(f"\n[User Task]: {user_query}\n")

    result = orchestrator.process_request(query=user_query, enable_quality_scoring=True)

    print("\n--- 1. Jev Routing Decision ---")
    print(f"Assigned Specialist: {result.selected_agent}")
    print(f"Routing Action:      {result.action_taken.value.upper()}")
    print(f"Confidence:          {result.routing_decision.confidence:.2%}")
    print(f"Decision Latency:    {result.telemetry.get('jev_routing_latency_ms', 0):.1f} ms")

    if result.tool_executions:
        print("\n--- 2. Specialist Tool Executions ---")
        for tool in result.tool_executions:
            print(f"• Tool: {tool['tool']} (Iteration {tool['iteration']})")
            print(f"  Result: {str(tool['result'])[:150]}...")

    print("\n--- 3. Gemini Specialist Output ---")
    print(result.agent_output)

    if result.quality_score:
        print("\n--- 4. Jev Quality Verification ---")
        print(f"Quality Score: {result.quality_score.score:.2f} / 2.0 (Confidence: {result.quality_score.confidence:.2%})")

    print("\n--- 5. Telemetry ---")
    print(f"Total Pipeline Latency: {result.total_latency_ms:.1f} ms")
    print(f"Agent Execution Latency: {result.telemetry.get('agent_execution_latency_ms', 0):.1f} ms")
    print("=" * 70)


if __name__ == "__main__":
    main()
