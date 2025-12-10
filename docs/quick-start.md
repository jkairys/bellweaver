# Bellweaver - Quick Start Guide

Get up and running in 5 minutes.

## Choose Your Setup Method

### Option 1: Docker (Recommended - Easiest)

See **[Docker Deployment Guide](docker-deployment.md)** for complete instructions.

Quick start:
```bash
# Copy environment file
cp .env.example .env

# Edit .env with your Compass credentials
# Then build and start
docker-compose up -d

# Sync data
docker exec -it bellweaver bellweaver compass sync

# Access at http://localhost:5000
```

### Option 2: Local Development Setup

## Prerequisites

- Python 3.10+ (currently using 3.12.9)
- Poetry for dependency management
- Node.js 20+ (for frontend development)

## First Time Setup

```bash
# 1. Copy environment template (from project root)
cp .env.example .env

# 2. Edit with your credentials
vim .env

# Add the following to .env:
# COMPASS_USERNAME=your_compass_username
# COMPASS_PASSWORD=your_compass_password
# COMPASS_BASE_URL=https://your-school.compass.education
# CLAUDE_API_KEY=sk-ant-xxxxx (optional, for future filtering features)

# 3. Navigate to backend directory and install dependencies
cd packages/bellweaver
poetry install --with dev
```

## Using the CLI

```bash
cd packages/bellweaver

# Sync data from Compass
poetry run bellweaver compass sync

# Sync with custom date range
poetry run bellweaver compass sync --days 30

# Start the API server
poetry run bellweaver api serve

# Start with debug mode
poetry run bellweaver api serve --debug
```

## Running the Frontend

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Access at http://localhost:3000
# API calls are proxied to backend at http://localhost:5000
```

## Running Tests

```bash
cd packages/bellweaver

# Run all tests
poetry run pytest -v

# Run integration tests with real Compass credentials
poetry run pytest tests/test_compass_client_real.py -v

# Run specific test
poetry run pytest tests/test_compass_client_real.py::test_login -v
```

## Development Commands

```bash
cd packages/bellweaver

# Format code (Black)
poetry run black bellweaver tests

# Lint code (Flake8)
poetry run flake8 bellweaver tests

# Type check (mypy)
poetry run mypy bellweaver

# Install new packages
poetry add package-name                # Production
poetry add --group dev package-name    # Development only
```

## Project Structure

```
bellweaver/
├── packages/                      # Python packages (monorepo)
│   ├── compass-client/            # Compass API client library
│   │   ├── compass_client/
│   │   │   ├── adapters/          # ✅ HTTP-based Compass client
│   │   │   ├── models/            # Data models
│   │   │   └── parsers/           # Validation layer
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── bellweaver/                # Main application
│       ├── bellweaver/
│       │   ├── adapters/          # Calendar source adapters
│       │   ├── filtering/         # ✅ Claude API filtering
│       │   ├── db/                # ✅ Database layer
│       │   ├── api/               # ✅ Flask REST API
│       │   ├── cli/               # ✅ CLI interface
│       │   └── models/            # Data models
│       ├── tests/                 # Unit & integration tests
│       └── pyproject.toml         # Poetry configuration
│
├── frontend/                      # React frontend (Vite)
├── docs/                          # Documentation
├── .env.example                   # Environment template
└── README.md                      # Project overview
```

## Current Status

✅ **Compass Authentication** - HTTP-based client working (~1 second)
✅ **Calendar Fetching** - Can retrieve events from Compass API
✅ **Mock Data** - Realistic test data available for development
✅ **Tests Passing** - Integration tests with real credentials working
⏳ **In Progress** - Database integration, API routes, filtering pipeline

## Troubleshooting

**Poetry not finding packages?**

```bash
cd packages/bellweaver
poetry lock --refresh
poetry install --with dev
```

**Virtual environment issues?**

```bash
cd packages/bellweaver
poetry env remove python
poetry install --with dev
```

**Tests failing?**

```bash
# Check .env file has correct credentials
cat .env

# Ensure you're in the backend directory
cd packages/bellweaver
poetry run pytest -v
```

## Next Steps

See `docs/index.md` for complete project documentation and development roadmap.
