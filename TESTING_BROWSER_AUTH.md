# Testing Playwright Browser Authentication

This guide explains how to test and debug the Compass browser-based authentication implementation.

## Quick Start

### Prerequisites
```bash
# Ensure Playwright browsers are installed
poetry run playwright install chromium

# Ensure credentials are in .env
cat .env | grep COMPASS_
```

You should see:
```
COMPASS_USERNAME=your_username
COMPASS_PASSWORD=your_password
```

### Run Tests

#### 1. Automated Test (Headless - Runs in Background)
```bash
poetry run python debug_browser_login.py
```

This runs silently in the background and outputs results to both console and `debug_browser_login.log`.

**Output:**
```
================================================================================
COMPASS BROWSER CLIENT DEBUG TEST
================================================================================
Username: KAI0002
Base URL: https://seaford-northps-vic.compass.education
Debug Mode: False
Headless: True

Step 1: Creating CompassBrowserClient...
✓ Client created successfully

Step 2: Testing login...
[browser automation logs...]

Step 3: Checking authentication cookies...
Current cookies: 7
  - cpsdid: ...
  - cf_clearance: ...
  ...

Step 4: Testing calendar event fetch...
✗ TEST FAILED: Failed to fetch calendar events
```

#### 2. Visual Debug Test (Shows Browser Window)
```bash
poetry run python debug_browser_login.py --debug
```

This opens a visible browser window so you can watch the login process step-by-step. Screenshots are saved to `debug_screenshots/` directory.

**Benefits:**
- Watch the login form being filled in real-time
- See Cloudflare challenges as they happen
- Visual confirmation of form submission
- Screenshots for diagnosis (in `debug_screenshots/`)

### Viewing Results

#### Console Output
Shows in real-time as test runs:
```bash
2025-11-23 16:27:39,469 - src.adapters.compass_browser - INFO - Submitting login form...
2025-11-23 16:27:39,472 - src.adapters.compass_browser - INFO - Found submit button, clicking it
2025-11-23 16:27:39,591 - src.adapters.compass_browser - INFO - Waiting for potential Cloudflare challenge...
```

#### Log File
Full persistent log saved to `debug_browser_login.log`:
```bash
tail -f debug_browser_login.log
```

#### Screenshots (Debug Mode Only)
Browse generated screenshots in `debug_screenshots/`:
```bash
ls -la debug_screenshots/
open debug_screenshots/02_login_page_loaded.png  # View specific screenshot
```

Screenshot sequence:
1. `01_navigation_failed.png` - If initial navigation fails
2. `02_login_page_loaded.png` - Login form visible
3. `03_cloudflare_challenge.png` - Cloudflare detected
4. `04_username_field_not_found.png` - If form fields not found
5. `05_form_filled.png` - After credentials filled
6. `06_submit_failed.png` - If submission fails
7. `07_navigation_timeout.png` - After navigation timeout
8. `08_after_login.png` - Final state after login attempt
9. `99_login_error.png` - If error occurs

## Current State

### ✅ What Works
- Browser launch and Playwright setup
- Navigation to Compass login page
- Cloudflare challenge detection and resolution
- Form field detection and filling
- Form submission
- Authentication cookie capture
- Session initialization API calls
- Comprehensive logging and debugging

### ❌ What Doesn't Work
- Login succeeds from user perspective but API calls still fail
- Still stuck on login page despite having auth cookies
- Calendar API returns HTML instead of JSON
- userId cannot be extracted from JavaScript context

**Root Cause**: Compass has strong bot detection that allows browser automation to appear successful (pass Cloudflare) but prevents actual API access. The session is not truly authenticated for API calls.

## Understanding the Debug Output

### Login Process

```
Step 1: Creating CompassBrowserClient...
✓ Client created successfully
```
✅ Client object created with your credentials.

```
Step 2: Testing login...
Launching browser (headless=True, debug=False)
Browser launched successfully
```
✅ Playwright browser started.

```
Navigating to login URL: https://seaford-northps-vic.compass.education/login.aspx?sessionstate=disabled
Login page loaded successfully
```
✅ Successfully navigated to login form.

```
Cloudflare challenge detected on login page
Waiting for Cloudflare challenge to be resolved...
Cloudflare challenge resolved
```
ℹ️ Cloudflare bot detection was encountered and resolved. This is normal.

```
Waiting for username field...
Username field found
```
✅ Login form found and is interactive.

```
Filling username: KAI0002
Filling password...
Checked 'remember me' checkbox
```
✅ Credentials filled in form.

```
Submitting login form...
Found submit button, clicking it
```
✅ Form submitted successfully.

```
Waiting for login navigation...
Navigation timeout or still on login page: Timeout 40000ms exceeded.
```
❌ **Critical Issue**: After form submission, still on login page. Despite having time (40+ seconds), the form submission didn't result in successful authentication.

```
Current cookies: ['cpsdid', '__cf_bm', '_cfuvid', 'cf_clearance', '_ga', '_gid', '_gat']
Auth cookies present, attempting to extract userId anyway...
```
ℹ️ We have authentication cookies, but they're not sufficient for API access. Compass requires additional state that we're not capturing.

### API Call

```
Step 4: Testing calendar event fetch...
Requesting events from 2025-11-23 to 2025-12-23...
Fetching calendar events from 2025-11-23 to 2025-12-23
```
Starting calendar fetch.

```
Calling API: https://seaford-northps-vic.compass.education/Services/Calendar.svc/GetCalendarEventsByUser?...
Payload: {'userId': 0, 'homePage': True, ...}
```
Attempting to call the API endpoint.

```
API Response: {'error': 'Unexpected token \'<\', "<!DOCTYPE "... is not valid JSON'}
```
❌ **API Error**: The API returned HTML (DOCTYPE element) instead of JSON. This indicates:
- The API request was not authenticated
- Server redirected to error/login page
- Our session is not valid for API calls

## Troubleshooting

### Issue: Username field not found
**Cause**: Cloudflare challenge not resolved, or page structure different
**Solution**:
1. Check `debug_screenshots/04_username_field_not_found.png`
2. Verify Compass login URL is correct in `.env`
3. Try with `--debug` flag to see browser visually

### Issue: Navigation timeout
**Cause**: Form submission rejected, invalid credentials, or bot detection
**Solution**:
1. Verify credentials in `.env` are correct
2. Test credentials manually in browser first
3. Check `debug_screenshots/07_navigation_timeout.png`
4. Try with `--debug` flag to see where form submission fails

### Issue: API returns HTML instead of JSON
**Cause**: Session is not authenticated for API calls
**Solution**:
1. This is the core issue - Compass blocks automated API access
2. See PLAYWRIGHT_AUTHENTICATION_DEBUG.md for analysis
3. Consider alternative approaches:
   - Use CompassMockClient for development
   - Implement user session cookie capture
   - Contact Compass for API access

## Using the Implementation in Code

### Headless Mode (Production)
```python
from src.adapters.compass_browser import CompassBrowserClient

client = CompassBrowserClient(
    base_url="https://compass.example.com",
    username="username",
    password="password"
    # debug=False is default
)

try:
    client.login()
    events = client.get_calendar_events("2025-01-01", "2025-01-31")
    print(f"Got {len(events)} events")
finally:
    client.close()
```

### Debug Mode (Development)
```python
from src.adapters.compass_browser import CompassBrowserClient

client = CompassBrowserClient(
    base_url="https://compass.example.com",
    username="username",
    password="password",
    debug=True,  # Enable debug mode
    headless=False  # Show browser window
)

try:
    client.login()  # Watch it happen in visible browser
    # Screenshots saved to debug_screenshots/
finally:
    client.close()
```

## Next Steps

1. **Try the test**: `poetry run python debug_browser_login.py --debug`
   - Watch the browser window
   - See exactly where login fails
   - Examine generated screenshots

2. **Review the logs**: `tail -f debug_browser_login.log`
   - Detailed trace of every step
   - Error messages with full context

3. **Check the analysis**: Read `PLAYWRIGHT_AUTHENTICATION_DEBUG.md`
   - Root cause analysis
   - Possible solutions
   - Recommendations

4. **Consider alternatives**:
   - Use `CompassMockClient` for MVP
   - Implement user session management
   - Contact Compass for official API access

## Configuration

### Environment Variables
```bash
# .env
COMPASS_USERNAME=your_username
COMPASS_PASSWORD=your_password
COMPASS_BASE_URL=https://seaford-northps-vic.compass.education
```

### Test Script Options
```bash
# Headless (no browser window shown)
poetry run python debug_browser_login.py

# Debug with visible browser
poetry run python debug_browser_login.py --debug

# View logs in real-time
tail -f debug_browser_login.log

# View all screenshots
ls -la debug_screenshots/
```

## Support

For more information, see:
- `COMPASS_AUTHENTICATION_STRATEGIES.md` - Authentication strategy overview
- `PLAYWRIGHT_AUTHENTICATION_DEBUG.md` - Detailed debugging analysis
- `src/adapters/compass_browser.py` - Implementation source code
- `debug_browser_login.py` - Test script source code
