"""Example 3: Speculative Fan-out in a Single Request.

Demonstrates sending 5 distinct architectural and routing questions about
a single incoming pull request / commit diff in one fast API call.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.jev_client import JevClient, NoulQuestion, ChoiceQuestion, ScoreQuestion


def main():
    print("=" * 65)
    print("Example 3: Speculative Fan-Out Batching with Jev")
    print("=" * 65)

    client = JevClient()

    pr_diff_state = {
        "pr_id": 482,
        "title": "feat(auth): Add OAuth2 Google and GitHub login providers",
        "changed_files": ["app/auth/oauth.py", "app/routes/login.py", "alembic/versions/004_oauth.py"],
        "lines_added": 340,
        "lines_deleted": 12,
        "author": "dev-contractor",
        "summary": "Introduces OAuth2 social logins. Alters users table to add provider_id column and updates token signing logic."
    }

    print("\n[State: Pull Request Context]:")
    print(json.dumps(pr_diff_state, indent=2))

    # Speculative Fan-out: 5 questions evaluated simultaneously
    questions = {
        "primary_reviewer": ChoiceQuestion(
            instructions="Which specialist should lead the code review?",
            criteria={
                "security_architect": "Changes involving authentication, cryptographic tokens, or permissions",
                "database_specialist": "Schema migrations, indexing, table locks",
                "frontend_lead": "UI components and client state"
            }
        ),
        "requires_db_migration": NoulQuestion(
            instructions="Does this pull request include a database schema change or migration?"
        ),
        "touches_security_perimeter": NoulQuestion(
            instructions="Does this PR modify authentication, credentials, or security token handlers?"
        ),
        "risk_level_score": ScoreQuestion(
            instructions="Rate the deployment risk level.",
            criteria=[
                "Low risk: pure additive logic or docs",
                "Medium risk: standard API additions",
                "High risk: core auth / database alterations"
            ]
        ),
        "needs_canary_rollout": NoulQuestion(
            instructions="Should this feature be deployed via a staged canary rollout?"
        )
    }

    print(f"\n[Evaluating {len(questions)} Questions in a Single System One Pass]...")
    response = client.evaluate(state=pr_diff_state, questions=questions)

    print(f"\n[Completed in {response.latency_ms:.1f} ms!]")
    print("-" * 65)

    for q_id, ans in response.answers.items():
        if hasattr(ans, "choice"):
            print(f"• {q_id}: Choice = '{ans.choice}' (Confidence: {ans.confidence:.2%})")
        elif hasattr(ans, "noul"):
            print(f"• {q_id}: Probability = {ans.noul:.2%}")
        elif hasattr(ans, "score"):
            print(f"• {q_id}: Score = {ans.score:.2f} / 2.0 (Confidence: {ans.confidence:.2%})")

    print("=" * 65)


if __name__ == "__main__":
    main()
