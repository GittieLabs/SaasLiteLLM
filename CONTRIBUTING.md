# Contributing to SaaS LiteLLM

Thank you for your interest in contributing to SaaS LiteLLM! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/SaasLiteLLM.git
   cd SaasLiteLLM
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/GittieLabs/SaasLiteLLM.git
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- PostgreSQL 15+ (via Docker)
- Redis 7+ (via Docker)

### Local Development Environment

1. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install uv
   uv pip install -e ".[dev]"
   ```

3. **Set up environment variables**:
   ```bash
   chmod +x setup_env.sh
   ./setup_env.sh
   ```

4. **Start Docker services**:
   ```bash
   ./scripts/docker_setup.sh
   ```

5. **Run database migrations**:
   ```bash
   ./scripts/run_migrations.sh
   ```

6. **Start the development servers**:
   ```bash
   # Terminal 1: LiteLLM backend
   python scripts/start_local.py

   # Terminal 2: SaaS API wrapper
   python scripts/start_saas_api.py
   ```

7. **Verify the setup**:
   - SaaS API: http://localhost:8003/docs
   - LiteLLM Backend: http://localhost:8002/ui

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug fixes**: Fix issues identified in the issue tracker
- **New features**: Add new functionality to the project
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Performance improvements**: Optimize existing code
- **Code refactoring**: Improve code quality and maintainability

### Before You Start

1. **Check existing issues**: Look for existing issues or create a new one to discuss your proposed changes
2. **Discuss major changes**: For significant changes, open an issue first to discuss your approach
3. **Keep changes focused**: Each PR should address a single concern

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: Maximum 100 characters
- **Imports**: Group imports in the following order:
  1. Standard library imports
  2. Related third-party imports
  3. Local application imports
- **Type hints**: Use type hints for function parameters and return values
- **Docstrings**: Use Google-style docstrings

### Code Formatting

We use automated tools to maintain code quality:

```bash
# Format code with Black
black src/ tests/

# Check code style with Ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/

# Sort imports
isort src/ tests/
```

### Naming Conventions

- **Functions and variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_CASE`
- **Private methods**: `_leading_underscore`

### Example Code

```python
from typing import Optional
from datetime import datetime


class JobTracker:
    """Tracks LLM jobs and their associated costs.

    Attributes:
        team_id: The unique identifier for the team.
        job_type: The type of job being tracked.
    """

    def __init__(self, team_id: str, job_type: str) -> None:
        self.team_id = team_id
        self.job_type = job_type

    def create_job(
        self,
        user_id: str,
        metadata: Optional[dict] = None
    ) -> dict:
        """Create a new job for tracking.

        Args:
            user_id: The user creating the job.
            metadata: Optional metadata for the job.

        Returns:
            A dictionary containing the job details.
        """
        # Implementation here
        pass
```

## Testing Requirements

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_job_tracking.py

# Run with verbose output
pytest -v
```

### Test Structure

- Place tests in the `tests/` directory
- Mirror the source code structure
- Use descriptive test names: `test_<function>_<scenario>_<expected_result>`

### Writing Tests

```python
import pytest
from src.models.job_tracking import JobTracker


def test_create_job_success():
    """Test successful job creation."""
    tracker = JobTracker(team_id="test-team", job_type="analysis")
    result = tracker.create_job(user_id="user@example.com")

    assert result["status"] == "created"
    assert result["team_id"] == "test-team"


def test_create_job_invalid_team_id():
    """Test job creation with invalid team ID."""
    with pytest.raises(ValueError):
        tracker = JobTracker(team_id="", job_type="analysis")
```

### Test Coverage

- Aim for at least 80% code coverage
- All new features must include tests
- Bug fixes should include regression tests

## Pull Request Process

### 1. Create a Branch

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Write clean, maintainable code
- Follow the coding standards
- Add or update tests
- Update documentation as needed

### 3. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add job cost aggregation endpoint

- Implement new endpoint for aggregating job costs
- Add unit tests for cost calculation
- Update API documentation"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

### 4. Run Tests and Checks

Before pushing, ensure all checks pass:

```bash
# Format code
black src/ tests/
isort src/ tests/

# Run linters
ruff check src/ tests/

# Run tests
pytest

# Type checking
mypy src/
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name
```

Then create a pull request on GitHub:
- Fill out the PR template completely
- Link any related issues
- Request reviews from maintainers

### 6. Address Review Comments

- Be responsive to feedback
- Make requested changes promptly
- Push additional commits to your branch
- Re-request review when ready

### PR Checklist

Before submitting, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear and descriptive
- [ ] PR description explains the changes
- [ ] No merge conflicts with main branch

## Issue Reporting

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check documentation** for solutions
3. **Verify the issue** in the latest version

### Creating a Bug Report

Use the bug report template and include:

- Clear description of the bug
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or screenshots

### Requesting Features

Use the feature request template and include:

- Clear description of the feature
- Use case and benefits
- Proposed implementation (if applicable)
- Alternative solutions considered

## Documentation

### Updating Documentation

- Documentation is in the `docs/` directory
- Use Markdown format
- Include code examples where appropriate
- Keep language clear and concise

### Building Documentation

```bash
# Install documentation dependencies
pip install -r requirements-docs.txt

# Build documentation locally
mkdocs serve

# View at http://localhost:8000
```

## Community

### Getting Help

- Check the [documentation](https://gittielabs.github.io/SaasLiteLLM/)
- Search existing [issues](https://github.com/GittieLabs/SaasLiteLLM/issues)
- Create a new issue for bugs or questions

### Communication

- Be respectful and professional
- Provide context and details
- Be patient - maintainers are volunteers
- Help others when you can

## Recognition

Contributors who make significant contributions will be recognized in:

- Release notes
- CONTRIBUTORS.md file
- Project documentation

Thank you for contributing to SaaS LiteLLM!
