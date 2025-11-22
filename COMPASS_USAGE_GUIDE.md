# Compass API Client - Usage Guide

Quick reference for using the Compass adapters and related components.

## Using CompassMockClient (No Credentials Needed)

Perfect for development and testing:

```python
from src.adapters.compass_mock import CompassMockClient
from datetime import datetime, timedelta

# Initialize
client = CompassMockClient(
    base_url="https://mock.compass.example.com",
    username="test_user",
    password="test_password"
)

# Login (always succeeds in mock)
client.login()

# Fetch events
start_date = datetime.now().strftime("%Y-%m-%d")
end_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
events = client.get_calendar_events(start_date, end_date, limit=100)

# Process events
for event in events:
    print(f"{event['longTitle']} on {event['start']}")

# Clean up
client.close()
```

## Using CompassClient (Real Compass Instance)

For production use with real credentials:

```python
from src.adapters.compass import CompassClient
from datetime import datetime, timedelta

# Initialize with your Compass instance details
client = CompassClient(
    base_url="https://your-compass.edu.au",
    username="parent_username",
    password="parent_password"
)

try:
    # Login (validates credentials against Compass)
    client.login()
    print("✓ Authenticated with Compass")

    # Fetch events for 14-day window
    start = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    events = client.get_calendar_events(start, end)
    print(f"Retrieved {len(events)} events")

    # Process events
    for event in events:
        print(f"  • {event['longTitle']}")
        print(f"    Start: {event['start']}")
        if event.get('description'):
            print(f"    Notes: {event['description']}")

finally:
    client.close()
```

## Storing Credentials Securely

Use `CredentialManager` to encrypt and store credentials:

```python
from src.db.credentials import CredentialManager
from src.db.database import get_session

# Get database session
with get_session() as session:
    cred_manager = CredentialManager(session)

    # Save credentials (encrypted)
    cred_manager.save_compass_credentials(
        username="parent_username",
        password="parent_password"
    )
    print("✓ Credentials saved (encrypted)")

    # Load credentials later
    username, password = cred_manager.load_compass_credentials()

    # Use with Compass client
    client = CompassClient(
        base_url="https://your-compass.edu.au",
        username=username,
        password=password
    )
    client.login()
```

**Important:** Set `BELLBIRD_ENCRYPTION_KEY` in `.env`:
```bash
# First run generates key, then save it:
BELLBIRD_ENCRYPTION_KEY=your_generated_key_here
```

## Filtering Events with Claude

Use `LLMFilter` to intelligently filter events:

```python
from src.filtering.llm_filter import LLMFilter
import os

# Initialize filter with your API key
filter_engine = LLMFilter(api_key=os.getenv('CLAUDE_API_KEY'))

# Define user configuration
user_config = {
    'child_name': 'Emma',
    'school': 'Sample Primary School',
    'year_level': 'Year 3',
    'class': '3A',
    'interests': ['music', 'sports', 'science'],
    'filter_rules': 'Include events for Year 3 and mixed years. Exclude events before 8am.'
}

# Filter events
results = filter_engine.filter_events(events, user_config)

# Results structure:
# [
#   {
#     "event_id": "1",
#     "title": "Year 3 Excursion to Taronga Zoo",
#     "date": "2025-11-27",
#     "is_relevant": true,
#     "reason": "Year 3 specific excursion matching Emma's interests",
#     "action_needed": "Permission slip required. Cost: $25"
#   },
#   ...
# ]

for result in results:
    if result['is_relevant']:
        print(f"✓ {result['title']}")
        print(f"  Why: {result['reason']}")
        if result['action_needed']:
            print(f"  Action: {result['action_needed']}")
```

## Complete Pipeline Example

End-to-end example combining all components:

```python
from src.adapters.compass import CompassClient
from src.db.credentials import CredentialManager
from src.filtering.llm_filter import LLMFilter
from src.db.database import get_session
from datetime import datetime, timedelta
import os
import json

# 1. Load credentials
with get_session() as session:
    cred_manager = CredentialManager(session)
    username, password = cred_manager.load_compass_credentials()

# 2. Fetch events from Compass
compass_client = CompassClient(
    base_url="https://your-compass.edu.au",
    username=username,
    password=password
)
compass_client.login()

start = datetime.now().strftime("%Y-%m-%d")
end = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
raw_events = compass_client.get_calendar_events(start, end)
compass_client.close()

print(f"Fetched {len(raw_events)} raw events from Compass")

# 3. Filter with Claude
llm_filter = LLMFilter(api_key=os.getenv('CLAUDE_API_KEY'))

user_config = {
    'child_name': 'Emma',
    'school': 'Sample Primary School',
    'year_level': 'Year 3',
    'class': '3A',
    'interests': ['music', 'sports'],
    'filter_rules': 'Include Year 3 specific events and whole-school events.'
}

filtered_results = llm_filter.filter_events(raw_events, user_config)

# 4. Display relevant events
print("\n📅 Relevant Events for Emma:")
print("-" * 60)
for result in filtered_results:
    if result.get('is_relevant'):
        print(f"\n✓ {result['title']}")
        print(f"  Date: {result['date']}")
        print(f"  Reason: {result['reason']}")
        if result.get('action_needed'):
            print(f"  ⚠️  Action: {result['action_needed']}")
```

## Common Patterns

### Date Range Queries

```python
from datetime import datetime, timedelta

# Next 7 days
today = datetime.now()
start = today.strftime("%Y-%m-%d")
end = (today + timedelta(days=7)).strftime("%Y-%m-%d")
events = client.get_calendar_events(start, end)

# Specific date range
from dateutil import parser
start_date = parser.parse("2025-12-01").strftime("%Y-%m-%d")
end_date = parser.parse("2025-12-31").strftime("%Y-%m-%d")
events = client.get_calendar_events(start_date, end_date)
```

### Error Handling

```python
from src.adapters.compass import CompassClient

client = CompassClient(
    base_url="https://your-compass.edu.au",
    username="username",
    password="password"
)

try:
    client.login()
except Exception as e:
    print(f"Login failed: {e}")
    exit(1)

try:
    events = client.get_calendar_events("2025-11-22", "2025-12-06")
except Exception as e:
    print(f"Failed to fetch events: {e}")
finally:
    client.close()
```

### Switching Between Mock and Real

```python
# Configuration
USE_MOCK = True

if USE_MOCK:
    from src.adapters.compass_mock import CompassMockClient as CompassClientImpl
else:
    from src.adapters.compass import CompassClient as CompassClientImpl

# Use same interface
client = CompassClientImpl(base_url, username, password)
client.login()
events = client.get_calendar_events(start, end)
client.close()
```

## Event Structure Reference

Events returned from Compass have this structure:

```python
{
    'id': str,                          # Unique event ID
    'longTitle': str,                   # Full event title
    'longTitleWithoutTime': str,        # Title without time
    'start': str,                       # ISO format datetime
    'finish': str,                      # ISO format datetime
    'allDay': bool,                     # All-day event flag
    'subjectTitle': str,                # Short category (Excursion, Music, etc.)
    'subjectLongName': str,             # Full category name
    'locations': [{'name': str}, ...],  # Locations involved
    'managers': [{'name': str}, ...],   # Staff managing event
    'rollMarked': bool,                 # Attendance required
    'description': str                  # Additional details (permissions, costs, etc.)
}
```

## Environment Setup

```bash
# Create .env with required variables
cat > .env << 'EOF'
# Required
CLAUDE_API_KEY=sk-ant-...
BELLBIRD_ENCRYPTION_KEY=your_fernet_key_here

# Optional
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=sqlite:///./data/bellbird.db
EOF

# Install dependencies
poetry install --with dev
```

## Testing

Run the test suite:

```bash
# Full test with mock client
python test_compass_client.py

# With real credentials (after updating test_compass_client.py)
python test_compass_client.py --real-credentials
```

---

**For more details, see:**
- COMPASS_PYTHON_CLIENT_PLAN.md - Technical implementation details
- IMPLEMENTATION_SUMMARY.md - What was implemented
- CLAUDE.md - Project context and architecture
