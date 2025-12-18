"""Normalize Jira API responses into consistent data structures."""

from datetime import datetime
from typing import Any

from .models import NormalizedIssue


class IssueNormalizer:
    """Convert Jira API responses to NormalizedIssue format."""

    @staticmethod
    def normalize(issue_data: dict[str, Any], base_url: str) -> NormalizedIssue:
        """Normalize a Jira issue response.

        Args:
            issue_data: Raw issue data from Jira API
            base_url: Jira base URL for constructing issue links

        Returns:
            Normalized issue object
        """
        key = issue_data.get("key", "UNKNOWN")
        fields = issue_data.get("fields", {})

        # Extract basic fields
        summary = fields.get("summary", "No Summary")
        project = fields.get("project", {})
        project_key = project.get("key", key.split("-")[0] if "-" in key else "UNKNOWN")

        # Issue type
        issuetype = fields.get("issuetype", {})
        issue_type = issuetype.get("name", "Task")

        # Status
        status_obj = fields.get("status", {})
        status = status_obj.get("name", "Unknown")

        # Priority
        priority_obj = fields.get("priority", {})
        priority = priority_obj.get("name", "None") if priority_obj else "None"

        # Assignee
        assignee_obj = fields.get("assignee")
        assignee = (
            assignee_obj.get("displayName", assignee_obj.get("emailAddress", "Unassigned"))
            if assignee_obj
            else "Unassigned"
        )

        # Reporter
        reporter_obj = fields.get("reporter")
        reporter = (
            reporter_obj.get("displayName", reporter_obj.get("emailAddress", "Unknown"))
            if reporter_obj
            else "Unknown"
        )

        # Labels
        labels = fields.get("labels", [])

        # Components
        components_list = fields.get("components", [])
        components = [comp.get("name", "") for comp in components_list if comp.get("name")]

        # Timestamps
        created = fields.get("created", "")
        updated = fields.get("updated", "")
        created_at = IssueNormalizer._format_datetime(created)
        updated_at = IssueNormalizer._format_datetime(updated)

        # Description (handle Atlassian Document Format)
        description_raw = fields.get("description")
        description_text = IssueNormalizer._extract_description_text(description_raw)

        # Issue links
        issue_links = fields.get("issuelinks", [])
        links = IssueNormalizer._extract_links(issue_links, base_url)

        # Construct URL
        url = f"{base_url.rstrip('/')}/browse/{key}"

        return NormalizedIssue(
            key=key,
            url=url,
            project_key=project_key,
            type=issue_type,
            summary=summary,
            status=status,
            priority=priority,
            assignee=assignee,
            reporter=reporter,
            labels=labels,
            components=components,
            created_at=created_at,
            updated_at=updated_at,
            description_text=description_text,
            acceptance_criteria="",  # TODO: Extract from description if pattern found
            dev_notes="",
            links=links,
        )

    @staticmethod
    def _format_datetime(dt_string: str) -> str:
        """Format ISO datetime string to readable format.

        Args:
            dt_string: ISO format datetime string

        Returns:
            Formatted datetime string
        """
        if not dt_string:
            return "Unknown"

        try:
            dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            return dt_string

    @staticmethod
    def _extract_description_text(description: Any) -> str:
        """Extract plain text from Jira description (handles Atlassian Document Format).

        Args:
            description: Description field from Jira (can be dict, str, or None)

        Returns:
            Plain text description
        """
        if not description:
            return ""

        # If it's already a string, return it
        if isinstance(description, str):
            return description

        # Handle Atlassian Document Format (ADF)
        if isinstance(description, dict):
            return IssueNormalizer._parse_adf(description)

        return str(description)

    @staticmethod
    def _parse_adf(adf_doc: dict[str, Any]) -> str:
        """Parse Atlassian Document Format to plain text.

        Args:
            adf_doc: ADF document structure

        Returns:
            Plain text extracted from ADF
        """
        text_parts = []

        def extract_text(node: dict[str, Any]) -> None:
            """Recursively extract text from ADF nodes."""
            node_type = node.get("type", "")

            # Handle text nodes
            if node_type == "text":
                text_parts.append(node.get("text", ""))

            # Handle nodes with content
            content = node.get("content", [])
            for child in content:
                if isinstance(child, dict):
                    extract_text(child)

            # Add line breaks for paragraphs
            if node_type == "paragraph" and text_parts and text_parts[-1] != "\n":
                text_parts.append("\n")

        extract_text(adf_doc)
        return "".join(text_parts).strip()

    @staticmethod
    def _extract_links(issue_links: list[dict[str, Any]], base_url: str) -> list[str]:
        """Extract related issue links.

        Args:
            issue_links: List of issue link objects from Jira
            base_url: Jira base URL

        Returns:
            List of formatted links
        """
        links = []
        for link in issue_links:
            # Handle inward and outward links
            inward_issue = link.get("inwardIssue")
            outward_issue = link.get("outwardIssue")

            if inward_issue:
                key = inward_issue.get("key")
                if key:
                    links.append(f"{base_url.rstrip('/')}/browse/{key}")

            if outward_issue:
                key = outward_issue.get("key")
                if key:
                    links.append(f"{base_url.rstrip('/')}/browse/{key}")

        return links
