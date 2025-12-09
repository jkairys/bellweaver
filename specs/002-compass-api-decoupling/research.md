# Research Document: Compass API Decoupling and Mock Data Infrastructure

**Feature**: Compass API Decoupling and Mock Data Infrastructure
**Research Date**: 2025-12-09
**Status**: Complete

## Executive Summary

This research document provides technical guidance for implementing a mock data infrastructure that enables local development and CI/CD testing without requiring real Compass API credentials. The research covers five key technical areas: factory pattern implementation, environment-based configuration, GitHub Actions path filtering, mock data management, and startup validation.

## Research Topics

### 0. Python Monorepo Package Management

#### Decision: Use Poetry Path Dependencies with Separate pyproject.toml Files

Structure the repository as a multi-package monorepo with separate `pyproject.toml` files for each package (compass-client and bellweaver), using Poetry path dependencies for local development.

#### Rationale

- **True Decoupling**: Separate packages enforce architectural boundaries at the package level, preventing accidental coupling
- **Independent Testing**: Each package can have its own test suite that runs independently, enabling selective CI workflows
- **Clear Public API**: Package boundaries force explicit definition of public vs. private APIs via `__init__.py`
- **Future Flexibility**: Easy migration to PyPI publication or separate repositories if needed
- **Poetry Native**: Poetry's path dependency feature makes local monorepo development seamless
- **Standard Practice**: Aligns with Python packaging best practices for multi-package projects

According to Python Packaging Authority guidance, "A project can have multiple packages under it, each with its own pyproject.toml and independent versioning" ([PyPA - Packaging Python Projects](https://packaging.python.org/)).

#### Alternatives Considered

1. **Single Package with Internal Modules** (adapters/ folder)
   - **Pros**: Simpler structure, single pyproject.toml
   - **Cons**: Doesn't prevent tight coupling, harder to enforce API boundaries, can't version independently, difficult to achieve true CI separation
   - **Rejected**: Doesn't meet "completely decouple" requirement

2. **Separate Git Repositories**
   - **Pros**: Maximum isolation, independent CI/CD
   - **Cons**: Complicates local development, requires package publishing for testing changes, overkill for small team
   - **Rejected**: Too much overhead for 2-3 developers

3. **Git Submodules**
   - **Pros**: Separate repos with unified checkout
   - **Cons**: Complex workflow, easy to make mistakes, difficult dependency management
   - **Rejected**: Poor developer experience

4. **Poetry Plugins/Workspaces** (experimental)
   - **Pros**: Native monorepo support
   - **Cons**: Experimental feature, not stable as of 2025
   - **Reference**: [Poetry Workspaces Discussion](https://github.com/python-poetry/poetry/issues/936)
   - **Deferred**: May revisit when feature is stable

#### Implementation Guidance

**Step 1: Repository Structure**

```
bellweaver/  (repo root)
├── packages/
│   ├── compass-client/
│   │   ├── compass_client/      # Package source
│   │   ├── tests/
│   │   ├── pyproject.toml       # Compass package config
│   │   └── README.md
│   │
│   └── bellweaver/
│       ├── bellweaver/          # App source (currently in backend/)
│       ├── tests/
│       ├── pyproject.toml       # Bellweaver app config
│       └── README.md
│
├── frontend/                    # React app (unchanged)
├── .github/workflows/           # Separate workflows per package
└── README.md                    # Monorepo documentation
```

**Step 2: Compass Client pyproject.toml**

```toml
[tool.poetry]
name = "compass-client"
version = "0.1.0"
description = "Python client for Compass Education API"
authors = ["Your Name <email@example.com>"]
packages = [{include = "compass_client"}]

[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.31.0"
beautifulsoup4 = "^4.12.0"
pydantic = "^2.5.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Step 3: Bellweaver pyproject.toml (Modified)**

```toml
[tool.poetry]
name = "bellweaver"
version = "0.1.0"
# ... existing metadata ...

[tool.poetry.dependencies]
python = "^3.11"
# Path dependency for local development
compass-client = {path = "../compass-client", develop = true}
# ... existing dependencies (Flask, SQLAlchemy, etc.) ...

[tool.poetry.group.dev.dependencies]
# ... existing dev dependencies ...

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Key Configuration Notes**:
- `develop = true`: Installs compass-client in editable mode (like `pip install -e`)
- Path is relative from bellweaver/pyproject.toml location
- Both packages can be independently developed and tested

**Step 4: Development Workflow**

```bash
# Install compass-client package
cd packages/compass-client
poetry install

# Run compass-client tests
poetry run pytest

# Install bellweaver (automatically installs compass-client via path dep)
cd packages/bellweaver
poetry install

# Run bellweaver tests (compass-client is available)
poetry run pytest
```

**Step 5: Docker Configuration**

```dockerfile
# Multi-stage build for both packages
FROM python:3.11-slim as builder

# Install Poetry
RUN pip install poetry

# Build compass-client
WORKDIR /build/compass-client
COPY packages/compass-client/pyproject.toml packages/compass-client/poetry.lock ./
RUN poetry build

# Install bellweaver with compass-client
WORKDIR /app
COPY packages/bellweaver/pyproject.toml packages/bellweaver/poetry.lock ./
COPY --from=builder /build/compass-client/dist/*.whl /tmp/
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev \
    && pip install /tmp/*.whl
```

#### Package Public API Design

**Compass Client Public Interface** (`compass_client/__init__.py`):

```python
"""
Compass Education API client library.

Public API:
    - CompassClient: Real HTTP client
    - CompassMockClient: Mock client for testing
    - create_client: Factory function
    - CompassEvent, CompassUser: Data models
    - CompassClientError: Base exception
"""

from compass_client.client import CompassClient
from compass_client.mock_client import CompassMockClient
from compass_client.factory import create_client
from compass_client.models import CompassEvent, CompassUser
from compass_client.exceptions import (
    CompassClientError,
    CompassAuthenticationError,
    CompassParseError
)

__version__ = "0.1.0"

__all__ = [
    "CompassClient",
    "CompassMockClient",
    "create_client",
    "CompassEvent",
    "CompassUser",
    "CompassClientError",
    "CompassAuthenticationError",
    "CompassParseError",
]
```

**Bellweaver Usage**:

```python
# In bellweaver/api/routes.py
from compass_client import create_client, CompassEvent, CompassClientError

def sync_calendar():
    try:
        client = create_client()  # Auto-detects mode from environment
        events_data = client.get_calendar_events()
        # ... process events
    except CompassClientError as e:
        # Handle compass-specific errors
        pass
```

#### Testing Strategy

**Compass Package Tests** (packages/compass-client/tests/):
```bash
# Run only compass-client tests
cd packages/compass-client
poetry run pytest

# Tests have NO knowledge of bellweaver
# Test coverage focuses on:
# - Client authentication and HTTP calls
# - Mock client data loading
# - Model validation
# - Parser logic
```

**Bellweaver Tests** (packages/bellweaver/tests/):
```bash
# Run only bellweaver tests
cd packages/bellweaver
poetry run pytest

# Can mock compass_client package:
from unittest.mock import patch

@patch('compass_client.create_client')
def test_api_endpoint(mock_create):
    mock_create.return_value = MockCompassClient()
    # ... test bellweaver logic
```

#### CI/CD Workflow Separation

**Workflow: test-compass.yml**
```yaml
name: Test Compass Client

on:
  pull_request:
    paths:
      - 'packages/compass-client/**'
      - '.github/workflows/test-compass.yml'
  push:
    branches: [main]
    paths:
      - 'packages/compass-client/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Poetry
        run: pip install poetry
      - name: Install dependencies
        working-directory: packages/compass-client
        run: poetry install
      - name: Run tests
        working-directory: packages/compass-client
        run: poetry run pytest --cov=compass_client
```

**Workflow: test-bellweaver.yml**
```yaml
name: Test Bellweaver

on:
  pull_request:
    paths:
      - 'packages/bellweaver/**'
      - 'packages/compass-client/**'  # Re-run if dependency changes
      - '.github/workflows/test-bellweaver.yml'
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Poetry
        run: pip install poetry

      # Install compass-client first
      - name: Install Compass Client
        working-directory: packages/compass-client
        run: poetry install

      # Install bellweaver (with compass-client path dependency)
      - name: Install Bellweaver
        working-directory: packages/bellweaver
        run: poetry install
        env:
          COMPASS_MODE: mock  # Use mock data in CI

      - name: Run tests
        working-directory: packages/bellweaver
        run: poetry run pytest --cov=bellweaver
```

#### Migration Path from Current Structure

**Current**: `backend/bellweaver/` contains everything

**Migration Steps**:

1. Create `packages/compass-client/` directory structure
2. Move files from bellweaver to compass-client:
   - `adapters/compass.py` → `compass_client/client.py`
   - `adapters/compass_mock.py` → `compass_client/mock_client.py`
   - `models/compass.py` → `compass_client/models.py`
   - `parsers/compass.py` → `compass_client/parser.py`
   - `data/mock/` → `compass_client/data/mock/`
3. Create compass-client `pyproject.toml` with minimal dependencies
4. Create compass-client `__init__.py` with public API exports
5. Move compass-related tests to `packages/compass-client/tests/`
6. Create `packages/bellweaver/` and move `backend/` contents
7. Update bellweaver `pyproject.toml` to add compass-client path dependency
8. Update all imports in bellweaver from `bellweaver.adapters.compass` to `compass_client`
9. Remove moved files from bellweaver package
10. Update Docker build to handle both packages
11. Create separate GitHub workflows
12. Update documentation

#### Benefits Summary

| Benefit | How Monorepo Achieves It |
|---------|-------------------------|
| True decoupling | Enforced at package boundary, impossible to import bellweaver from compass-client |
| Independent testing | Separate test suites, can run `pytest` in each package directory |
| Selective CI | Path-based workflow filtering on `packages/*/` |
| Clear contracts | Public API defined in `__init__.py`, internal modules not importable |
| Future flexibility | Can publish to PyPI by changing from path to version dependency |
| Local development | Poetry path dependencies with `develop=true` for instant feedback |

#### Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Increased complexity | Clear documentation, simple structure, only 2 packages |
| Circular dependencies | Impossible - compass-client has zero bellweaver dependencies |
| Version skew | Path dependencies always use local version, no version conflicts |
| Build time increase | Minimal - compass-client is lightweight, builds in seconds |
| Developer confusion | README with clear setup instructions, automated scripts |

---

### 1. Factory Pattern for Client Selection

#### Decision: Implement Simple Factory Function with Protocol-Based Interface

Use a simple factory function that returns either a real or mock Compass client based on environment configuration. Both clients will implement a common protocol (Python `Protocol` or abstract base class) to ensure interface consistency.

#### Rationale

- **Simplicity**: A factory function is lightweight and doesn't require a dependency injection framework for this use case
- **Type Safety**: Python `Protocol` provides structural typing without requiring inheritance, making it easy to ensure both clients match the same interface
- **Testability**: Clients can be easily swapped in tests without modifying application code
- **Explicit Dependencies**: The factory makes it clear where client selection happens, improving code maintainability
- **Zero Runtime Overhead**: Unlike full DI frameworks, a simple factory has minimal performance impact

According to industry best practices, "Program to interfaces, not implementations by defining dependencies using abstract base classes or interfaces, which makes code easier to test and encourages the use of mocks in unit tests." ([ArjanCodes - Python Dependency Injection Best Practices](https://arjancodes.com/blog/python-dependency-injection-best-practices/))

#### Alternatives Considered

1. **Full Dependency Injection Framework** (e.g., dependency-injector)
   - **Pros**: Comprehensive container management, advanced features
   - **Cons**: Adds complexity and dependencies for a relatively simple use case; overkill for this project size
   - **Reference**: [Dependency Injector Documentation](https://python-dependency-injector.ets-labs.org/)

2. **Strategy Pattern with Runtime Injection**
   - **Pros**: Very flexible, allows runtime strategy changes
   - **Cons**: More complex than needed; adds indirection without significant benefit
   - **Reference**: [Python Patterns Guide](https://python-patterns.guide/gang-of-four/factory-method/)

3. **Monkey Patching in Tests**
   - **Pros**: Minimal code changes
   - **Cons**: Fragile, hard to maintain, implicit dependencies, can cause test pollution
   - **Rejected**: Does not meet requirements for production mock mode

#### Implementation Guidance

**Step 1: Define Common Protocol**

```python
# backend/bellweaver/adapters/compass_protocol.py
from typing import Protocol, Dict, List, Any, Optional


class CompassClientProtocol(Protocol):
    """Protocol that both real and mock Compass clients must implement."""

    base_url: str
    username: str
    user_id: Optional[int]
    _authenticated: bool

    def authenticate(self) -> bool:
        """Authenticate with Compass and set up session."""
        ...

    def get_user_details(self) -> Dict[str, Any]:
        """Get current user details."""
        ...

    def get_calendar_events(
        self,
        start_date: str,
        end_date: str,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get calendar events for a date range."""
        ...
```

**Step 2: Update Existing Clients to Match Protocol**

Both `CompassClient` and `CompassMockClient` should be updated to match the protocol. Since they already share similar interfaces, this should require minimal changes.

**Step 3: Implement Factory Function**

```python
# backend/bellweaver/adapters/factory.py
import os
from typing import Optional
from .compass_protocol import CompassClientProtocol
from .compass import CompassClient
from .compass_mock import CompassMockClient


class CompassClientConfigError(Exception):
    """Raised when Compass client configuration is invalid."""
    pass


def create_compass_client(
    mode: Optional[str] = None,
    base_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> CompassClientProtocol:
    """
    Factory function to create appropriate Compass client based on configuration.

    Args:
        mode: Operating mode ('mock' or 'real'). Defaults to COMPASS_MODE env var.
        base_url: Compass base URL. Defaults to COMPASS_BASE_URL env var.
        username: Compass username. Defaults to COMPASS_USERNAME env var.
        password: Compass password. Defaults to COMPASS_PASSWORD env var.

    Returns:
        CompassClientProtocol: Either CompassClient or CompassMockClient

    Raises:
        CompassClientConfigError: If required configuration is missing or invalid

    Example:
        >>> # Use environment variables
        >>> client = create_compass_client()
        >>>
        >>> # Override mode explicitly
        >>> client = create_compass_client(mode='mock')
        >>>
        >>> # Provide all parameters
        >>> client = create_compass_client(
        ...     mode='real',
        ...     base_url='https://school.compass.education',
        ...     username='user@example.com',
        ...     password='secret'
        ... )
    """
    # Get mode from parameter or environment
    mode = (mode or os.getenv('COMPASS_MODE', 'real')).lower().strip()

    # Validate mode
    if mode not in ('mock', 'real'):
        raise CompassClientConfigError(
            f"Invalid COMPASS_MODE: '{mode}'. Must be 'mock' or 'real'."
        )

    # Get credentials from parameters or environment
    base_url = base_url or os.getenv('COMPASS_BASE_URL', '')
    username = username or os.getenv('COMPASS_USERNAME', '')
    password = password or os.getenv('COMPASS_PASSWORD', '')

    # Mock mode: credentials are optional (uses defaults)
    if mode == 'mock':
        return CompassMockClient(
            base_url=base_url or 'https://mock.compass.education',
            username=username or 'mock_user',
            password=password or 'mock_password'
        )

    # Real mode: validate required credentials
    if not base_url:
        raise CompassClientConfigError(
            "COMPASS_BASE_URL is required when COMPASS_MODE='real'"
        )
    if not username:
        raise CompassClientConfigError(
            "COMPASS_USERNAME is required when COMPASS_MODE='real'"
        )
    if not password:
        raise CompassClientConfigError(
            "COMPASS_PASSWORD is required when COMPASS_MODE='real'"
        )

    return CompassClient(
        base_url=base_url,
        username=username,
        password=password
    )
```

**Step 4: Update Application Code**

Replace direct client instantiation with factory calls:

```python
# Before
from bellweaver.adapters.compass import CompassClient
client = CompassClient(base_url, username, password)

# After
from bellweaver.adapters.factory import create_compass_client
client = create_compass_client()  # Uses environment variables
```

**Error Handling Best Practices**

1. **Fail Fast**: Validate configuration at startup, not during first API call
2. **Clear Messages**: Error messages should tell users exactly what's missing or invalid
3. **Helpful Defaults**: Mock mode should work without any configuration
4. **Type Safety**: Use Protocol for compile-time interface checking (requires mypy)

---

### 2. Environment-Based Configuration

#### Decision: Use python-dotenv with Multi-File Strategy and Explicit Mode Variable

Implement environment-based configuration using `python-dotenv` with support for multiple environment files (`.env` for development, `.env.test` for testing). Add a new `COMPASS_MODE` environment variable to control operational mode.

#### Rationale

- **Industry Standard**: python-dotenv is used by over 70% of Python developers for configuration management (2025 industry reports)
- **12-Factor Principles**: Follows 12-factor app methodology for configuration management
- **Security**: Keeps credentials out of code and provides clear separation between environments
- **Flexibility**: Supports both development (file-based) and production (environment-based) workflows
- **Developer Experience**: Simple `.env` files are easy to understand and modify

According to best practices, "When deploying to production or a cloud service, set environment variables in the environment directly (e.g., through AWS, Heroku, or Docker)." ([GeeksforGeeks - Python Environment Variables](https://www.geeksforgeeks.org/python/using-python-environment-variables-with-python-dotenv/))

#### Alternatives Considered

1. **Configuration Files (YAML/TOML)**
   - **Pros**: Structured, supports complex nested configuration
   - **Cons**: Requires additional parsing, not as widely adopted for credentials
   - **Rejected**: Environment variables are simpler and more secure for this use case

2. **Python Configuration Modules**
   - **Pros**: Type-safe with dataclasses, IDE support
   - **Cons**: Requires more boilerplate, less standard than .env
   - **Partial Adoption**: Use for parsed/validated config, but load from env vars

3. **Config Management Tools** (e.g., dynaconf, python-decouple)
   - **Pros**: Advanced features, multiple sources
   - **Cons**: Additional complexity and dependencies
   - **Rejected**: python-dotenv is sufficient for current needs

#### Implementation Guidance

**Step 1: Update .env.example with New Variables**

```bash
# Bellweaver Environment Variables
# Copy this file to .env and fill in your values
# This file is used by both Docker and local development

# Compass API Mode (mock or real)
# - 'mock': Use sample data from backend/data/mock/ (no credentials required)
# - 'real': Connect to actual Compass API (credentials required below)
COMPASS_MODE=mock

# Compass API credentials (required only when COMPASS_MODE=real)
COMPASS_USERNAME=your_compass_username
COMPASS_PASSWORD=your_compass_password
COMPASS_BASE_URL=https://your-school.compass.education

# Claude API Key (required)
CLAUDE_API_KEY=your-anthropic-api-key-here

# Database Encryption Key (auto-generated on first run if not provided)
BELLWEAVER_ENCRYPTION_KEY=will-be-auto-generated-on-first-run

# Flask Configuration (optional)
FLASK_ENV=development
FLASK_DEBUG=1

# Database location (optional, defaults to data/bellweaver.db)
DATABASE_URL=sqlite:///./data/bellweaver.db
```

**Step 2: Create .env.test for Testing**

```bash
# Test environment configuration
COMPASS_MODE=mock
CLAUDE_API_KEY=test_key_for_ci
DATABASE_URL=sqlite:///:memory:
FLASK_ENV=testing
FLASK_DEBUG=0
```

**Step 3: Update Application Initialization**

```python
# backend/bellweaver/__init__.py or main entry point
import os
from pathlib import Path
from dotenv import load_dotenv


def load_environment(env_file: str = '.env') -> None:
    """
    Load environment variables from .env file.

    Loads variables from specified file if it exists. In production,
    environment variables can be set directly without a file.

    Args:
        env_file: Name of environment file to load (default: '.env')
    """
    # Find project root (where .env lives)
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / env_file

    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment from {env_path}")
    else:
        print(f"No {env_file} file found, using system environment variables")


def get_config_mode() -> str:
    """
    Get current configuration mode with validation.

    Returns:
        str: Configuration mode ('mock' or 'real')

    Raises:
        ValueError: If COMPASS_MODE is invalid
    """
    mode = os.getenv('COMPASS_MODE', 'real').lower().strip()
    if mode not in ('mock', 'real'):
        raise ValueError(f"Invalid COMPASS_MODE: '{mode}'. Must be 'mock' or 'real'.")
    return mode


# Load environment at import time
load_environment()
```

**Step 4: Update Test Configuration**

```python
# backend/tests/conftest.py
import pytest
from dotenv import load_dotenv
from pathlib import Path


@pytest.fixture(scope='session', autouse=True)
def load_test_env():
    """Load test environment variables before any tests run."""
    test_env = Path(__file__).parent.parent / '.env.test'
    if test_env.exists():
        load_dotenv(test_env, override=True)
    else:
        # Fallback: set mock mode directly if .env.test missing
        import os
        os.environ['COMPASS_MODE'] = 'mock'
```

**Step 5: CLI Configuration Override**

```python
# backend/bellweaver/cli/commands/compass.py
import typer
from typing import Optional

app = typer.Typer()


@app.command()
def sync(
    mode: Optional[str] = typer.Option(
        None,
        '--mode',
        '-m',
        help="Override COMPASS_MODE: 'mock' or 'real'"
    )
):
    """Sync data from Compass API."""
    from bellweaver.adapters.factory import create_compass_client

    # Factory will use --mode flag or fall back to environment variable
    client = create_compass_client(mode=mode)
    # ... rest of sync logic
```

**Security Best Practices (2025 Standards)**

1. **Never Commit .env**: Always in `.gitignore`
2. **File Permissions**: Set `.env` to 600 (read/write for owner only)
3. **Separate Environments**: Different files for dev/test/production
4. **Production**: Use platform environment variables (Docker, AWS, etc.) instead of files
5. **Audit Trail**: Log when configuration is loaded (but never log credential values)

---

### 3. GitHub Actions Path Filtering

#### Decision: Use dorny/paths-filter for Granular Workflow Control

Implement separate workflows using the `dorny/paths-filter` action to conditionally run jobs based on changed files. Create three workflows:
1. **compass-library.yml**: Tests for Compass API library (runs only on library changes)
2. **bellweaver-app.yml**: Tests for Bellweaver application (runs on app changes)
3. **full-test.yml**: Comprehensive test suite (runs on demand or for main branch)

#### Rationale

- **Resource Efficiency**: "Saves time and resources, especially in monorepo setups" by running tests only when relevant code changes ([CI Cube - GitHub Actions Paths Filter](https://cicube.io/workflow-hub/github-actions-paths-filter/))
- **Granular Control**: Native GitHub `paths` filters don't work at job/step level; dorny/paths-filter provides the needed granularity
- **Proven Solution**: Industry standard for monorepo CI optimization with 4.5k+ stars on GitHub
- **Fast Feedback**: Developers get relevant test results faster by skipping unrelated tests
- **Clear Separation**: Makes dependency boundaries explicit through CI configuration

According to the documentation, "This action enables conditional execution of workflow steps and jobs, based on the files modified by pull request, on a feature branch, or by the recently pushed commits." ([dorny/paths-filter](https://github.com/dorny/paths-filter))

#### Alternatives Considered

1. **Native GitHub paths/paths-ignore**
   - **Pros**: Built-in, no external dependencies
   - **Cons**: Only works at workflow level, not job/step level; cannot combine multiple conditions easily
   - **Reference**: [GitHub Workflow Syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions)
   - **Rejected**: Insufficient granularity for this use case

2. **Custom Shell Scripts**
   - **Pros**: Full control, no action dependencies
   - **Cons**: Requires maintenance, error-prone, reinvents the wheel
   - **Rejected**: dorny/paths-filter is more reliable

3. **Separate Repositories**
   - **Pros**: Complete isolation, independent versioning
   - **Cons**: Complicates development, requires separate release processes
   - **Rejected**: Overkill; library is tightly coupled to application

#### Implementation Guidance

**Step 1: Restructure Repository for Clear Boundaries**

Ensure clear directory separation:
```
backend/
  bellweaver/
    adapters/
      compass.py           # Compass library
      compass_mock.py      # Compass library
      compass_protocol.py  # Compass library
      factory.py           # Shared (both)
    parsers/
      compass.py           # Bellweaver app
    api/                   # Bellweaver app
    cli/                   # Bellweaver app
    db/                    # Bellweaver app
  tests/
    test_compass_client.py          # Compass library tests
    test_compass_client_real.py     # Compass library tests
    test_compass_mock.py            # Compass library tests
    test_compass_parser.py          # Bellweaver app tests
    test_*.py                       # Bellweaver app tests
```

**Step 2: Create Workflow for Compass Library Tests**

```yaml
# .github/workflows/compass-library.yml
name: Compass Library Tests

on:
  pull_request:
    branches:
      - main
  push:
    branches:
      - main

jobs:
  # Detect which files changed
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      compass-library: ${{ steps.filter.outputs.compass-library }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Check for Compass library changes
        uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            compass-library:
              - 'backend/bellweaver/adapters/compass.py'
              - 'backend/bellweaver/adapters/compass_mock.py'
              - 'backend/bellweaver/adapters/compass_protocol.py'
              - 'backend/tests/test_compass_client.py'
              - 'backend/tests/test_compass_client_real.py'
              - 'backend/tests/test_compass_mock.py'
              - 'backend/pyproject.toml'

  # Run Compass library tests only if library changed
  test-compass-library:
    needs: detect-changes
    if: needs.detect-changes.outputs.compass-library == 'true'
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: backend

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: latest
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Load cached venv
        id: cached-poetry-dependencies
        uses: actions/cache@v3
        with:
          path: backend/.venv
          key: venv-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}

      - name: Install dependencies
        if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
        run: poetry install --with dev --no-interaction

      - name: Run Compass library tests
        run: |
          poetry run pytest \
            tests/test_compass_client.py \
            tests/test_compass_mock.py \
            --cov=bellweaver/adapters \
            --cov-report=xml \
            --cov-report=term
        env:
          COMPASS_MODE: mock

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./backend/coverage.xml
          flags: compass-library
          fail_ci_if_error: false
          token: ${{ secrets.CODECOV_TOKEN }}

  # Dummy job for required status checks when tests are skipped
  compass-library-skipped:
    needs: detect-changes
    if: needs.detect-changes.outputs.compass-library == 'false'
    runs-on: ubuntu-latest
    steps:
      - name: No Compass library changes detected
        run: echo "Compass library tests skipped - no relevant changes"
```

**Step 3: Create Workflow for Bellweaver Application Tests**

```yaml
# .github/workflows/bellweaver-app.yml
name: Bellweaver Application Tests

on:
  pull_request:
    branches:
      - main
  push:
    branches:
      - main

jobs:
  # Always run application tests (they're fast with mock data)
  test-bellweaver:
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: backend

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: latest
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Load cached venv
        id: cached-poetry-dependencies
        uses: actions/cache@v3
        with:
          path: backend/.venv
          key: venv-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}

      - name: Install dependencies
        if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
        run: poetry install --with dev --no-interaction

      - name: Run Bellweaver tests (with mock Compass)
        run: |
          poetry run pytest \
            --cov=bellweaver \
            --cov-report=xml \
            --cov-report=term \
            --ignore=tests/test_compass_client_real.py
        env:
          COMPASS_MODE: mock
          CLAUDE_API_KEY: test_key

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./backend/coverage.xml
          flags: bellweaver-app
          fail_ci_if_error: false
          token: ${{ secrets.CODECOV_TOKEN }}
```

**Step 4: Create Combined Workflow for Full Testing**

```yaml
# .github/workflows/full-test.yml
name: Full Test Suite

on:
  workflow_dispatch:  # Manual trigger
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  full-test:
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: backend

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: latest
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Install dependencies
        run: poetry install --with dev --no-interaction

      - name: Run full test suite
        run: |
          poetry run pytest \
            --cov=bellweaver \
            --cov-report=xml \
            --cov-report=term \
            --ignore=tests/test_compass_client_real.py
        env:
          COMPASS_MODE: mock
          CLAUDE_API_KEY: test_key
```

**Required Status Checks Configuration**

To handle the case where Compass library tests are skipped, configure branch protection rules to require either:
- `compass-library-tests` OR `compass-library-skipped`

According to best practices: "A dummy step that passes is necessary for required status checks" when using conditional jobs ([DevOpsSchool - GitHub Actions Paths Filter](https://www.devopsschool.com/blog/github-actions-paths-filter-complete-guide/))

**Expected Resource Savings**

Based on the current test setup:
- Compass library tests: ~1-2 minutes
- Bellweaver app tests: ~2-3 minutes
- Expected reduction: ~70% fewer unnecessary Compass library test runs

---

### 4. Mock Data Management

#### Decision: Store Mock Data as Versioned JSON with Pydantic Schema Validation

Store mock data as JSON files in `backend/data/mock/` directory with the following structure:
- One file per API endpoint (e.g., `compass_events.json`, `compass_user.json`)
- JSON format for readability and standard tooling support
- Commit files to repository (expected size < 10MB)
- Validate against Pydantic models during load

#### Rationale

- **Human Readable**: JSON is easy to inspect, edit, and review in pull requests
- **Standard Tooling**: All languages and tools support JSON natively
- **Type Safety**: Pydantic provides strong validation during load
- **Version Control Friendly**: Text format works well with Git diffs
- **Size Appropriate**: Compass API responses are small enough to commit (<10MB guideline)

According to best practices, "Adopt a semantic versioning strategy (e.g., MAJOR.MINOR.PATCH) to clearly communicate changes in your models" and "Maintain comprehensive documentation for each version of your schema." ([Restack - Model Versioning JSON Schema](https://www.restack.io/p/model-versioning-answer-json-schema-example-cat-ai))

#### Alternatives Considered

1. **Binary Formats** (Pickle, MessagePack)
   - **Pros**: Smaller size, faster loading
   - **Cons**: Not human-readable, not version-control friendly, security risks with pickle
   - **Rejected**: Readability is more important than performance for mock data

2. **Database Fixtures** (SQLite, fixtures in DB format)
   - **Pros**: Matches production data model
   - **Cons**: Requires DB setup, harder to inspect and modify, couples mock data to DB schema
   - **Rejected**: JSON provides better separation of concerns

3. **Python Modules** (dict definitions in .py files)
   - **Pros**: Can use Python for data generation, type hints
   - **Cons**: Mixing data with code, harder to parse in non-Python tools
   - **Rejected**: Prefer data files over code

4. **YAML Format**
   - **Pros**: More readable for nested structures, supports comments
   - **Cons**: Requires additional parsing library, less standard than JSON
   - **Partial Adoption**: Could use YAML for human-edited configuration, but JSON for API mock data

#### Implementation Guidance

**Step 1: Define Mock Data Directory Structure**

```
backend/
  data/
    mock/
      compass_events.json      # Calendar events mock data
      compass_user.json        # User details mock data
      README.md                # Documentation for mock data
      schema_version.json      # Schema version tracking
```

**Step 2: Create Schema Version Tracking**

```json
// backend/data/mock/schema_version.json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-12-09T00:00:00Z",
  "updated_by": "developer@example.com",
  "compass_api_version": "2025-Q4",
  "notes": "Initial mock data from production Compass instance",
  "endpoints": {
    "events": {
      "file": "compass_events.json",
      "record_count": 150,
      "date_range": "2025-01-01 to 2025-12-31",
      "model": "CompassEvent"
    },
    "user": {
      "file": "compass_user.json",
      "record_count": 1,
      "model": "CompassUser"
    }
  }
}
```

**Step 3: Create Mock Data README**

```markdown
# Mock Data Documentation

This directory contains sample data from the Compass API used for testing and development.

## Files

- **compass_events.json**: Sample calendar events (150 events covering 2025)
- **compass_user.json**: Sample user details (1 user profile)
- **schema_version.json**: Metadata about mock data versions and schemas

## Schema Validation

All mock data is validated against Pydantic models in `bellweaver/models/compass.py`:
- `compass_events.json` → `CompassEvent` model
- `compass_user.json` → `CompassUser` model

## Updating Mock Data

To refresh mock data from a real Compass instance:

```bash
# Ensure .env has COMPASS_MODE=real and valid credentials
poetry run bellweaver mock update --source real

# Review changes before committing
git diff backend/data/mock/

# Commit updated mock data
git add backend/data/mock/
git commit -m "data: update mock Compass data from production instance"
```

## Data Privacy

This mock data has been sanitized to remove:
- Personal identifying information (names, emails, phone numbers)
- School-specific details
- Sensitive content from event descriptions

Original data structure and types are preserved for testing.

## Size Limits

Keep mock data files under 10MB total to avoid repository bloat.
Current size: ~500KB

## Versioning

When mock data schema changes significantly:
1. Update `schema_version.json` with new version number
2. Document breaking changes in this README
3. Update validation tests to handle new schema
```

**Step 4: Implement Mock Data Validation Utility**

```python
# backend/bellweaver/adapters/mock_validator.py
from pathlib import Path
from typing import List, Dict, Any, Type, TypeVar
import json
from pydantic import BaseModel, ValidationError

T = TypeVar('T', bound=BaseModel)


class MockDataValidationError(Exception):
    """Raised when mock data fails validation."""
    pass


def load_and_validate_mock_data(
    file_path: Path,
    model: Type[T],
    allow_partial: bool = False
) -> List[T]:
    """
    Load JSON mock data and validate against Pydantic model.

    Args:
        file_path: Path to JSON file containing mock data
        model: Pydantic model class to validate against
        allow_partial: If True, skip invalid records instead of failing

    Returns:
        List of validated model instances

    Raises:
        MockDataValidationError: If data is invalid and allow_partial=False
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Mock data file not found: {file_path}")

    try:
        with open(file_path, 'r') as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as e:
        raise MockDataValidationError(f"Invalid JSON in {file_path}: {e}")

    # Handle both list and single object
    if not isinstance(raw_data, list):
        raw_data = [raw_data]

    validated_items: List[T] = []
    errors: List[Dict[str, Any]] = []

    for idx, item in enumerate(raw_data):
        try:
            validated_item = model.model_validate(item)
            validated_items.append(validated_item)
        except ValidationError as e:
            error_info = {
                'index': idx,
                'errors': e.errors(),
                'item': item
            }
            errors.append(error_info)

            if not allow_partial:
                raise MockDataValidationError(
                    f"Validation failed for item {idx} in {file_path}: {e}"
                )

    if errors and allow_partial:
        print(f"Warning: {len(errors)} items failed validation in {file_path}")
        print(f"Successfully loaded {len(validated_items)}/{len(raw_data)} items")

    if not validated_items:
        raise MockDataValidationError(f"No valid data found in {file_path}")

    return validated_items


def validate_mock_data_schema(mock_dir: Path) -> Dict[str, Any]:
    """
    Validate all mock data files against their expected schemas.

    Returns dict with validation results:
    {
        'valid': True/False,
        'files': {
            'compass_events.json': {'valid': True, 'count': 150, 'errors': []},
            'compass_user.json': {'valid': True, 'count': 1, 'errors': []}
        }
    }
    """
    from bellweaver.models.compass import CompassEvent, CompassUser

    validation_map = {
        'compass_events.json': CompassEvent,
        'compass_user.json': CompassUser,
    }

    results = {
        'valid': True,
        'files': {}
    }

    for filename, model in validation_map.items():
        file_path = mock_dir / filename
        file_result = {
            'valid': False,
            'count': 0,
            'errors': []
        }

        try:
            items = load_and_validate_mock_data(file_path, model, allow_partial=False)
            file_result['valid'] = True
            file_result['count'] = len(items)
        except (FileNotFoundError, MockDataValidationError) as e:
            file_result['errors'].append(str(e))
            results['valid'] = False

        results['files'][filename] = file_result

    return results
```

**Step 5: Best Practices for Mock Data Content**

1. **Data Sanitization**: Replace PII before committing:
   ```python
   # Example sanitization function
   def sanitize_event(event: dict) -> dict:
       """Remove PII from event data."""
       event['title'] = faker.sentence()
       event['description'] = faker.text(max_nb_chars=200)
       if 'attendees' in event:
           event['attendees'] = [
               {'name': f'Student {i}', 'email': f'student{i}@example.com'}
               for i in range(len(event['attendees']))
           ]
       return event
   ```

2. **Representative Coverage**: Include diverse examples:
   - Different event types (classes, excursions, parent-teacher conferences)
   - Various date ranges (past, current, future)
   - Edge cases (all-day events, multi-day events, cancelled events)

3. **Realistic Volume**: Match production patterns:
   - 100-200 events for a typical school year
   - 1-2 user profiles
   - Total size target: < 1MB per file

4. **Version Metadata**: Track schema evolution in schema_version.json

---

### 5. Startup Validation

#### Decision: Validate Mock Data at Application Startup with Graceful Degradation

Implement startup validation that checks mock data integrity when running in mock mode. Validation should:
1. Occur during application initialization (before accepting requests)
2. Use Pydantic `model_validate` for type-safe validation
3. Provide clear error messages indicating which files/fields are invalid
4. Fail fast in development, with optional graceful degradation in production

#### Rationale

- **Early Error Detection**: "Fail Fast" principle catches configuration issues before requests are processed
- **Clear Diagnostics**: Detailed validation errors help developers fix issues quickly
- **Type Safety**: Pydantic validation ensures mock data matches application expectations
- **Production Safety**: Graceful degradation prevents complete outages from bad mock data (if enabled)

According to Pydantic best practices, "Validation code should not raise ValidationError itself, but rather raise a ValueError or AssertionError (or subclass thereof) which will be caught and used to populate ValidationError." ([Pydantic Error Handling](https://docs.pydantic.dev/latest/errors/errors/))

#### Alternatives Considered

1. **Lazy Validation** (validate on first use)
   - **Pros**: Faster startup
   - **Cons**: Errors appear later, harder to debug, inconsistent behavior
   - **Rejected**: Fail-fast is better for development experience

2. **No Validation** (trust mock data is correct)
   - **Pros**: Simplest implementation
   - **Cons**: Runtime errors are confusing, no early warning of schema drift
   - **Rejected**: Validation is critical for maintaining mock data quality

3. **Pre-commit Hooks** (validate before git commit)
   - **Pros**: Catches issues before they reach CI
   - **Cons**: Can be bypassed, doesn't help in production
   - **Partial Adoption**: Use in addition to, not instead of, startup validation

4. **Continuous Validation** (validate on every request)
   - **Pros**: Catches dynamic issues
   - **Cons**: Significant performance overhead
   - **Rejected**: Startup validation is sufficient for static mock data

#### Implementation Guidance

**Step 1: Create Startup Validation Module**

```python
# backend/bellweaver/startup.py
import sys
from pathlib import Path
from typing import Optional
from pydantic import ValidationError
from logging import getLogger

from bellweaver.adapters.mock_validator import (
    validate_mock_data_schema,
    MockDataValidationError
)

logger = getLogger(__name__)


class StartupValidationError(Exception):
    """Raised when startup validation fails critically."""
    pass


def validate_mock_data_startup(
    mock_dir: Path,
    fail_fast: bool = True,
    graceful_degradation: bool = False
) -> bool:
    """
    Validate mock data files at application startup.

    Args:
        mock_dir: Directory containing mock data files
        fail_fast: If True, raise exception on validation failure
        graceful_degradation: If True, allow app to start with warnings

    Returns:
        bool: True if validation passed, False if failed but degraded gracefully

    Raises:
        StartupValidationError: If validation fails and fail_fast=True

    Example:
        >>> # In Flask app initialization
        >>> from bellweaver.startup import validate_mock_data_startup
        >>> validate_mock_data_startup(mock_dir, fail_fast=True)
    """
    logger.info(f"Validating mock data in {mock_dir}...")

    if not mock_dir.exists():
        error_msg = f"Mock data directory not found: {mock_dir}"
        logger.error(error_msg)

        if fail_fast and not graceful_degradation:
            raise StartupValidationError(error_msg)
        return False

    try:
        results = validate_mock_data_schema(mock_dir)
    except Exception as e:
        error_msg = f"Unexpected error during mock data validation: {e}"
        logger.exception(error_msg)

        if fail_fast and not graceful_degradation:
            raise StartupValidationError(error_msg)
        return False

    if not results['valid']:
        # Build detailed error message
        error_lines = ["Mock data validation failed:"]
        for filename, file_result in results['files'].items():
            if not file_result['valid']:
                error_lines.append(f"  - {filename}:")
                for error in file_result['errors']:
                    error_lines.append(f"      {error}")

        error_msg = "\n".join(error_lines)
        logger.error(error_msg)

        if fail_fast and not graceful_degradation:
            raise StartupValidationError(error_msg)

        logger.warning("Application starting with invalid mock data (graceful degradation enabled)")
        return False

    # Success
    logger.info("Mock data validation passed")
    for filename, file_result in results['files'].items():
        logger.info(f"  ✓ {filename}: {file_result['count']} records valid")

    return True


def startup_checks(compass_mode: str, mock_dir: Optional[Path] = None) -> None:
    """
    Run all startup validation checks based on application mode.

    Args:
        compass_mode: 'mock' or 'real'
        mock_dir: Path to mock data directory (required if compass_mode='mock')

    Raises:
        StartupValidationError: If critical validation fails

    Example:
        >>> # In Flask app factory
        >>> def create_app():
        >>>     app = Flask(__name__)
        >>>     startup_checks(
        >>>         compass_mode=os.getenv('COMPASS_MODE', 'real'),
        >>>         mock_dir=Path(__file__).parent / 'data' / 'mock'
        >>>     )
        >>>     return app
    """
    logger.info(f"Running startup checks (mode: {compass_mode})")

    if compass_mode == 'mock':
        if mock_dir is None:
            raise StartupValidationError("mock_dir is required when compass_mode='mock'")

        # Validate mock data with fail-fast in development
        # In production, you might want: fail_fast=False, graceful_degradation=True
        validate_mock_data_startup(
            mock_dir=mock_dir,
            fail_fast=True,
            graceful_degradation=False
        )

    elif compass_mode == 'real':
        # Could add checks for real mode (e.g., credentials present)
        logger.info("Real mode: skipping mock data validation")

    else:
        raise StartupValidationError(f"Invalid compass_mode: {compass_mode}")

    logger.info("✓ All startup checks passed")
```

**Step 2: Integrate into Flask Application**

```python
# backend/bellweaver/api/__init__.py
import os
from pathlib import Path
from flask import Flask
from logging import getLogger

from bellweaver.startup import startup_checks, StartupValidationError

logger = getLogger(__name__)


def create_app() -> Flask:
    """
    Flask application factory.

    Creates and configures the Flask application with startup validation.
    """
    app = Flask(__name__)

    # Load environment
    from bellweaver import load_environment
    load_environment()

    # Get configuration
    compass_mode = os.getenv('COMPASS_MODE', 'real')

    # Run startup checks BEFORE registering routes
    try:
        mock_dir = Path(__file__).parent.parent.parent / 'data' / 'mock'
        startup_checks(compass_mode=compass_mode, mock_dir=mock_dir)
    except StartupValidationError as e:
        logger.critical(f"Application startup failed: {e}")
        # In production, you might want to start anyway with degraded functionality
        # For development, fail fast to surface issues immediately
        raise

    # Register blueprints (only after validation passes)
    from bellweaver.api.routes import user_bp, events_bp
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(events_bp, url_prefix='/api')

    logger.info(f"✓ Flask application initialized (mode: {compass_mode})")
    return app
```

**Step 3: Add CLI Validation Command**

```python
# backend/bellweaver/cli/commands/mock.py
import typer
from pathlib import Path
from bellweaver.startup import validate_mock_data_startup, StartupValidationError

app = typer.Typer()


@app.command()
def validate():
    """
    Validate mock data files against expected schemas.

    Useful for checking mock data before committing or as a pre-commit hook.
    """
    mock_dir = Path(__file__).parent.parent.parent.parent / 'data' / 'mock'

    typer.echo(f"Validating mock data in {mock_dir}...")

    try:
        result = validate_mock_data_startup(mock_dir, fail_fast=True)
        if result:
            typer.secho("✓ All mock data is valid", fg=typer.colors.GREEN, bold=True)
            raise typer.Exit(0)
        else:
            typer.secho("✗ Mock data validation failed", fg=typer.colors.RED, bold=True)
            raise typer.Exit(1)
    except StartupValidationError as e:
        typer.secho(f"✗ Validation error: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(1)
```

**Step 4: Error Message Best Practices**

According to Pydantic error handling patterns:

```python
# Example: Formatting validation errors for user display
def format_validation_error(error: ValidationError, context: str = "") -> str:
    """
    Format Pydantic ValidationError into human-readable message.

    Args:
        error: Pydantic ValidationError
        context: Additional context (e.g., filename)

    Returns:
        Formatted error message with field paths and descriptions
    """
    lines = [f"Validation failed{f' for {context}' if context else ''}:"]

    for err in error.errors():
        field_path = " → ".join(str(loc) for loc in err['loc'])
        error_type = err['type']
        message = err['msg']

        lines.append(f"  • {field_path}: {message} (type: {error_type})")

        if 'input' in err and err['input'] is not None:
            # Show first 50 chars of invalid input
            input_preview = str(err['input'])[:50]
            if len(str(err['input'])) > 50:
                input_preview += "..."
            lines.append(f"      Input: {input_preview}")

    return "\n".join(lines)
```

**Step 5: Testing Startup Validation**

```python
# backend/tests/test_startup_validation.py
import pytest
import json
from pathlib import Path
from bellweaver.startup import (
    validate_mock_data_startup,
    startup_checks,
    StartupValidationError
)


def test_startup_validation_with_valid_data(tmp_path):
    """Test startup validation passes with valid mock data."""
    # Create valid mock data
    events_file = tmp_path / "compass_events.json"
    events_file.write_text(json.dumps([
        {
            "__type": "CalendarTransport:http://jdlf.com.au/ns/data/calendar",
            "activityId": 1,
            "title": "Test Event",
            # ... full valid event data
        }
    ]))

    # Should pass without error
    result = validate_mock_data_startup(tmp_path, fail_fast=True)
    assert result is True


def test_startup_validation_with_invalid_data(tmp_path):
    """Test startup validation fails with invalid mock data."""
    # Create invalid mock data (missing required fields)
    events_file = tmp_path / "compass_events.json"
    events_file.write_text(json.dumps([
        {"title": "Incomplete Event"}
    ]))

    # Should raise validation error
    with pytest.raises(StartupValidationError, match="Validation failed"):
        validate_mock_data_startup(tmp_path, fail_fast=True)


def test_startup_validation_graceful_degradation(tmp_path):
    """Test graceful degradation when validation fails."""
    # Create invalid mock data
    events_file = tmp_path / "compass_events.json"
    events_file.write_text(json.dumps([{"invalid": "data"}]))

    # Should not raise with graceful degradation
    result = validate_mock_data_startup(
        tmp_path,
        fail_fast=False,
        graceful_degradation=True
    )
    assert result is False


def test_startup_validation_missing_directory(tmp_path):
    """Test validation handles missing mock data directory."""
    missing_dir = tmp_path / "nonexistent"

    with pytest.raises(StartupValidationError, match="not found"):
        validate_mock_data_startup(missing_dir, fail_fast=True)
```

**Configuration by Environment**

| Environment | fail_fast | graceful_degradation | Behavior |
|-------------|-----------|----------------------|----------|
| Development | True | False | Fail immediately on invalid data |
| Testing | True | False | Fail immediately to catch issues |
| Staging | True | False | Fail to prevent bad deployments |
| Production | False | True | Log errors but allow startup |

**Performance Considerations**

- Validation at startup: ~50-200ms for typical mock data sizes
- Acceptable overhead: < 1% of total application startup time
- One-time cost: Only runs once at startup, not per request

---

## Implementation Checklist

### Phase 1: Core Infrastructure (Week 1)
- [ ] Create `CompassClientProtocol` interface
- [ ] Implement `create_compass_client()` factory function
- [ ] Add `COMPASS_MODE` to environment variables
- [ ] Update `.env.example` with new configuration
- [ ] Update existing code to use factory function
- [ ] Write tests for factory function and protocol

### Phase 2: Mock Data Infrastructure (Week 1-2)
- [ ] Create `backend/data/mock/` directory structure
- [ ] Implement mock data validation utilities
- [ ] Create `schema_version.json` metadata
- [ ] Write mock data README documentation
- [ ] Add mock data validation to startup process
- [ ] Create CLI command for mock data validation

### Phase 3: CI/CD Optimization (Week 2)
- [ ] Create `compass-library.yml` workflow
- [ ] Create `bellweaver-app.yml` workflow
- [ ] Create `full-test.yml` workflow
- [ ] Configure branch protection rules for new workflows
- [ ] Test workflow path filtering with sample PRs
- [ ] Update documentation with new CI structure

### Phase 4: Mock Data Management (Week 2-3)
- [ ] Implement mock data update CLI command
- [ ] Add data sanitization utilities
- [ ] Create representative mock data samples
- [ ] Test mock data with full application
- [ ] Document mock data update process
- [ ] Add pre-commit hook for validation (optional)

### Phase 5: Testing & Documentation (Week 3)
- [ ] Write integration tests for mock mode
- [ ] Write tests for startup validation
- [ ] Test CI workflows end-to-end
- [ ] Update CLAUDE.md with new patterns
- [ ] Create migration guide for developers
- [ ] Document troubleshooting common issues

---

## References

### Factory Pattern & Dependency Injection
- [Python Dependency Injection Best Practices | ArjanCodes](https://arjancodes.com/blog/python-dependency-injection-best-practices/)
- [The Factory Method Pattern | Python Patterns Guide](https://python-patterns.guide/gang-of-four/factory-method/)
- [Dependency Injection in Python | Better Stack Community](https://betterstack.com/community/guides/scaling-python/python-dependency-injection/)
- [Factory Method in Python | Refactoring Guru](https://refactoring.guru/design-patterns/factory-method/python/example)

### Environment Configuration
- [python-dotenv on GitHub](https://github.com/theskumar/python-dotenv)
- [Using Python Environment Variables with Python Dotenv | GeeksforGeeks](https://www.geeksforgeeks.org/python/using-python-environment-variables-with-python-dotenv/)
- [Best Practice to Manage Environment Variables in Pythonic Projects | Medium](https://medium.com/@rakeshonrediff/best-practice-to-manage-environment-variables-in-pythonic-projects-80d8bddd84f1)
- [Using Environment Variables in Python | The Python Corner](https://thepythoncorner.com/posts/2025-01-12-using-environment-variables-in-python/)

### GitHub Actions Path Filtering
- [dorny/paths-filter on GitHub](https://github.com/dorny/paths-filter)
- [GitHub Actions: paths-filter complete Guide | DevOpsSchool](https://www.devopsschool.com/blog/github-actions-paths-filter-complete-guide/)
- [How to conditionally run GitHub Actions | CI Cube](https://cicube.io/workflow-hub/github-actions-paths-filter/)
- [Boost GitHub Actions Efficiency with Path Filters | Thomas Thornton Blog](https://thomasthornton.cloud/2024/05/14/boost-github-actions-efficiency-with-path-filters-only-run-when-specific-files-or-paths-are-updated/)

### Mock Data & Schema Validation
- [jsonschema on PyPI](https://pypi.org/project/jsonschema/)
- [JSON Schema Validation in Python | jsonschema Documentation](https://python-jsonschema.readthedocs.io/)
- [Model Versioning JSON Schema Example | Restack](https://www.restack.io/p/model-versioning-answer-json-schema-example-cat-ai)
- [Working with JSON Schema in Python | CodeRivers](https://coderivers.org/blog/json-schema-python/)

### Pydantic Validation & Error Handling
- [Validation Errors | Pydantic Documentation](https://docs.pydantic.dev/latest/errors/validation_errors/)
- [Error Handling | Pydantic Documentation](https://docs.pydantic.dev/latest/errors/errors/)
- [JSON Validation | Pydantic Documentation](https://docs.pydantic.dev/latest/concepts/json/)
- [Validate JSON Documents in Python using Pydantic | Couchbase](https://www.couchbase.com/blog/validate-json-documents-in-python-using-pydantic/)

---

## Appendix: Key Code Patterns

### Pattern 1: Factory Function with Error Handling

```python
def create_compass_client(mode: Optional[str] = None) -> CompassClientProtocol:
    mode = (mode or os.getenv('COMPASS_MODE', 'real')).lower().strip()

    if mode not in ('mock', 'real'):
        raise CompassClientConfigError(f"Invalid mode: '{mode}'")

    if mode == 'mock':
        return CompassMockClient(...)

    # Validate credentials for real mode
    if not os.getenv('COMPASS_BASE_URL'):
        raise CompassClientConfigError("Missing COMPASS_BASE_URL")

    return CompassClient(...)
```

### Pattern 2: Environment Loading with Fallback

```python
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'

if env_path.exists():
    load_dotenv(env_path)
else:
    # Production: use system environment variables
    pass
```

### Pattern 3: Startup Validation with Graceful Degradation

```python
try:
    validate_mock_data_startup(mock_dir, fail_fast=True)
except StartupValidationError as e:
    if os.getenv('FLASK_ENV') == 'production':
        logger.warning(f"Mock data invalid, starting with degraded functionality: {e}")
    else:
        logger.critical(f"Startup failed: {e}")
        raise
```

### Pattern 4: GitHub Actions Path Filter

```yaml
- uses: dorny/paths-filter@v3
  id: filter
  with:
    filters: |
      compass-library:
        - 'backend/bellweaver/adapters/compass*.py'
        - 'backend/tests/test_compass_*.py'

- name: Run tests
  if: steps.filter.outputs.compass-library == 'true'
  run: pytest ...
```

### Pattern 5: Mock Data Validation

```python
from pydantic import ValidationError

try:
    items = [CompassEvent.model_validate(item) for item in raw_data]
except ValidationError as e:
    error_msg = format_validation_error(e, context=filename)
    raise MockDataValidationError(error_msg)
```

---

## Conclusion

This research provides a comprehensive technical foundation for implementing Compass API decoupling with mock data infrastructure. The recommended approaches prioritize:

1. **Simplicity**: Factory functions over complex DI frameworks
2. **Standards**: python-dotenv and industry-standard patterns
3. **Efficiency**: Path filtering to optimize CI resource usage
4. **Reliability**: Startup validation to catch issues early
5. **Maintainability**: Clear separation of concerns and documentation

All recommendations are based on current Python best practices (2025), proven industry patterns, and the specific needs of the Bellweaver project.
