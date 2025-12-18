"""Data models for Jira issues and normalized output."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


class NormalizedIssue(BaseModel):
    """Normalized issue data structure for consistent markdown generation."""

    key: str = Field(..., description="Issue key (e.g., UEP-123)")
    url: str = Field(..., description="Direct link to Jira issue")
    project_key: str = Field(..., description="Project code")
    type: str = Field(..., description="Issue type (Story, Bug, Task, etc.)")
    summary: str = Field(..., description="Issue title/summary")
    status: str = Field(..., description="Current status")
    priority: str = Field(default="None", description="Priority level")
    assignee: str = Field(default="Unassigned", description="Assigned person")
    reporter: str = Field(default="Unknown", description="Reporter")
    labels: list[str] = Field(default_factory=list, description="Labels list")
    components: list[str] = Field(default_factory=list, description="Components list")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    description_text: str = Field(default="", description="Description (plain text)")
    acceptance_criteria: str = Field(default="", description="Acceptance criteria (if extractable)")
    dev_notes: str = Field(default="", description="Developer notes")
    links: list[str] = Field(default_factory=list, description="Related issues/PRs")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "key": "UEP-123",
                "url": "https://example.atlassian.net/browse/UEP-123",
                "project_key": "UEP",
                "type": "Story",
                "summary": "Implement user authentication",
                "status": "In Progress",
                "priority": "High",
                "assignee": "john.doe@example.com",
                "reporter": "jane.smith@example.com",
                "labels": ["auth", "security"],
                "components": ["Backend", "API"],
                "created_at": "2025-12-01 10:00:00",
                "updated_at": "2025-12-18 14:30:00",
                "description_text": "As a user, I want to log in securely...",
                "acceptance_criteria": "",
                "dev_notes": "",
                "links": [],
            }
        }


class JiraIssueResponse(BaseModel):
    """Raw Jira API issue response structure (simplified)."""

    key: str
    fields: dict[str, Any]
    self: str  # URL to the issue

    class Config:
        """Pydantic model configuration."""

        extra = "allow"


class JiraSearchResponse(BaseModel):
    """Jira API search response structure."""

    startAt: int
    maxResults: int
    total: int
    issues: list[dict[str, Any]]

    class Config:
        """Pydantic model configuration."""

        extra = "allow"
