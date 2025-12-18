"""Issue fetching orchestration."""

from typing import Optional

from rich.console import Console

from .config import Settings
from .jira_client import JiraClient
from .models import NormalizedIssue
from .normalizer import IssueNormalizer

console = Console()


class IssueFetcher:
    """Orchestrate fetching and normalizing Jira issues."""

    def __init__(self, settings: Settings):
        """Initialize issue fetcher.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.normalizer = IssueNormalizer()

    def fetch_single(self, issue_key: str) -> NormalizedIssue:
        """Fetch and normalize a single issue.

        Args:
            issue_key: Issue key (e.g., UEP-123)

        Returns:
            Normalized issue

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        with JiraClient(self.settings) as client:
            fields = client.get_default_fields()
            issue_data = client.get_issue(issue_key, fields)
            normalized = self.normalizer.normalize(issue_data, self.settings.jira_base_url)

            console.print(f"[green]✓[/green] Fetched: {normalized.key} - {normalized.summary}")
            return normalized

    def fetch_batch(
        self,
        jql: str,
        limit: Optional[int] = None,
        batch_size: int = 50,
    ) -> list[NormalizedIssue]:
        """Fetch and normalize multiple issues using JQL.

        Args:
            jql: JQL query string
            limit: Maximum number of issues to fetch (None = all)
            batch_size: Number of issues to fetch per API call

        Returns:
            List of normalized issues

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        with JiraClient(self.settings) as client:
            fields = client.get_default_fields()
            
            # If limit is specified and smaller than batch_size, adjust batch_size
            if limit and limit < batch_size:
                batch_size = limit
            
            issues_data = client.search_all_issues(jql, fields, batch_size, limit)

            normalized_issues = []
            for issue_data in issues_data:
                try:
                    normalized = self.normalizer.normalize(
                        issue_data, self.settings.jira_base_url
                    )
                    normalized_issues.append(normalized)
                    console.print(
                        f"[green]✓[/green] Normalized: {normalized.key} - {normalized.summary}"
                    )
                except Exception as e:
                    key = issue_data.get("key", "UNKNOWN")
                    console.print(f"[yellow]⚠[/yellow] Failed to normalize {key}: {e}")

            console.print(f"\n[bold green]Total issues fetched: {len(normalized_issues)}[/bold green]")
            return normalized_issues
