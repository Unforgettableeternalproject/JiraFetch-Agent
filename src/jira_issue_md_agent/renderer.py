"""Markdown template rendering."""

from importlib.resources import files
from jinja2 import Environment, BaseLoader, TemplateNotFound

from .models import NormalizedIssue


class PackageLoader(BaseLoader):
    """Load templates from package resources using importlib.resources."""
    
    def __init__(self, package_name: str, package_path: str = "templates"):
        self.package_name = package_name
        self.package_path = package_path
    
    def get_source(self, environment, template):
        """Get template source from package resources."""
        try:
            # Use importlib.resources to access package data
            template_files = files(self.package_name).joinpath(self.package_path)
            template_file = template_files.joinpath(template)
            
            # Read template content
            source = template_file.read_text(encoding='utf-8')
            
            # Return (source, filename, uptodate_function)
            # uptodate_function returns False to always reload (safe for packaged apps)
            return source, None, lambda: False
            
        except (FileNotFoundError, AttributeError) as e:
            raise TemplateNotFound(template) from e


class MarkdownRenderer:
    """Render normalized issues to Markdown using Jinja2 templates."""

    def __init__(self):
        """Initialize renderer with package template loader."""
        self.env = Environment(
            loader=PackageLoader("jira_issue_md_agent", "templates"),
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
