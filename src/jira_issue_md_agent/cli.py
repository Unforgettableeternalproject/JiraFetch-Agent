"""Command-line interface for Jira Issue MD Agent."""

import re
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

def _parse_issue_file(file_path: Path) -> list[str]:
    """Parse issue keys from a file.
    
    Supports formats:
    - Plain list: one issue key per line
    - Markdown list: - ISSUE-123
    - Mixed with other text
    
    Args:
        file_path: Path to the file
        
    Returns:
        List of issue keys found
    """
    content = file_path.read_text(encoding="utf-8")
    
    # Pattern to match issue keys like JSAI-123, UEP-456, etc.
    # Matches: PROJECT-NUMBER format
    pattern = r'\b([A-Z][A-Z0-9]+-\d+)\b'
    
    matches = re.findall(pattern, content)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keys = []
    for key in matches:
        if key not in seen:
            seen.add(key)
            unique_keys.append(key)
    
    return unique_keys



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
    file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        help="Read issue keys from a file (one per line or markdown list)",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of issues to fetch for JQL queries (default: 10)",
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

        # Fetch issues from a file
        jira-md fetch --file docs/issues.md

        # Custom output directory
        jira-md fetch --key UEP-123 --out ./my-outputs

        # Don't overwrite existing files
        jira-md fetch --jql "sprint = 42" --no-overwrite
    """
    # Validate input
    if not key and not jql and not file:
        console.print("[red]Error:[/red] Must specify one of: --key, --jql, or --file")
        raise typer.Exit(1)

    # Check for conflicting options
    options_count = sum([bool(key), bool(jql), bool(file)])
    if options_count > 1:
        console.print("[red]Error:[/red] Can only specify one of --key, --jql, or --file")
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
        renderer = MarkdownRenderer()
        writer = MarkdownWriter(settings.output_dir, overwrite=not no_overwrite)

        # Fetch issues
        console.print("\n" + "=" * 60)
        
        if key:
            console.print(Panel(f"Fetching single issue: [bold]{key}[/bold]", expand=False))
            issue = fetcher.fetch_single(key)
            content = renderer.render(issue)
            writer.write(issue, content)

        elif file:
            # Read issue keys from file
            console.print(Panel(f"Reading issue keys from: [bold]{file}[/bold]", expand=False))
            try:
                issue_keys = _parse_issue_file(file)
                if not issue_keys:
                    console.print("[yellow]No issue keys found in file[/yellow]")
                    raise typer.Exit(0)
                
                console.print(f"[cyan]Found {len(issue_keys)} issue key(s)[/cyan]")
                
                # Fetch all issues
                issues = []
                for idx, issue_key in enumerate(issue_keys, 1):
                    try:
                        console.print(f"\n[cyan]Fetching {idx}/{len(issue_keys)}:[/cyan] {issue_key}")
                        issue = fetcher.fetch_single(issue_key)
                        issues.append(issue)
                    except Exception as e:
                        console.print(f"[red]✗[/red] Failed to fetch {issue_key}: {e}")
                
                if not issues:
                    console.print("[yellow]No issues were successfully fetched[/yellow]")
                    raise typer.Exit(1)
                
                # Render and write all issues
                console.print(f"\n[cyan]Rendering {len(issues)} issue(s)...[/cyan]")
                issues_with_content = [(issue, renderer.render(issue)) for issue in issues]
                written_paths = writer.write_batch(issues_with_content)
                
                console.print(f"\n[bold green]✓ Successfully written {len(written_paths)} file(s)[/bold green]")
                
            except FileNotFoundError:
                console.print(f"[red]Error:[/red] File not found: {file}")
                raise typer.Exit(1)
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to read file: {e}")
                raise typer.Exit(1)

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
