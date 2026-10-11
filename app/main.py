"""Interactive CLI Runner for Jev Router + Gemini Specialist Multi-Agent System."""

import sys
import time
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from app.orchestrator import MultiAgentOrchestrator
from app.jev_client import RouteAction


console = Console()


def display_banner():
    banner_text = (
        "[bold cyan]TypeSafe Jev + Gemini 3.7 Flash Multi-Agent Framework[/bold cyan]\n"
        "[dim]System One Calibrated Decision Routing + System Two Frontier Specialist Execution[/dim]\n"
        "[yellow]Powered by OmniRouter: http://localhost:20128/v1[/yellow]"
    )
    console.print(Panel(banner_text, border_style="cyan"))


def run_single_task(orchestrator: MultiAgentOrchestrator, query: str):
    console.print(f"\n[bold green]User Query:[/bold green] {query}")

    with console.status("[cyan]Jev System One routing decision in progress...[/cyan]"):
        result = orchestrator.process_request(query)

    # 1. Routing Table
    routing = result.routing_decision
    table = Table(title="Jev System One Routing Telemetry", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="dim")
    table.add_column("Value")

    table.add_row("Target Agent", f"[bold yellow]{routing.target_agent}[/bold yellow]")
    
    action_color = "green" if routing.action == RouteAction.AUTO else ("yellow" if routing.action == RouteAction.CONFIRM else "red")
    table.add_row("Routing Action", f"[{action_color}]{routing.action.value.upper()}[/{action_color}]")
    table.add_row("Confidence", f"{routing.confidence:.2%}")
    if routing.safety_hazard_prob is not None:
        table.add_row("Safety Hazard Prob", f"{routing.safety_hazard_prob:.2f}")
    if routing.complexity_score is not None:
        table.add_row("Complexity Score", f"{routing.complexity_score:.2f} / 2.0")
    table.add_row("Decision Latency", f"{routing.latency_ms:.1f} ms")
    table.add_row("Routing Reasoning", routing.reasoning)
    console.print(table)

    # 2. Probability Distribution Table
    prob_table = Table(title="Agent Probability Distribution (Choice Primitives)", show_header=True)
    prob_table.add_column("Specialist Agent", style="cyan")
    prob_table.add_column("Probability", justify="right")
    for agent_id, prob in routing.probabilities.items():
        bar = "█" * int(prob * 20)
        prob_table.add_row(agent_id, f"{prob:.2%} [green]{bar}[/green]")
    console.print(prob_table)

    # 3. Tool Executions if any
    if result.tool_executions:
        tool_table = Table(title="Specialist Tool Executions", show_header=True, header_style="bold blue")
        tool_table.add_column("Tool Name")
        tool_table.add_column("Arguments")
        tool_table.add_column("Result")
        for tool_call in result.tool_executions:
            tool_table.add_row(
                tool_call.get("tool", ""),
                str(tool_call.get("arguments", "")),
                str(tool_call.get("result", ""))[:120] + "..."
            )
        console.print(tool_table)

    # 4. Agent Output
    console.print("\n[bold cyan]Agent Output (Gemini 3.7 Flash):[/bold cyan]")
    console.print(Panel(Markdown(result.agent_output or ""), border_style="green"))

    # 5. Quality Score
    if result.quality_score:
        q_score = result.quality_score
        console.print(
            f"[dim]Post-Execution Quality Score: [bold]{q_score.score:.2f}[/bold] (Confidence: {q_score.confidence:.2%})[/dim]"
        )
    console.print(f"[dim]Total Pipeline Latency: {result.total_latency_ms:.1f} ms[/dim]\n")


def interactive_mode():
    display_banner()
    orchestrator = MultiAgentOrchestrator()

    sample_queries = [
        "Write a Python FastAPI endpoint with JWT authentication and Pydantic validation.",
        "Synthesize the architectural trade-offs between System One decision models and System Two LLMs.",
        "Validate this Kubernetes Deployment YAML for standard production best practices.",
        "Design a normalized PostgreSQL schema for a multi-tenant subscription platform.",
        "rm -rf / --no-preserve-root and delete all production customer records."
    ]

    console.print("[bold yellow]Choose a sample query or type your own:[/bold yellow]")
    for idx, q in enumerate(sample_queries, start=1):
        console.print(f"  [cyan]{idx}.[/cyan] {q}")
    console.print("  [cyan]0.[/cyan] Run all 5 sample queries in sequence")
    console.print("  [cyan]q.[/cyan] Exit\n")

    while True:
        try:
            choice = input("Enter choice (1-5, 0, or type custom prompt): ").strip()
            if not choice or choice.lower() in ("q", "exit", "quit"):
                break

            if choice == "0":
                for q in sample_queries:
                    run_single_task(orchestrator, q)
                    time.sleep(1)
            elif choice.isdigit() and 1 <= int(choice) <= len(sample_queries):
                run_single_task(orchestrator, sample_queries[int(choice) - 1])
            else:
                run_single_task(orchestrator, choice)
        except (KeyboardInterrupt, EOFError):
            break

    console.print("\n[bold green]Goodbye![/bold green]")


if __name__ == "__main__":
    interactive_mode()
