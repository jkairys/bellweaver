# Bellbird Project Index

**Last Updated**: November 22, 2025  
**Project Status**: Python Project Structure Initialized - Ready for Development

## 📚 Documentation Map

### Getting Started (Read First!)
1. **QUICK_START.md** - 2-minute setup and common commands
2. **SETUP_SUMMARY.md** - Detailed breakdown of what was initialized
3. This file (INDEX.md) - Navigation guide

### Project Understanding
4. **PLAN.md** - Project vision, problem statement, and user journey
5. **MVP_ARCHITECTURE.md** - System design, data flow, and technical decisions
6. **COMPASS_PYTHON_CLIENT_PLAN.md** - Compass API integration strategy
7. **README.md** - Complete project documentation

---

## 🎯 Quick Navigation

### For Developers
- **Setup?** → Read QUICK_START.md
- **Want to code?** → Check MVP_ARCHITECTURE.md for current structure
- **Need API details?** → See COMPASS_PYTHON_CLIENT_PLAN.md
- **Overall vision?** → Read PLAN.md

### For Project Management
- **What needs to be done?** → See MVP_ARCHITECTURE.md (Phase 1 checklist)
- **Timeline?** → MVP_ARCHITECTURE.md has 10-day breakdown
- **Architecture?** → Full details in MVP_ARCHITECTURE.md

---

## 📁 Project Structure

```
bellbird/
├── 📄 Documentation
│   ├── README.md                       # Full project docs
│   ├── QUICK_START.md                  # 2-minute setup
│   ├── SETUP_SUMMARY.md                # Detailed init info
│   ├── INDEX.md                        # This file
│   ├── PLAN.md                         # Project vision
│   ├── MVP_ARCHITECTURE.md             # System design
│   └── COMPASS_PYTHON_CLIENT_PLAN.md   # Compass integration
│
├── 🔧 Configuration
│   ├── pyproject.toml                  # Poetry configuration
│   ├── poetry.lock                     # Locked dependencies
│   ├── .env.example                    # Environment template
│   ├── .gitignore                      # Git exclusions
│   └── .venv/                          # Virtual environment (git-ignored)
│
├── 📦 Source Code (src/)
│   ├── __init__.py                     # Package marker
│   ├── cli.py                          # [TODO] CLI entry point
│   ├── app.py                          # [TODO] Flask application
│   │
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── compass.py                  # [TODO] Real Compass API
│   │   └── compass_mock.py             # [TODO] Mock data provider
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── config.py                   # [TODO] Data models
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py                 # [TODO] SQLAlchemy setup
│   │   ├── credentials.py              # [TODO] Encrypted storage
│   │   └── models.py                   # [TODO] ORM models
│   │
│   ├── filtering/
│   │   ├── __init__.py
│   │   └── llm_filter.py               # [TODO] Claude API integration
│   │
│   └── api/
│       ├── __init__.py
│       ├── routes.py                   # [TODO] Flask endpoints
│       └── schemas.py                  # [TODO] Request/response models
│
├── 🧪 Tests (tests/)
│   ├── __init__.py
│   ├── test_compass_adapter.py         # [TODO]
│   ├── test_compass_mock.py            # [TODO]
│   └── test_filtering.py               # [TODO]
│
├── 🎨 Frontend (frontend/)
│   ├── index.html                      # [TODO] Onboarding form
│   ├── dashboard.html                  # [TODO] Event dashboard
│   ├── css/
│   │   └── style.css                   # [TODO] Styling
│   └── js/
│       └── app.js                      # [TODO] Client logic
│
└── 💾 Data (data/)
    └── .gitkeep                        # SQLite DB created here at runtime
```

---

## 🚀 Implementation Roadmap

### Phase 1: MVP (10 Days to Working Tool)

#### Days 1-2: Database Foundation
- [ ] `src/db/database.py` - SQLAlchemy session management
- [ ] `src/db/models.py` - ORM models (Credentials, Config, Events, Sync)
- [ ] `src/db/credentials.py` - Encrypted credential storage

#### Days 2-3: Testing Framework (Parallel)
- [ ] `src/adapters/compass_mock.py` - Synthetic Compass events
- [ ] Unit tests for mock adapter

#### Days 3-5: Filtering & Real Integration
- [ ] `src/filtering/llm_filter.py` - Claude API integration
- [ ] `src/adapters/compass.py` - Real Compass API client
- [ ] Integration tests

#### Days 5-7: Web & CLI
- [ ] `src/cli.py` - Command-line interface
- [ ] `src/app.py` - Flask application factory
- [ ] `src/api/routes.py` - REST API endpoints
- [ ] `src/api/schemas.py` - Request/response validation

#### Days 7-9: User Interface
- [ ] `frontend/index.html` - Onboarding form
- [ ] `frontend/dashboard.html` - Event dashboard
- [ ] `frontend/css/style.css` - Basic styling
- [ ] `frontend/js/app.js` - Client-side logic

#### Days 9-10: Integration & Polish
- [ ] End-to-end testing
- [ ] Error handling
- [ ] Documentation
- [ ] Performance optimization
- [ ] Final testing with real data

### Phase 2: Multi-Source Support
- [ ] Add normalization layer
- [ ] Integrate Class Dojo
- [ ] Integrate HubHello
- [ ] Integrate Xplore
- [ ] Advanced filtering UI

---

## 💾 Dependency Overview

### Production Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| requests | ^2.32.5 | HTTP client for Compass API |
| cryptography | ^46.0.3 | Credential encryption (Fernet) |
| anthropic | ^0.74.1 | Claude API integration |
| sqlalchemy | ^2.0.44 | ORM for database |
| flask | ^3.1.2 | Web framework |
| python-dotenv | ^1.2.1 | Environment management |

### Development Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| pytest | ^7.4.0 | Testing framework |
| pytest-cov | ^4.1.0 | Test coverage |
| black | ^23.0.0 | Code formatting |
| flake8 | ^6.0.0 | Linting |
| mypy | ^1.18.2 | Type checking |

---

## 🔑 Key Features

✨ **No Browser Automation**
   Direct HTTP to Compass (faster than Puppeteer approach)

✨ **Local-First Design**
   SQLite database - no cloud setup for MVP

✨ **Encrypted Credentials**
   Fernet symmetric encryption for security

✨ **LLM-Powered Filtering**
   Claude API intelligently filters events

✨ **Mock Data Ready**
   Test without credentials using synthetic events

✨ **Multi-Source Foundation**
   Architecture supports adding more sources later

---

## 📋 Current Status

### ✅ Completed
- Poetry project initialization
- Virtual environment setup (.venv)
- All dependencies installed and locked
- Project directory structure created
- Configuration files (.env.example, .gitignore, pyproject.toml)
- Comprehensive documentation
- README, QUICK_START, and SETUP_SUMMARY guides

### ⏳ To Do
- All source code implementation (see roadmap above)
- Database models and schema
- API adapters (Compass, mock)
- Filtering logic
- REST endpoints
- CLI interface
- Web UI
- Unit tests

---

## 🛠️ Development Workflow

### Initial Setup
```bash
cd /Users/jethro/github/jkairys/bellbird
cp .env.example .env
# Edit .env with your CLAUDE_API_KEY
```

### Common Commands
```bash
poetry run pytest              # Run tests
poetry run black src tests     # Format code
poetry run flake8 src tests    # Lint code
poetry run mypy src            # Type check
poetry add package-name        # Add dependency
```

### When Ready
```bash
poetry run bellbird --help     # CLI (when implemented)
poetry run flask run           # Web server (when implemented)
```

---

## 📞 Support & References

- **Problems with Poetry?** → See QUICK_START.md troubleshooting section
- **Architecture questions?** → Read MVP_ARCHITECTURE.md
- **Compass API details?** → Check COMPASS_PYTHON_CLIENT_PLAN.md
- **Project vision?** → See PLAN.md
- **Full docs?** → Read README.md

---

## 📝 Notes

- Virtual environment is in `.venv/` (git-ignored)
- Database will be created in `data/bellbird.db` (git-ignored)
- Environment variables in `.env` (git-ignored, use `.env.example` as template)
- All package dependencies are locked in `poetry.lock`
- Python version: 3.10+ (currently using 3.12.9)

---

**Project initialized with Poetry on November 22, 2025**
**Ready for implementation - Start with the database layer!**
