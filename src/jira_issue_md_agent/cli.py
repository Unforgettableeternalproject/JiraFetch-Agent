"""Command-line interface for Jira Issue MD Agent."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .config import Settings, load_settings
from .issue_fetcher import IssueFetcher
from .renderer import MarkdownRenderer
from .writer import MarkdownWriter

app = typer.Typer(
    name="jira-md",
    help="Fetch Jira issues and convert to development-ready Markdown files",
    add_completion=False,
)
console = Console()


@app.callback()
def main():
    """Jira Issue Markdown Agent - Fetch and convert Jira issues to Markdown."""
    pass


@app.command("version")
def show_version():
    """Show version information."""
    console.print(f"jira-issue-md-agent version {__version__}")
    raise typer.Exit()


@app.command()
def fetch(
    key: Optional[str] = typer.Option(
        None,
        "--key",
        "-k",
        help="Fetch single issue by key (e.g., UEP-123)",
    ),
    jql: Optional[str] = typer.Option(
        None,
        "--jql",
        "-q",
        help='Fetch multiple issues using JQL (e.g., "project = UEP AND status = Open")',
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of issues to fetch (default: 10)",
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        "-o",
        help="Output directory (default: from .env or 'outputs')",
    ),
    no_overwrite: bool = typer.Option(
        False,
        "--no-overwrite",
        help="Don't overwrite existing files (create versioned files instead)",
    ),
    env_file: Optional[Path] = typer.Option(
        None,
        "--env",
        "-e",
        help="Path to .env file (default: .env in current directory)",
    ),
):
    """Fetch Jira issue(s) and generate Markdown files.

    Examples:

        # Fetch single issue
        jira-md fetch --key UEP-123

        # Fetch multiple issues with JQL
        jira-md fetch --jql "project = UEP AND assignee = currentUser()"

        # Custom output directory
        jira-md fetch --key UEP-123 --out ./my-outputs

        # Don't overwrite existing files
        jira-md fetch --jql "sprint = 42" --no-overwrite
    """
    # Validate input
    if not key and not jql:
        console.print("[red]Error:[/red] Either --key or --jql must be specified")
        raise typer.Exit(1)

    if key and jql:
        console.print("[red]Error:[/red] Cannot specify both --key and --jql")
        raise typer.Exit(1)

    try:
        # Load settings
        console.print("[cyan]Loading configuration...[/cyan]")
        settings = load_settings(env_file)

        # Override output directory if specified
        if out:
            settings.output_dir = out

        # Initialize components
        fetcher = IssueFetcher(settings)
        renderer = MarkdownRenderer.from_package()
        writer = MarkdownWriter(settings.output_dir, overwrite=not no_overwrite)

        # Fetch issues
        console.print("\n" + "=" * 60)
        if key:
            console.print(Panel(f"Fetching single issue: [bold]{key}[/bold]", expand=False))
            issue = fetcher.fetch_single(key, limit=limit)
            content = renderer.render(issue)
            writer.write(issue, content)

        elif jql:
            console.print(Panel(f"Fetching issues with JQL:\n[bold]{jql}[/bold]", expand=False))
            issues = fetcher.fetch_batch(jql, limit=limit)

            if not issues:
                console.print("[yellow]No issues found matching the JQL query[/yellow]")
                raise typer.Exit(0)

            # Render and write all issues
            console.print(f"\n[cyan]Rendering {len(issues)} issue(s)...[/cyan]")
            issues_with_content = [(issue, renderer.render(issue)) for issue in issues]
            written_paths = writer.write_batch(issues_with_content)

            console.print(f"\n[bold green]✓ Successfully written {len(written_paths)} file(s)[/bold green]")

        console.print("=" * 60)
        console.print(f"\n[bold green]Done![/bold green] Output directory: {settings.output_dir}")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] Configuration file not found: {e}")
        console.print("\n[yellow]Tip:[/yellow] Create a .env file with your Jira credentials")
        console.print("Example:\n")
        console.print("  JIRA_BASE_URL=https://your-domain.atlassian.net")
        console.print("  JIRA_EMAIL=your-email@example.com")
        console.print("  JIRA_API_TOKEN=your-token-here")
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
