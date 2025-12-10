# Migration Guide: Compass API Decoupling

**Feature**: 002-compass-api-decoupling | **Date**: 2025-12-09
**Purpose**: Guide developers through migrating their existing Bellweaver codebase to the new decoupled Compass API architecture.

## Overview

The `002-compass-api-decoupling` feature refactors the Compass API integration into a new, independent Python package called `compass-client`. This guide will walk you through the necessary steps to update your Bellweaver application to consume the new `compass-client` package and leverage its features, including mock data support and environment-based configuration.

## Key Changes

-   **Monorepo Structure**: The project is now a multi-package monorepo.
    -   `packages/compass-client/`: The new standalone Compass API library.
    -   `packages/bellweaver/`: The main Bellweaver application, which now depends on `compass-client`.
-   **Package Renames/Moves**:
    -   Old `backend/bellweaver/` content has been moved to `packages/bellweaver/`.
-   **Import Paths**: Direct imports from `bellweaver.adapters.compass`, `bellweaver.models.compass`, `bellweaver.parsers.compass` are replaced with imports from the `compass_client` package.
-   **Client Instantiation**: Direct instantiation of `CompassClient` or `CompassMockClient` is replaced with the `create_client()` factory function, which handles mode selection.
-   **Configuration**: A new `COMPASS_MODE` environment variable controls whether the application uses the real Compass API or mock data.

## Migration Steps

Follow these steps to migrate your Bellweaver codebase:

### Step 1: Update Project Structure

1.  **Clone the latest repository**: Ensure your local repository is up-to-date with the `002-compass-api-decoupling` branch.
    ```bash
    git clone <repo-url>
    cd bellweaver
    git checkout 002-compass-api-decoupling
    ```
2.  **Verify Monorepo Setup**: Confirm that `packages/bellweaver/` and `packages/compass-client/` directories exist at the root.

### Step 2: Install New Package Dependencies

1.  **Install `compass-client`**: Navigate to the `compass-client` directory and install its dependencies.
    ```bash
    cd packages/compass-client
    poetry install --with dev
    ```
2.  **Install `bellweaver`**: Navigate to the `bellweaver` directory and install its dependencies. This will automatically install `compass-client` as a path dependency.
    ```bash
    cd ../bellweaver
    poetry install --with dev
    ```

### Step 3: Update Environment Variables

1.  **Update `.env.example`**: Copy the new `.env.example` to your local `.env` file.
    ```bash
    cp .env.example .env
    ```
2.  **Configure `COMPASS_MODE`**: Add or update the `COMPASS_MODE` variable in your `.env` file (or directly in your environment).
    ```dotenv
    # Use mock mode for local development
    COMPASS_MODE=mock

    # Configure real Compass credentials if needed
    COMPASS_BASE_URL=https://your-school.compass.education
    COMPASS_USERNAME=your_username
    COMPASS_PASSWORD=your_password
    ```

### Step 4: Update Python Imports

Replace old import statements with new ones from the `compass_client` package.

**Old Import Paths (Monolithic `bellweaver`):**
```python
from bellweaver.adapters.compass import CompassClient
from bellweaver.adapters.compass_mock import CompassMockClient
from bellweaver.models.compass import CompassEvent, CompassUser
from bellweaver.parsers.compass import CompassParser
```

**New Import Paths (`compass-client` Package):**
```python
from compass_client import (
    create_client,
    CompassClient,       # Still available for direct use if needed
    CompassMockClient,   # Still available for direct use if needed
    CompassEvent,
    CompassUser,
    CompassParser,
    CompassClientError,
    CompassAuthenticationError,
    CompassParseError
)
```

**Action**: Search and replace these imports across your Bellweaver codebase.

### Step 5: Update Client Instantiation

Replace direct client instantiation with the `create_client()` factory function.

**Old Client Instantiation:**
```python
# Manual client selection
if os.getenv("USE_MOCK") == "true":
    client = CompassMockClient(base_url, username, password)
else:
    client = CompassClient(base_url, username, password)
```

**New Client Instantiation (Recommended):**
```python
from compass_client import create_client

# Factory automatically selects mode based on COMPASS_MODE env var or explicit 'mode' parameter
client = create_client(
    base_url=os.getenv("COMPASS_BASE_URL"),
    username=os.getenv("COMPASS_USERNAME"),
    password=os.getenv("COMPASS_PASSWORD")
    # Optional: mode="mock" or mode="real" to override env var
)
```

**Action**: Update all code locations where `CompassClient` or `CompassMockClient` are instantiated.

### Step 6: Remove Old Code (Cleanup)

After migrating imports and client instantiation, remove the old Compass-related files from the `bellweaver` application.

**Files to Remove (from `packages/bellweaver/bellweaver/`):**
-   `adapters/compass.py`
-   `adapters/compass_mock.py`
-   `models/compass.py` (ensure `CompassEvent` and `CompassUser` are now imported from `compass_client`)
-   `parsers/compass.py` (ensure `CompassParser` is now imported from `compass_client`)

**Action**: Delete these files after confirming no other Bellweaver code directly uses them.

### Step 7: Update CI/CD Workflows

If you maintain separate CI/CD configurations, ensure they are updated to:

1.  **Install `compass-client`** first, then `bellweaver`.
2.  **Set `COMPASS_MODE=mock`** for CI runs to avoid geo-blocking and credential issues.
3.  **Utilize path filtering** if specific workflows for `compass-client` and `bellweaver` are desired (e.g., using `dorny/paths-filter@v3`).

**Action**: Review and update `.github/workflows/` files.

### Step 8: Test Your Migration

1.  **Run Tests**:
    ```bash
    cd packages/bellweaver
    poetry run pytest
    ```
2.  **Verify Local Development**:
    ```bash
    export COMPASS_MODE=mock
    poetry run bellweaver api serve
    ```
    Then, access API endpoints (e.g., `curl http://localhost:5000/user`) to confirm mock data is served.
3.  **Refresh Mock Data** (if you have real credentials):
    ```bash
    cd packages/compass-client
    poetry run python -m compass_client.cli refresh-mock-data \
        --base-url "$COMPASS_BASE_URL" \
        --username "$COMPASS_USERNAME" \
        --password "$COMPASS_PASSWORD"
    ```

## Post-Migration Benefits

-   **Clean Separation of Concerns**: Clear boundary between Compass API logic and application logic.
-   **Enhanced Testability**: Both packages can be tested independently.
-   **Improved CI/CD Efficiency**: Selective CI runs save time and resources.
-   **Simplified Local Development**: Mock mode allows immediate development without real credentials.

## Troubleshooting

-   **"Module 'compass_client' not found"**: Ensure `compass-client` is installed in your environment.
-   **"Authentication failed" in real mode**: Verify your Compass credentials and `COMPASS_BASE_URL`.
-   **Invalid mock data**: Run `poetry run bellweaver mock validate` to check mock data integrity.
-   Refer to **[docs/quick-start.md](docs/quick-start.md)** for detailed troubleshooting.

---

## Document Metadata

-   **Created**: 2025-12-09
-   **Feature**: 002-compass-api-decoupling
-   **Author**: Claude Code
-   **Related Documents**:
    -   [spec.md](../spec.md) - Feature specification
    -   [plan.md](../plan.md) - Implementation plan
    -   [data-model.md](../data-model.md) - Data model
    -   [quickstart.md](../quickstart.md) - Developer quickstart
    -   [contracts/](./contracts/) - API contracts