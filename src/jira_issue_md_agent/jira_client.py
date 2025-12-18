"""Jira REST API client with abstraction for API changes."""

from typing import Any, Optional

import httpx
from rich.console import Console

from .config import Settings

console = Console()


class JiraClient:
    """Abstract Jira API client to isolate API interactions."""

    def __init__(self, settings: Settings, timeout: float = 30.0):
        """Initialize Jira client with settings.

        Args:
            settings: Application settings with Jira credentials
            timeout: Request timeout in seconds
        """
        self.base_url = settings.jira_base_url.rstrip("/")
        self.auth = settings.get_jira_auth()
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    def __enter__(self):
        """Context manager entry."""
        self._client = httpx.Client(
            auth=self.auth,
            timeout=self.timeout,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._client:
            self._client.close()

    def get_issue(self, issue_key: str, fields: Optional[list[str]] = None) -> dict[str, Any]:
        """Fetch a single issue by key.

        Args:
            issue_key: Issue key (e.g., UEP-123)
            fields: Optional list of fields to retrieve

        Returns:
            Issue data as dictionary

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use context manager.")

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        params = {}
        if fields:
            params["fields"] = ",".join(fields)

        console.print(f"[cyan]Fetching issue:[/cyan] {issue_key}")
        response = self._client.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def search_issues(
        self,
        jql: str,
        fields: Optional[list[str]] = None,
        max_results: int = 50,
        start_at: int = 0,
    ) -> dict[str, Any]:
        """Search issues using JQL.

        Args:
            jql: JQL query string
            fields: Optional list of fields to retrieve
            max_results: Maximum results per page
            start_at: Starting index for pagination

        Returns:
            Search response with issues

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use context manager.")

        # Use POST request with REST API v3 /search/jql endpoint
        url = f"{self.base_url}/rest/api/3/search/jql"
        payload: dict[str, Any] = {
            "jql": jql,
            "maxResults": max_results,
        }
        
        # Only add startAt if not 0
        if start_at > 0:
            payload["startAt"] = start_at
        
        # Add fields if specified (as array)
        if fields:
            payload["fields"] = fields
        
        console.print(f"[cyan]Searching with JQL:[/cyan] {jql}")
        try:
            response = self._client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Print detailed error for debugging
            console.print(f"[red]Error:[/red] {e}")
            if e.response.text:
                console.print(f"[yellow]Response body:[/yellow] {e.response.text}")
            raise

    def search_all_issues(
        self,
        jql: str,
        fields: Optional[list[str]] = None,
        batch_size: int = 50,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Search all issues matching JQL with automatic pagination.

        Args:
            jql: JQL query string
            fields: Optional list of fields to retrieve
            batch_size: Results per batch
            limit: Maximum number of issues to fetch (None = all)

        Returns:
            List of all matching issues (up to limit)

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        all_issues = []
        start_at = 0

        while True:
            # If limit is set, don't fetch more than needed
            current_batch_size = batch_size
            if limit:
                remaining = limit - len(all_issues)
                if remaining <= 0:
                    break
                current_batch_size = min(batch_size, remaining)
            
            response = self.search_issues(jql, fields, current_batch_size, start_at)
            issues = response.get("issues", [])
            
            # Break if no more issues returned
            if not issues:
                break
                
            all_issues.extend(issues)

            total = response.get("total", len(issues))  # Fallback to current count if total not provided
            fetched = len(all_issues)

            console.print(f"[green]Fetched {fetched} issues (limit: {limit or 'none'})[/green]")

            # Stop if reached the limit
            if limit and fetched >= limit:
                break

            # Note: This API endpoint may not support pagination with startAt
            # If you need more than 50 results, increase maxResults parameter
            break

        return all_issues

    @staticmethod
    def get_default_fields() -> list[str]:
        """Get default fields to fetch from Jira API.

        Returns:
            List of field names
        """
        return [
            "summary",
            "description",
            "status",
            "priority",
            "assignee",
            "reporter",
            "labels",
            "components",
            "fixVersions",
            "created",
            "updated",
            "issuetype",
            "parent",
            "subtasks",
            "issuelinks",
            "project",
        ]
