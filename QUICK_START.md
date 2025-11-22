# Bellbird - Quick Start Guide

## What's Done ✅

Your Bellbird Python project is fully initialized with:

- **Poetry project** with all dependencies configured
- **Virtual environment** (.venv) with 22 core packages + 5 dev tools
- **Project structure** with organized src/, tests/, frontend/, and data/ directories
- **Configuration files** ready for use
- **Documentation** explaining architecture and usage

## First Time Setup (2 minutes)

```bash
# 1. Navigate to project
cd /Users/jethro/github/jkairys/bellbird

# 2. Copy environment template
cp .env.example .env

# 3. Edit with your API keys
# Add your CLAUDE_API_KEY to .env
vim .env

# 4. Verify Poetry is working
poetry --version
poetry env info
```

## Development Commands

```bash
# Run tests
poetry run pytest

# Format code (Black)
poetry run black src tests

# Lint code (Flake8)
poetry run flake8 src tests

# Type check (mypy)
poetry run mypy src

# Install new packages
poetry add package-name

# Run CLI (when implemented)
poetry run bellbird --help

# Run Flask server (when implemented)
poetry run flask run
```

## Project Structure at a Glance

```
bellbird/
├── src/                    # Main source code
│   ├── adapters/          # Compass API client (to implement)
│   ├── db/                # Database layer (to implement)
│   ├── filtering/         # Claude API filtering (to implement)
│   ├── models/            # Data models (to implement)
│   ├── api/               # Flask REST API (to implement)
│   ├── cli.py             # CLI entry point (to implement)
│   └── app.py             # Flask app (to implement)
│
├── frontend/              # Web UI (to implement)
├── tests/                 # Unit tests
├── data/                  # Runtime data (SQLite database will go here)
│
├── pyproject.toml         # Poetry configuration
├── .env.example           # Environment template
├── .gitignore             # Git rules
├── README.md              # Full documentation
└── QUICK_START.md         # This file
```

## MVP Timeline (Next Steps)

### Phase 1: MVP (10 days)
1. **Database Layer** - SQLite with encrypted credentials (Day 1-2)
2. **Mock Adapter** - Synthetic Compass events for testing (Day 2-3)
3. **Compass Client** - Real API integration (Day 4-5)
4. **Filtering** - Claude API event filtering (Day 3-5)
5. **CLI Interface** - Command-line tool (Day 5-6)
6. **Flask Backend** - REST API endpoints (Day 6-7)
7. **Web UI** - Simple HTML/JS frontend (Day 7-8)
8. **Integration & Polish** - Testing and refinement (Day 8-10)

### Key Files to Implement First
- `src/db/database.py` - Database connection & schema
- `src/db/models.py` - SQLAlchemy ORM models
- `src/adapters/compass_mock.py` - Mock data provider
- `src/filtering/llm_filter.py` - Claude integration

## Key Design Decisions (Reference)

1. **No Browser Automation**: Direct HTTP requests to Compass (faster, simpler)
2. **Local-First**: SQLite database, no cloud setup needed for MVP
3. **Encrypted Credentials**: Using cryptography.fernet for security
4. **LLM Filtering**: Claude API intelligently filters events
5. **Mock Data Ready**: Test without real credentials

## Useful Resources

- **PLAN.md** - Full project vision and requirements
- **MVP_ARCHITECTURE.md** - System design and data flow diagrams
- **COMPASS_PYTHON_CLIENT_PLAN.md** - Detailed integration plan
- **README.md** - Complete documentation

## Common Tasks

### Add a new dependency
```bash
poetry add package-name          # Production
poetry add --group dev package   # Development only
```

### Update dependencies
```bash
poetry update
```

### Clean virtual environment
```bash
poetry env remove bellbird
poetry install --with dev
```

### Export requirements.txt (if needed)
```bash
poetry export -f requirements.txt --output requirements.txt
```

## Environment Variables Explained

```bash
# Your Anthropic API key for Claude access
CLAUDE_API_KEY=sk-ant-xxxxx

# Auto-generated encryption key for credential storage
# Leave empty on first run - it will be generated and saved
BELLBIRD_ENCRYPTION_KEY=

# Flask settings (optional)
FLASK_ENV=development
FLASK_DEBUG=1

# Database location (optional, defaults to ./data/bellbird.db)
DATABASE_URL=sqlite:///./data/bellbird.db
```

## Troubleshooting

**Poetry not finding packages?**
```bash
poetry lock --refresh
poetry install --with dev
```

**Virtual environment issues?**
```bash
poetry env remove bellbird
poetry install --with dev
```

**Wrong Python version?**
```bash
poetry env info  # Check current Python
pyenv versions   # Check available versions
pyenv global 3.12.9  # Switch version if needed
```

## Next Steps

1. Review **PLAN.md** to understand the project scope
2. Read **MVP_ARCHITECTURE.md** for system design
3. Start implementing **src/db/database.py** - the foundation layer
4. Create **src/db/models.py** with SQLAlchemy ORM models
5. Build mock data in **src/adapters/compass_mock.py**

---

Happy coding! The project is ready to go. 🚀
