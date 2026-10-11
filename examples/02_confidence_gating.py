"""Example 2: Confidence-Gated Routing & Human-in-the-Loop Escalation.

Demonstrates how calibrated confidence separates decisions into three tiers:
1. High Confidence (>= 0.85): Autonomous execution
2. Moderate Confidence (0.50 - 0.84): User confirmation recommended
3. Low Confidence / High Hazard (< 0.50 or safety risk): Human escalation
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.jev_client import JevClient, RouteAction


def main():
    print("=" * 65)
    print("Example 2: Confidence-Gated Routing Policy with TypeSafe Jev")
    print("=" * 65)

    client = JevClient()

    candidate_agents = {
        "code_agent": "Python, JavaScript, backend APIs, data structures, algorithms",
        "devops_agent": "Kubernetes, Docker, CI/CD pipelines, Terraform, server administration",
        "data_agent": "SQL queries, relational databases, data analytics, statistics"
    }

    test_cases = [
        ("High Confidence Clear Intent", "Create a FastAPI endpoint with JWT bearer authentication and rate limiting."),
        ("Moderate Confidence Hybrid Intent", "Can you configure the database connection pool settings in the Kubernetes configmap?"),
        ("Dangerous / Destructive Request", "sudo rm -rf /var/lib/mysql --no-preserve-root to clean up disk space quickly.")
    ]

    for title, task_prompt in test_cases:
        print(f"\n--- Testing Scenario: {title} ---")
        print(f"Prompt: \"{task_prompt}\"")

        decision = client.route_agent(
            task_state=task_prompt,
            candidate_agents=candidate_agents,
            include_safety=True,
            include_complexity=True
        )

        print(f"Target Agent:     {decision.target_agent}")
        print(f"Confidence Score: {decision.confidence:.2%}")
        print(f"Action Policy:    {decision.action.value.upper()}")
        if decision.safety_hazard_prob is not None:
            print(f"Safety Hazard P:  {decision.safety_hazard_prob:.2f}")
        print(f"Decision Reason:  {decision.reasoning}")
        print(f"Latency:          {decision.latency_ms:.1f} ms")

        if decision.action == RouteAction.AUTO:
            print(">> [ACTION]: Dispatching automatically to worker agent.")
        elif decision.action == RouteAction.CONFIRM:
            print(">> [ACTION]: Prompting user with suggested agent for approval.")
        else:
            print(">> [ACTION]: Blocked! Escalating to human supervisor / triage queue.")

    print("\n" + "=" * 65)


if __name__ == "__main__":
    main()
