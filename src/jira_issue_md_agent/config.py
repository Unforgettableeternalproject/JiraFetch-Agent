"""Configuration management for Jira Issue MD Agent."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    jira_base_url: str = Field(
        ...,
        description="Jira base URL (e.g., https://your-domain.atlassian.net)",
    )
    jira_email: str = Field(..., description="Jira user email for authentication")
    jira_api_token: str = Field(..., description="Jira API token for authentication")
    output_dir: Path = Field(default=Path("outputs"), description="Output directory for markdown files")

    def get_jira_auth(self) -> tuple[str, str]:
        """Return authentication tuple for httpx basic auth."""
        return (self.jira_email, self.jira_api_token)


def load_settings(env_file: Optional[Path] = None) -> Settings:
    """Load settings from environment or specified .env file."""
    if env_file:
        return Settings(_env_file=str(env_file))
    return Settings()
