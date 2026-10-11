"""Example 1: Core TypeSafe Jev System One Decision Primitives.

Demonstrates:
1. Noul: Calibrated yes/no probabilities
2. Choice: Multi-option selection with confidence distribution
3. Score: Ordinal rubric rating with continuous scoring
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.jev_client import JevClient, NoulQuestion, ChoiceQuestion, ScoreQuestion


def main():
    print("=" * 60)
    print("Example 1: TypeSafe Jev System One Decision Primitives")
    print("=" * 60)

    client = JevClient()

    # 1. State to evaluate
    alert_payload = {
        "alertname": "PostgresDiskFillingFast",
        "severity": "critical",
        "instance": "db-primary-prod-01",
        "disk_free_percent": 3.8,
        "growth_rate_gb_per_hour": 15.2,
        "summary": "Database primary partition /data is 96.2% full and will exhaust disk in under 2 hours."
    }

    print("\n[Input State]:")
    print(json.dumps(alert_payload, indent=2))

    # 2. Define Typed Questions
    questions = {
        # Primitive A: Noul (Yes/No)
        "is_production_outage_risk": NoulQuestion(
            instructions="Does this alert indicate an imminent risk of a production outage?",
            criteria={
                "true": "Critical failure expected within hours",
                "false": "Informational or non-urgent metric"
            }
        ),
        # Primitive B: Choice (1 of N)
        "assigned_oncall_team": ChoiceQuestion(
            instructions="Which engineering team must be paged immediately?",
            criteria={
                "dba_platform": "Database infrastructure, disk capacity, replication, PostgreSQL",
                "network_eng": "VPC, DNS, routers, load balancers, firewall",
                "frontend_eng": "Web application UI, client-side bundle, CSS",
                "security_ops": "Compromised credentials, malware, unauthorized access"
            }
        ),
        # Primitive C: Score (2 to 10 Levels)
        "incident_urgency_score": ScoreQuestion(
            instructions="Rate the incident urgency level along standard severity rubrics.",
            criteria=[
                "SEV-4: Minor issue, fix during standard business hours",
                "SEV-3: Moderate issue, requires investigation today",
                "SEV-2: Major issue, page secondary on-call engineer",
                "SEV-1: Critical emergency, page primary on-call immediately"
            ]
        )
    }

    print("\n[Sending Evaluation Request to OmniRouter Jev Model]...")
    response = client.evaluate(state=alert_payload, questions=questions)

    print(f"\n[Response Received in {response.latency_ms:.1f} ms] (Model: {response.model})")
    print("-" * 60)

    # Inspect Noul Answer
    noul_ans = response.answers["is_production_outage_risk"]
    print(f"1. Noul Answer (Outage Risk):")
    print(f"   Probability: {noul_ans.noul:.2%}")

    # Inspect Choice Answer
    choice_ans = response.answers["assigned_oncall_team"]
    print(f"\n2. Choice Answer (Assigned Team):")
    print(f"   Winning Choice: {choice_ans.choice}")
    print(f"   Confidence: {choice_ans.confidence:.2%}")
    print(f"   Probabilities: {choice_ans.probabilities}")

    # Inspect Score Answer
    score_ans = response.answers["incident_urgency_score"]
    print(f"\n3. Score Answer (Urgency Level):")
    print(f"   Weighted Score: {score_ans.score:.2f} / 3.0")
    print(f"   Confidence: {score_ans.confidence:.2%}")
    print(f"   Legend: {score_ans.legend}")
    print("=" * 60)


if __name__ == "__main__":
    main()
