# Compass Authentication Strategies

This document summarizes the authentication approaches for the Compass Education API and their trade-offs.

## Overview

Compass Education uses ASP.NET forms-based authentication with complex client-side validation and security measures. We've explored two main strategies:

1. **Pure HTTP Requests** (`src/adapters/compass.py`)
2. **Browser Automation** (`src/adapters/compass_browser.py`)

## Strategy 1: Pure HTTP Requests (compass.py)

### Approach
- Uses Python `requests` library for HTTP requests
- Parses HTML forms to extract ASP.NET ViewState and other hidden fields
- Simulates browser headers (User-Agent, Accept, etc.)
- Manages cookies in a requests.Session

### Advantages
- ✅ Fast - no browser overhead
- ✅ Low memory usage
- ✅ Simple dependencies (requests, beautifulsoup4)
- ✅ Easy to debug (just HTTP traffic)
- ✅ Works great for well-designed APIs

### Disadvantages
- ❌ Compass appears to use anti-bot detection (Cloudflare, fingerprinting)
- ❌ Form submission may require undocumented fields
- ❌ Difficult to handle JavaScript-based validation
- ❌ May get rate-limited or blocked by bot detection

### Status
- Partial success: Works for initial browser header detection, but login form submission fails
- Tests mostly skip or fail with login errors
- Root cause: Compass tracks request patterns and blocks automated submissions

### When to Use
- If you have a direct API endpoint that doesn't require HTML form submission
- If you can get Compass to allowlist your IP/user-agent
- For read-only operations after successful authentication

## Strategy 2: Browser Automation (compass_browser.py)

### Approach
- Uses Playwright for full browser automation
- Renders JavaScript and handles dynamic content
- Submits forms through user interaction simulation
- Maintains full browser context (cookies, storage, etc.)

### Advantages
- ✅ Handles JavaScript-heavy pages
- ✅ Looks like a real user to bot detection
- ✅ Can handle complex multi-step authentication
- ✅ Works with modern web security measures
- ✅ More reliable for production systems

### Disadvantages
- ❌ Slow - significant overhead per request (~10-15 seconds for login)
- ❌ High memory usage - needs full browser instance
- ❌ More complex to debug (need screenshots, etc.)
- ❌ Additional dependencies (Playwright)
- ❌ Browser binaries required (200MB+)
- ❌ Harder to distribute/deploy
- ❌ Can't easily run multiple instances in parallel

### Status
- In development: Playwright browser instance works, but Compass still rejects login
- Tests fail with navigation timeout
- Root cause: May need additional JavaScript interception or Cloudflare challenge handling

### When to Use
- For reliable production authentication when API access isn't available
- When you need to scrape pages with heavy JavaScript
- For integrations that need to be 100% reliable
- When you have the infrastructure to run browsers

## Current Issues

### Compass Bot Detection
Both approaches are hitting bot detection/anti-automation measures:
- Cloudflare protection (cf_clearance cookie handling)
- Request fingerprinting (browserFingerprint field)
- User-agent and header validation
- Rate limiting on failed login attempts

### What We've Learned
From your curl command, we can see the real login involves:
1. Cloudflare bypass (cf_clearance cookie)
2. ASP.NET ViewState (large encoded string)
3. __VIEWSTATEGENERATOR (cryptographic hash)
4. __EVENTTARGET and __EVENTARGUMENT (postback mechanism)
5. browserFingerprint (client-side fingerprinting)
6. Specific headers (sec-fetch-*, priority, etc.)
7. Previous cookies (cpsdid, username, session cookies)

## Recommended Solutions

### Option A: Use Playwright (Recommended for MVP)
If you need to support Compass logins:

```python
from src.adapters.compass_browser import CompassBrowserClient

client = CompassBrowserClient(
    base_url="https://seaford-northps-vic.compass.education",
    username="your_username",
    password="your_password"
)
client.login()
events = client.get_calendar_events("2025-01-01", "2025-01-31")
client.close()
```

**Setup:**
```bash
poetry add --group dev playwright
poetry run playwright install
```

**Trade-offs:**
- More reliable than HTTP requests
- Slower and heavier weight
- Works in development; may need adjustment for production

### Option B: Manual Authentication
Ask users to:
1. Log into Compass manually in a browser
2. Export their session cookies
3. Use cookies for API requests

This shifts the burden to users but completely avoids bot detection.

### Option C: Contact Compass Support
- Request API credentials for programmatic access
- Ask about official integration options
- Inquire about whitelisting your application

### Option D: Mock/Test Implementation
For development and testing:
- Use `CompassMockClient` which returns synthetic data
- No authentication required
- Same interface as real client
- See `src/adapters/compass_mock.py`

```python
from src.adapters.compass_mock import CompassMockClient

client = CompassMockClient()
events = client.get_calendar_events("2025-01-01", "2025-01-31")
# Returns 15-20 realistic test events
```

## Next Steps

### Immediate (for testing)
1. Use CompassMockClient for development
2. Write tests against mock data
3. Test the filtering and API layers

### Short Term
1. Try browser automation with Playwright if you need real data
2. Monitor for Cloudflare challenge detection
3. Consider adding proxy rotation if needed

### Long Term
1. Consider contacting Compass for official API access
2. Evaluate if you can switch to schools with better API support
3. Implement caching to reduce authentication frequency

## Testing

### Run Tests Without Authentication
```bash
# Uses mock client - no credentials needed
poetry run pytest tests/test_compass_client_mock.py -v
```

### Run Tests With Real Compass
```bash
# Requires COMPASS_USERNAME and COMPASS_PASSWORD in .env
poetry run pytest tests/test_compass_client_real.py -v
```

### Run Browser Tests
```bash
# Requires Playwright browsers installed
poetry run playwright install
poetry run pytest tests/test_compass_browser_client.py -v
```

## File References

- **HTTP Requests:** `src/adapters/compass.py`
- **Browser Automation:** `src/adapters/compass_browser.py`
- **Mock Client:** `src/adapters/compass_mock.py`
- **Real API Tests:** `tests/test_compass_client_real.py`
- **Browser Tests:** `tests/test_compass_browser_client.py`
- **Mock Tests:** `tests/test_compass_client_mock.py` (if created)

## Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [ASP.NET ViewState](https://learn.microsoft.com/en-us/previous-versions/z1hkazw7(v=vs.100))
- [Compass Education](https://www.compass.education/)
- [Cloudflare Bot Management](https://www.cloudflare.com/products/bot-management/)

## Conclusion

The Compass Education platform has strong anti-automation measures in place. For a production system, consider either:

1. **Using browser automation** (Playwright) - works but has overhead
2. **Getting official API access** from Compass - ideal if available
3. **Using mock data** during development - low friction for MVP

The pure HTTP request approach works well for educational purposes and simple APIs, but Compass specifically requires either browser automation or insider knowledge of their security implementation.
