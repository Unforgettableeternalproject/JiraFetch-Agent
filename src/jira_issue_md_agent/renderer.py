"""Markdown template rendering."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

from .models import NormalizedIssue


class MarkdownRenderer:
    """Render normalized issues to Markdown using Jinja2 templates."""

    def __init__(self, template_dir: Path):
        """Initialize renderer with template directory.

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, issue: NormalizedIssue, template_name: str = "issue.md.j2") -> str:
        """Render an issue to Markdown.

        Args:
            issue: Normalized issue to render
            template_name: Template file name

        Returns:
            Rendered Markdown content
        """
        template = self.env.get_template(template_name)
        return template.render(issue=issue)

    @classmethod
    def from_package(cls) -> "MarkdownRenderer":
        """Create renderer using packaged templates.

        Returns:
            MarkdownRenderer instance
        """
        # Get template directory relative to this module
        template_dir = Path(__file__).parent / "templates"
        return cls(template_dir)
