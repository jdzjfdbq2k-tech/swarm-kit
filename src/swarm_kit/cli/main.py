import os
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="The official CLI for Swarm Agent Kit.", no_args_is_help=True)
console = Console()

TEMPLATE = '''from swarm_kit import Agent, Swarm


def get_time(city: str) -> str:
    """Return the current local time for a city."""
    from datetime import datetime

    return f"It is {datetime.now():%H:%M} in {city}."


# Define your agents here
researcher = Agent(
    name="Researcher",
    instructions="You research things. Use your tools when helpful.",
    tools=[get_time],
)

# Run them
if __name__ == "__main__":
    swarm = Swarm(agents=[researcher])
    result = swarm.execute("Researcher", "Hello world! What time is it in Lagos?")
    print(result.final_output)
'''

ENV_TEMPLATE = '''# Swarm Kit uses LiteLLM, so any provider key works here.
OPENAI_API_KEY=""
'''


@app.command()
def init(
    directory: Path = typer.Argument(Path("."), help="Where to create the project."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files."),
):
    """Initialize a new multi-agent project."""
    console.print("[bold blue]🚀 Initializing new agent project...[/bold blue]")

    agents_dir = directory / "agents"
    main_file = agents_dir / "main.py"
    if main_file.exists() and not force:
        console.print(f"[yellow]{main_file} already exists. Use --force to overwrite.[/yellow]")
        raise typer.Exit(code=1)

    agents_dir.mkdir(parents=True, exist_ok=True)
    main_file.write_text(TEMPLATE, encoding="utf-8")

    env_example = directory / ".env.example"
    if not env_example.exists():
        env_example.write_text(ENV_TEMPLATE, encoding="utf-8")

    console.print(f"[bold green]✔ Done! Created {main_file}[/bold green]")
    console.print("Copy [cyan].env.example[/cyan] to [cyan].env[/cyan], add your key, then run "
                  f"[cyan]python {main_file}[/cyan].")


@app.command()
def studio(
    port: int = typer.Option(8000, help="Port to serve the dashboard on."),
    host: str = typer.Option("127.0.0.1", help="Interface to bind to."),
    log_file: Path = typer.Option(Path(".swarm_runs.jsonl"), help="Swarm log file to visualize."),
):
    """Launch the Agent Studio (UI) to view logs."""
    import uvicorn

    os.environ["SWARM_KIT_LOG_FILE"] = str(log_file)
    console.print(f"[bold green]🚀 Launching Agent Studio on http://{host}:{port}[/bold green]")
    console.print(f"[dim]Watching {log_file.resolve()} — press Ctrl+C to stop the server[/dim]")

    uvicorn.run("swarm_kit.ui.server:app", host=host, port=port, log_level="warning")


@app.command()
def version():
    """Show the installed Swarm Kit version."""
    from swarm_kit import __version__

    console.print(f"swarm-agent-kit {__version__}")


def run():
    app()


if __name__ == "__main__":
    run()
