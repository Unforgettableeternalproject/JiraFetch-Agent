# Jira Issue Markdown Agent

A Python CLI tool that fetches Jira issues and converts them into development-ready Markdown files with structured checklists for tracking implementation progress.

## Features

- 🎯 **Single & Batch Fetching**: Fetch individual issues by key or multiple issues using JQL queries
- 🔄 **Data Normalization**: Consistent data structure across different Jira configurations
- 📝 **Template-based Output**: Jinja2 templates for customizable Markdown generation
- ✅ **Development-ready Format**: Includes goals, acceptance criteria, impact analysis, test plans, and deliverables
- 📂 **Organized Structure**: Automatic project-based folder organization
- 🎨 **Rich CLI**: Beautiful terminal output with progress indicators

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (recommended) or pip

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd JiraFetch-Agent

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Using pip

```bash
# Clone the repository
git clone <repository-url>
cd JiraFetch-Agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .
```

## Configuration

Create a `.env` file in the project root:

```env
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token-here
OUTPUT_DIR=outputs
```

### Getting Your Jira API Token

1. Log in to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label (e.g., "Jira MD Agent")
4. Copy the token to your `.env` file

## Usage

### Fetch Single Issue

```bash
jira-md fetch --key UEP-123
```

### Fetch Multiple Issues with JQL

```bash
# Fetch all open issues assigned to you
jira-md fetch --jql "project = UEP AND assignee = currentUser() AND status != Done"

# Fetch issues from a specific sprint
jira-md fetch --jql "sprint = 42"

# Fetch by status
jira-md fetch --jql "project = UEP AND status = 'In Progress'"
```

### Custom Output Directory

```bash
jira-md fetch --key UEP-123 --out ./my-issues
```

### Prevent Overwriting Existing Files

```bash
jira-md fetch --jql "sprint = 42" --no-overwrite
```

This will create versioned files (e.g., `UEP-123-fix-login__v2.md`) instead of overwriting.

### Using Custom Environment File

```bash
jira-md fetch --key UEP-123 --env /path/to/.env
```

## Output Structure

Generated files are organized by project:

```
outputs/
├── UEP/
│   ├── UEP-123-implement-user-auth.md
│   ├── UEP-124-fix-login-bug.md
│   └── UEP-125-add-password-reset.md
└── JSAI/
    └── JSAI-456-api-integration.md
```

## Markdown Template

Each generated file includes:

- **Header**: Issue metadata (key, project, status, priority, assignee, etc.)
- **背景與需求** (Background & Requirements): Original Jira description
- **目標** (Goals): High-level objectives checklist
- **驗收條件** (Acceptance Criteria): Acceptance criteria checklist
- **影響範圍** (Impact): Frontend/Backend/Database/Infra impact checklist
- **實作筆記** (Dev Notes): Implementation notes section
- **測試計畫** (Test Plan): Testing strategy and checklist
- **交付物** (Deliverables): PR, release notes, documentation checklist
- **參考連結** (Links): Related issues and resources

## Development

### Project Structure

```
src/jira_issue_md_agent/
├── __init__.py           # Package initialization
├── cli.py                # CLI interface (Typer)
├── config.py             # Configuration management
├── models.py             # Pydantic data models
├── jira_client.py        # Jira REST API client
├── issue_fetcher.py      # Issue fetching orchestration
├── normalizer.py         # Data normalization
├── renderer.py           # Template rendering
├── writer.py             # File writing and management
└── templates/
    └── issue.md.j2       # Jinja2 Markdown template
```

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
# Format with Black
poetry run black src/

# Lint with Ruff
poetry run ruff check src/
```

## Troubleshooting

### Authentication Errors

- Verify your `JIRA_EMAIL` and `JIRA_API_TOKEN` are correct
- Ensure the API token has proper permissions
- Check that your Jira base URL is correct (no trailing slash)

### JQL Syntax Errors

- Test your JQL in Jira's issue navigator first
- Common operators: `=`, `!=`, `IN`, `AND`, `OR`
- Use quotes for strings with spaces: `status = "In Progress"`
- Use `currentUser()` for current user: `assignee = currentUser()`

### No Issues Found

- Verify the JQL query returns results in Jira UI
- Check that you have permission to view the issues
- Ensure project key is correct

## License

MIT License

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
