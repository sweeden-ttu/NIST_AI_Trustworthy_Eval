"""Main entry point for rd-agent-mcp."""

import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from rd_agent_mcp.constants import DEFAULT_LM_STUDIO_BASE_URL
from rd_agent_mcp.server import mcp

app = typer.Typer(help="rd-agent-mcp: Research Agent MCP Server")
console = Console()


@app.command()
def serve(
    config: Path = typer.Option(None, help="Path to config file"),
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
):
    """Start the MCP server."""
    # MCP stdio transport uses stdout for JSON-RPC; log to stderr only.
    log = Console(stderr=True)
    log.print(f"[bold green]Starting rd-agent-mcp server...[/bold green]")

    try:
        # FastMCP owns the low-level Server; use its stdio runner (no .mount on FastMCP).
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        log.print("\n[yellow]Server stopped[/yellow]")
    except Exception as e:
        log.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@app.command()
def run_phase(
    phase: str = typer.Argument(..., help="Phase to run (questions, experiment, etc.)"),
    question: str = typer.Option(None, help="Question ID"),
    config: Path = typer.Option(None, help="Config file path"),
):
    """Run a specific research phase."""
    from rd_agent_mcp.phases.questions import QuestionsPhase
    from rd_agent_mcp.phases.experiment import ExperimentPhase
    from rd_agent_mcp.phases.embeddings import EmbeddingsPhase
    from rd_agent_mcp.phases.agent import AgentPhase
    from rd_agent_mcp.phases.results import ResultsPhase

    phases = {
        "questions": QuestionsPhase(),
        "experiment": ExperimentPhase(),
        "embeddings": EmbeddingsPhase(),
        "agent": AgentPhase(),
        "results": ResultsPhase(),
    }

    if phase not in phases:
        console.print(f"[red]Unknown phase:[/red] {phase}")
        console.print(f"Available phases: {', '.join(phases.keys())}")
        sys.exit(1)

    console.print(f"[bold]Running phase:[/bold] {phase}")

    # Create initial state
    state = {
        "messages": [],
        "papers": [],
        "topics": [],
        "homework_pdf": None,
        "questions": [],
        "experiments": [],
        "embeddings": {},
        "prompts": {},
        "agent_results": [],
        "results_json": None,
        "latex_sections": {},
        "schemas": {},
        "current_phase": "start",
        "run_id": "cli-run",
        "errors": [],
    }

    async def run():
        result = await phases[phase].run(state)
        return result

    try:
        result = asyncio.run(run())
        console.print(f"[bold green]Phase completed successfully![/bold green]")
        console.print(f"Current phase: {result.get('current_phase')}")
        console.print(f"Questions: {len(result.get('questions', []))}")
        console.print(f"Experiments: {len(result.get('experiments', []))}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@app.command("research-phase")
def research_phase_cmd(
    topic: str = typer.Option(..., "--topic", "-t", help="Research topic"),
    homework_pdf: Optional[Path] = typer.Option(
        None,
        "--homework-pdf",
        help="Path to homework PDF (optional .txt sidecar supported)",
    ),
    paper: Optional[list[str]] = typer.Option(
        None,
        "--paper",
        help="Paper URL or id (repeatable)",
    ),
):
    """Run the full LangGraph research pipeline (questions through results)."""
    from rd_agent_mcp.graph.research_graph import ResearchGraph

    papers = list(paper) if paper else []
    graph = ResearchGraph()
    initial_state = {
        "messages": [],
        "papers": papers,
        "topics": [topic],
        "homework_pdf": str(homework_pdf.resolve()) if homework_pdf else None,
        "questions": [],
        "experiments": [],
        "embeddings": {},
        "prompts": {},
        "agent_results": [],
        "results_json": None,
        "latex_sections": {},
        "schemas": {},
        "current_phase": "start",
        "run_id": str(uuid.uuid4()),
        "errors": [],
    }

    try:
        result = asyncio.run(graph.run(initial_state))
        console.print("[bold green]Pipeline completed.[/bold green]")
        console.print(f"Questions: {len(result.get('questions', []))}")
        console.print(f"Experiments: {len(result.get('experiments', []))}")
        console.print(f"Agent results: {len(result.get('agent_results', []))}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@app.command()
def validate_tests(
    test_dir: Path = typer.Option(Path("test_cases"), help="Path to test_cases directory"),
    question: str = typer.Option(None, help="Single question id, e.g. q1"),
):
    """Validate test_cases CONFIG and YAML files."""
    from rd_agent_mcp.test_runner import run_validation

    errs = run_validation(test_dir.resolve(), question=question)
    if errs:
        for e in errs:
            console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]OK:[/green] {test_dir}")


@app.command()
def init(
    output_dir: Path = typer.Option(Path.cwd(), help="Output directory"),
):
    """Initialize rd-agent-mcp in a directory."""
    console.print(f"[bold]Initializing rd-agent-mcp in {output_dir}...[/bold]")

    # Create directory structure
    dirs = [
        output_dir / "src",
        output_dir / "test_cases",
        output_dir / "agents",
        output_dir / "output",
        output_dir / "output" / "results",
        output_dir / "output" / "embeddings",
        output_dir / "output" / "diagrams",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Create config file
    config = output_dir / "config.json"
    if not config.exists():
        payload = {
            "chat_model": "ibm/granite-4-h-tiny",
            "embedding_model": "text-embedding-nomic-embed-text-v1.5",
            "base_url": DEFAULT_LM_STUDIO_BASE_URL,
            "chroma_path": "./output/embeddings/chroma_data",
            "sqlite_path": "./output/research.db",
        }
        config.write_text(json.dumps(payload, indent=2) + "\n")
        console.print(f"Created {config}")

    console.print("[bold green]Initialization complete![/bold green]")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
