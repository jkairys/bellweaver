# Bellweaver Documentation

**Last Updated:** December 1, 2025

## Project Overview

Bellweaver is a school calendar event aggregation and filtering tool that consolidates events from multiple sources and intelligently filters them based on relevance to specific children.

**Problem:** Parents receive overwhelming communication from multiple school sources (Compass, Class Dojo, HubHello, Xplore) with no unified view.

**Solution:** Single dashboard showing relevant calendar events for each child, powered by Claude API for intelligent filtering.

## Quick Links

- **[Quick Start Guide](quick-start.md)** - Get up and running in 5 minutes
- **[Docker Deployment](docker-deployment.md)** - Production deployment with Docker
- **[Architecture](architecture.md)** - System design and technical decisions
- **[Main README](../README.md)** - Project overview

## Current Status

### What's Working ✅

1. **Compass HTTP Client** (`packages/bellweaver/bellweaver/adapters/compass.py`)
   - Direct HTTP authentication (no browser automation)
   - Calendar event fetching from Compass API
   - Session management with cookies
   - Fast performance (~1 second total)
   - Integration tests passing

2. **Mock Client** (`packages/bellweaver/bellweaver/adapters/compass_mock.py`)
   - Realistic synthetic test data
   - Same interface as real client
   - No credentials required

3. **LLM Filter** (`packages/bellweaver/bellweaver/filtering/llm_filter.py`)
   - Claude API integration implemented
   - Event filtering and summarization
   - Not yet integrated into pipeline

4. **Credential Manager** (`packages/bellweaver/bellweaver/db/credentials.py`)
   - Fernet encryption implemented
   - Not yet integrated with database

5. **Database Layer** (`packages/bellweaver/bellweaver/db/`)
   - SQLAlchemy 2.0 with DeclarativeBase
   - Batch tracking for adapter method calls
   - ApiPayload storage for raw API responses
   - Encrypted credential storage
   - Full test coverage (26 tests passing)

6. **CLI Interface** (`packages/bellweaver/bellweaver/cli/`)
   - Typer-based command-line interface
   - Mock data management commands
   - Compass sync commands (user details and events)
   - API server management commands
   - All 75 tests passing

7. **Flask API** (`packages/bellweaver/bellweaver/api/`)
   - Application factory pattern
   - REST endpoints: `/api/user`, `/api/events`
   - Static file serving for production frontend
   - Health checks

8. **React Frontend** (`frontend/`)
   - Vite-based React application
   - Dashboard displaying user details and events
   - Responsive design with dark/light mode
   - API service layer with error handling
   - Development server with hot reload

9. **Docker Deployment** (Root directory)
   - Multi-stage Dockerfile (frontend + backend)
   - Docker Compose configuration
   - Single container serving both frontend and backend
   - Health checks and volume persistence

### What's Not Built ⏳

- Event filtering by child/relevance
- LLM-based event filtering integration
- End-to-end pipeline integration

## Tech Stack

### Backend

- **Language:** Python 3.10+
- **Package Manager:** Poetry
- **Web Framework:** Flask
- **Database:** SQLite
- **ORM:** SQLAlchemy 2.0
- **Encryption:** cryptography (Fernet)
- **LLM Integration:** Anthropic Claude API
- **CLI:** Typer

### Frontend

- **Framework:** React 18
- **Build Tool:** Vite
- **Styling:** CSS with dark/light mode

### Deployment

- **Containerization:** Docker with multi-stage builds
- **Orchestration:** Docker Compose
- **Reverse Proxy:** (Recommended for production: nginx, Traefik, or Caddy)

### Development Tools

- **Testing:** pytest + pytest-cov
- **Formatting:** black
- **Linting:** flake8
- **Type Checking:** mypy

## Project Structure

```
bellweaver/
├── packages/                      # Python packages (monorepo)
│   ├── compass-client/            # Compass API client library
│   │   ├── compass_client/
│   │   │   ├── adapters/          # ✅ HTTP-based Compass client
│   │   │   ├── models/            # Data models
│   │   │   └── parsers/           # Validation layer
│   │   └── tests/
│   └── bellweaver/                # Main application
│       ├── bellweaver/
│       │   ├── adapters/          # Calendar adapters
│       │   ├── db/                # ✅ Database layer
│       │   ├── filtering/         # ✅ Claude API filtering
│       │   ├── models/            # Data models
│       │   ├── api/               # ✅ Flask REST API
│       │   └── cli/               # ✅ CLI interface
│       ├── tests/                 # Unit & integration tests
│       └── pyproject.toml         # Poetry configuration
├── frontend/                      # React frontend (Vite)
├── docs/                          # Documentation
└── README.md                      # Project overview
```

## Development Workflow

### Setup

```bash
cd packages/bellweaver
poetry install --with dev
cp ../.env.example ../.env
# Edit .env with your credentials
```

### Testing

```bash
cd packages/bellweaver
poetry run pytest -v                    # All tests
poetry run pytest tests/ -v             # All tests in tests directory
```

### Code Quality

```bash
cd packages/bellweaver
poetry run black bellweaver tests    # Format
poetry run flake8 bellweaver tests   # Lint
poetry run mypy bellweaver          # Type check
```

## Environment Configuration

Required environment variables (in project root `.env`):

```bash
# Compass credentials
COMPASS_USERNAME=your_compass_username
COMPASS_PASSWORD=your_compass_password
COMPASS_BASE_URL=https://your-school.compass.education

# Claude API (optional, for filtering features)
CLAUDE_API_KEY=sk-ant-xxxxx

# Encryption key (auto-generated on first run)
BELLWEAVER_ENCRYPTION_KEY=
```

See `.env.example` in the project root for full template.

## Development Roadmap

### Phase 1: MVP Foundation (Current Phase)

**Completed:**

- [x] Compass HTTP client implementation
- [x] Mock client for testing
- [x] LLM filter implementation
- [x] Credential encryption implementation
- [x] Integration tests
- [x] Project structure and tooling

**Next Steps:**

- [ ] Database layer (SQLAlchemy models and schema)
- [ ] Flask API routes
- [ ] CLI interface
- [ ] Web UI (basic configuration and event display)
- [ ] End-to-end pipeline integration
- [ ] Full workflow testing

### Phase 2: Multi-Source Support (Future)

- [ ] Class Dojo adapter
- [ ] HubHello adapter
- [ ] Xplore adapter
- [ ] Event normalization layer
- [ ] Advanced filtering UI
- [ ] Improved styling

### Phase 3: Advanced Features (Future)

- [ ] Google Calendar sync
- [ ] Email/SMS notifications
- [ ] Scheduling and automation
- [ ] Multi-user support
- [ ] Cloud deployment (GCP)
- [ ] Mobile app

## Key Technical Decisions

### HTTP Client vs Browser Automation

**Decision:** Use HTTP client with direct requests

**Rationale:**

- Cloudflare blocks browser automation (even with stealth)
- HTTP client is faster (~1s vs ~10-15s)
- Simpler deployment (no browser dependencies)
- More reliable (fewer moving parts)
- Better Cloudflare bypass

### SQLite vs Cloud Database

**Decision:** Start with SQLite for MVP

**Rationale:**

- No server setup required
- Simple file-based storage
- Good enough for single-user local development
- Easy migration path to PostgreSQL/Cloud SQL later

### Fernet Encryption

**Decision:** Use symmetric encryption for credentials

**Rationale:**

- Simple and built-in to Python cryptography
- Suitable for local credential storage
- Key stored in environment (not in code)
- Good enough for single-user MVP

## Testing Strategy

### Integration Tests

- Real Compass authentication
- Calendar event fetching
- Various date ranges
- Error handling

### Unit Tests (Planned)

- Database operations
- Credential encryption/decryption
- LLM filtering logic
- API endpoints

### Test Data

- Mock client with realistic synthetic events
- Real Compass credentials for integration testing
- Synthetic user configs for filtering tests

## Troubleshooting

### Poetry Issues

```bash
cd backend
poetry lock --refresh
poetry install --with dev
poetry cache clear . --all
```

### Test Failures

```bash
# Verify .env has correct credentials
cat backend/.env

# Ensure you're in backend directory
cd backend
poetry run pytest -v
```

### Virtual Environment Issues

```bash
cd backend
poetry env remove python
poetry install --with dev
```

## Git Workflow

### Current Status

- **Branch:** main
- **Recent Work:** Compass client implementation and testing

### Never Commit

- `backend/.env` (contains credentials)
- `backend/.venv/` (virtual environment)
- `backend/data/` (user data and database)
- `__pycache__/` and `.pytest_cache/`

### Commit Style

- Clear, imperative tense
- Component prefix (e.g., "adapters:", "db:", "docs:")
- Example: "adapters: add HTTP-based Compass client"

## Common Tasks

### Adding Dependencies

```bash
cd backend
poetry add package-name                # Production
poetry add --group dev package-name    # Development
```

### Running Specific Tests

```bash
cd backend
poetry run pytest tests/test_compass_client_real.py::test_login -v
poetry run pytest tests/test_fixtures.py -v
```

### Updating Dependencies

```bash
cd backend
poetry update
```

## Performance Notes

### Compass Client

- Authentication: ~500ms
- Event fetch: ~500ms
- Total: ~1 second
- No browser overhead
- Session cookies reused within process

### Future Optimizations

- Database session cookie persistence (optional)
- Event caching to avoid repeated API calls
- Background sync jobs
- Rate limiting to avoid overwhelming Compass

## Security Considerations

### Credentials

- Stored encrypted using Fernet
- Encryption key in environment variable
- Never committed to git
- Database file gitignored

### API Keys

- Claude API key in environment
- Never hardcoded in source
- Rotation supported via environment update

### Session Management

- Cookies handled by requests.Session()
- Auto-cleanup on process exit
- Optional database persistence for cross-session reuse

## Success Metrics

### MVP Success Criteria

- User can authenticate with Compass
- User can fetch calendar events
- User can configure filtering rules
- User can view filtered events
- Events fetched and filtered within 5 seconds
- System works reliably with real data

### Future Success Criteria

- Support for 10+ concurrent users
- 99% uptime
- Automatic sync every 6 hours
- Support for multiple schools/sources

## Resources

- [Anthropic Claude API Docs](https://docs.anthropic.com)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [Flask Documentation](https://flask.palletsprojects.com)
- [Poetry Documentation](https://python-poetry.org/docs)
- [cryptography.io](https://cryptography.io/)

## Getting Help

1. Check [Quick Start Guide](quick-start.md) for setup issues
2. Review [Architecture](architecture.md) for technical questions
3. Check existing tests for usage examples
4. Review git history for implementation context

---

**Ready to start developing?** See [quick-start.md](quick-start.md) to get set up.
