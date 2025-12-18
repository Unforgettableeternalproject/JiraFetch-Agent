"""File writing and management."""

import re
from pathlib import Path

from rich.console import Console

from .models import NormalizedIssue

console = Console()


class MarkdownWriter:
    """Handle writing Markdown files with proper naming and deduplication."""

    def __init__(self, output_dir: Path, overwrite: bool = True):
        """Initialize writer.

        Args:
            output_dir: Base output directory
            overwrite: Whether to overwrite existing files
        """
        self.output_dir = Path(output_dir)
        self.overwrite = overwrite

    def write(self, issue: NormalizedIssue, content: str) -> Path:
        """Write issue markdown to file.

        Args:
            issue: Normalized issue
            content: Rendered markdown content

        Returns:
            Path to written file
        """
        file_path = self._get_file_path(issue)

        # Handle existing files
        if file_path.exists() and not self.overwrite:
            file_path = self._get_versioned_path(file_path)

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        file_path.write_text(content, encoding="utf-8")

        console.print(f"[green]✓[/green] Written: {file_path}")
        return file_path

    def write_batch(self, issues_with_content: list[tuple[NormalizedIssue, str]]) -> list[Path]:
        """Write multiple issues to files.

        Args:
            issues_with_content: List of (issue, content) tuples

        Returns:
            List of written file paths
        """
        written_paths = []
        for issue, content in issues_with_content:
            try:
                path = self.write(issue, content)
                written_paths.append(path)
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to write {issue.key}: {e}")

        return written_paths

    def _get_file_path(self, issue: NormalizedIssue) -> Path:
        """Generate file path for an issue.

        Args:
            issue: Normalized issue

        Returns:
            Path to file
        """
        slug = self._slugify(issue.summary)
        filename = f"{issue.key}-{slug}.md"
        return self.output_dir / issue.project_key / filename

    @staticmethod
    def _slugify(text: str, max_length: int = 50) -> str:
        """Convert text to file-friendly slug.

        Args:
            text: Text to slugify
            max_length: Maximum slug length

        Returns:
            Slugified text (supports Unicode characters including Chinese)
        """
        # Remove leading/trailing whitespace
        slug = text.strip()

        # Replace multiple spaces with single hyphen
        slug = re.sub(r"\s+", "-", slug)

        # Remove characters that are invalid in Windows filenames
        # Invalid: < > : " / \ | ? *
        slug = re.sub(r'[<>:"/\\|?*]', "", slug)

        # Remove control characters
        slug = re.sub(r"[\x00-\x1f\x7f]", "", slug)

        # Remove multiple consecutive hyphens
        slug = re.sub(r"-+", "-", slug)

        # Trim hyphens from ends
        slug = slug.strip("-")

        # Truncate to max length (considering multi-byte characters)
        if len(slug) > max_length:
            # Try to break at hyphen
            truncated = slug[:max_length]
            last_hyphen = truncated.rfind("-")
            if last_hyphen > 0:
                slug = truncated[:last_hyphen]
            else:
                slug = truncated

        return slug or "untitled"

    @staticmethod
    def _get_versioned_path(path: Path) -> Path:
        """Get versioned path for existing file.

        Args:
            path: Original file path

        Returns:
            Versioned file path (e.g., file__v2.md)
        """
        stem = path.stem
        suffix = path.suffix
        parent = path.parent

        version = 2
        while True:
            versioned_path = parent / f"{stem}__v{version}{suffix}"
            if not versioned_path.exists():
                return versioned_path
            version += 1
