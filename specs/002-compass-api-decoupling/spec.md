# Feature Specification: Compass API Decoupling and Mock Data Infrastructure

**Feature Branch**: `002-compass-api-decoupling`
**Created**: 2025-12-09
**Status**: Draft
**Input**: User description: "We need to completely decouple the compass API package from the Bell Weaver application because we are unable to test it or fetch data in get hub runners due to Geo blocking when I spin up the application I should be able to populate it with Sample data from the API so using mock dataserve the compass sink CI and point so that we can run the API as it would normally be run so I guess maybe have a mode where compass sink pulls from mock data rather than the real API and then everything else can run as per usual but make sure that the process of fetching and updating that mock data uses the real library and the mock data is committed to the code base probably stored in the Bell Weaver application. Separate out the getup workflows that test the compass API client library from the Bell Weaver application itself so that we only run test against the compass API library when Python files in that folder change."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Local Development with Sample Data (Priority: P1)

As a developer, I want to start the application locally with realistic sample data from Compass API without requiring actual Compass credentials, so that I can develop and test features immediately without access to a real Compass instance.

**Why this priority**: Enables local development workflow and unblocks developers who don't have Compass credentials or are working offline. This is the foundational capability that enables all other development activities.

**Independent Test**: Can be fully tested by starting the application in mock mode, verifying that sample data is loaded, and confirming that all API endpoints return data matching the expected Compass API schema without requiring real credentials.

**Acceptance Scenarios**:

1. **Given** the application is started with mock data mode enabled, **When** I request user data from the sync endpoint, **Then** I receive realistic sample data that matches the Compass API schema
2. **Given** the application is started with mock data mode enabled, **When** I request calendar events, **Then** I receive sample calendar events without needing Compass credentials
3. **Given** the application is running in mock mode, **When** I interact with any API endpoint, **Then** all functionality works identically to production mode except data comes from mock sources

---

### User Story 2 - CI/CD Pipeline Testing (Priority: P2)

As a DevOps engineer, I want CI/CD pipelines to run tests against the Bellweaver application without being blocked by geo-restrictions on Compass API, so that automated tests can verify application functionality in GitHub runners regardless of location.

**Why this priority**: Unblocks automated testing and enables continuous integration. Without this, the team cannot run automated tests in cloud environments, which significantly slows development velocity.

**Independent Test**: Can be fully tested by running the test suite in a GitHub runner with mock mode enabled and verifying all tests pass without making real Compass API calls.

**Acceptance Scenarios**:

1. **Given** tests are running in a GitHub runner, **When** the test suite executes with mock data mode, **Then** all tests pass without attempting to connect to Compass API
2. **Given** the CI pipeline is configured to use mock mode, **When** a pull request is created, **Then** automated tests complete successfully regardless of geo-location
3. **Given** tests are running against mock data, **When** API contract tests execute, **Then** they validate that responses match expected Compass API schemas

---

### User Story 3 - Mock Data Refresh (Priority: P3)

As a developer with Compass credentials, I want to refresh the committed mock data using the real Compass API, so that sample data stays current with actual API responses and schema changes.

**Why this priority**: Ensures mock data remains realistic and catches schema drift early. This is lower priority because it's needed less frequently and only by developers with Compass access.

**Independent Test**: Can be fully tested by running the mock data update command with real Compass credentials, verifying that new sample data is fetched and stored, and confirming that the updated data matches current API schemas.

**Acceptance Scenarios**:

1. **Given** I have valid Compass credentials, **When** I run the mock data update command, **Then** fresh sample data is fetched from the real Compass API and stored in the repository
2. **Given** the mock data has been refreshed, **When** the application runs in mock mode, **Then** it uses the newly updated sample data
3. **Given** the real Compass API schema has changed, **When** I refresh mock data, **Then** the updated mock data reflects the new schema and any validation failures are reported

---

### User Story 4 - Selective CI Workflow Execution (Priority: P4)

As a contributor, I want CI workflows for the Compass API library to run only when that library's code changes, so that pipelines execute faster and consume fewer resources.

**Why this priority**: Optimizes CI/CD resource usage and speeds up feedback loops. This is lower priority because it's an optimization rather than a functional requirement.

**Independent Test**: Can be fully tested by making changes to Bellweaver application code (not Compass library), triggering CI, and verifying that Compass API library tests are skipped while Bellweaver tests run.

**Acceptance Scenarios**:

1. **Given** I commit changes only to Bellweaver application code, **When** the CI pipeline runs, **Then** Compass API library tests are skipped
2. **Given** I commit changes to the Compass API library code, **When** the CI pipeline runs, **Then** both Compass API library tests and Bellweaver tests execute
3. **Given** I commit changes to both Compass library and Bellweaver code, **When** the CI pipeline runs, **Then** all test suites execute

---

### Edge Cases

- What happens when mock data files are missing or corrupted?
- How does the system handle switching between mock and real API modes during runtime?
- What happens when refreshing mock data fails due to authentication errors?
- How does the system behave when mock data schema doesn't match current application expectations?
- What happens when Compass API returns new fields that aren't in the mock data?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support a configuration mode that determines whether to use real Compass API or mock data sources
- **FR-002**: System MUST serve all existing API endpoints using mock data when running in mock mode
- **FR-003**: System MUST store mock data files in the application repository in a standard data format (JSON)
- **FR-004**: System MUST provide a command to update mock data by fetching fresh samples from the real Compass API using actual credentials
- **FR-005**: System MUST ensure mock data accurately represents real Compass API response schemas and data structures
- **FR-006**: System MUST allow developers to start the application locally with mock data without requiring Compass credentials
- **FR-007**: CI/CD pipelines MUST be able to run Bellweaver tests using mock data mode to avoid geo-blocking issues
- **FR-008**: System MUST separate CI workflows so Compass API library tests only run when Compass library code changes
- **FR-009**: System MUST separate CI workflows so Bellweaver application tests always run when application code changes
- **FR-010**: Mock data update process MUST use the real Compass API library to ensure consistency
- **FR-011**: System MUST validate that mock data matches expected schemas during application startup in mock mode
- **FR-012**: System MUST provide clear error messages when mock data is invalid or missing
- **FR-013**: Configuration mode MUST be settable via environment variables for deployment flexibility
- **FR-014**: System MUST maintain the same API contract whether running in mock or real mode
- **FR-015**: Mock data MUST include representative samples for all currently supported Compass API endpoints (user details, calendar events)

### Key Entities

- **Mock Data Store**: Collection of sample API responses stored as committed files in the repository, representing realistic Compass API data
- **Configuration Mode**: Application setting that determines data source (mock vs. real Compass API)
- **Compass API Library**: Separate package/module for Compass API integration that can be tested independently
- **Bellweaver Application**: Main application that consumes Compass data and should work with either real or mock sources

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can start the application locally with mock data and access all API endpoints without Compass credentials in under 30 seconds
- **SC-002**: CI/CD pipelines complete Bellweaver test suite successfully in GitHub runners without geo-blocking failures
- **SC-003**: Mock data can be refreshed using real Compass API and committed to repository in under 5 minutes
- **SC-004**: CI workflows for Compass API library execute only when Compass library files change, reducing unnecessary test runs by at least 70%
- **SC-005**: 100% of existing API endpoints function identically in both mock and real modes from the consumer perspective
- **SC-006**: Application startup time in mock mode is within 10% of startup time with real API connections
- **SC-007**: Zero authentication failures occur in CI pipelines when running in mock mode

## Assumptions

- Mock data will be stored in JSON format for readability and ease of maintenance
- Environment variable configuration is sufficient for mode switching (no UI configuration needed)
- Current Compass API schema is stable enough that mock data won't require frequent updates
- GitHub Actions is the CI/CD platform being used (for workflow path filtering)
- Mock data size will be reasonable enough to commit to repository (< 10MB)
- Developers updating mock data will have access to valid Compass credentials
- The Compass API library is or can be structured as a separate testable module
- Standard Python path filtering in GitHub workflows is sufficient for selective CI execution

## Dependencies

- Existing Compass API integration code must be refactorable to support mock mode
- CI/CD configuration must support conditional workflow execution based on file paths
- Application must support environment-based configuration for mode selection

## Scope

### In Scope

- Configuration mode for mock vs. real Compass API
- Mock data storage in repository
- Command to refresh mock data from real API
- CI workflow separation for Compass library vs. Bellweaver application
- Validation that mock data matches expected schemas
- Local development support with mock data

### Out of Scope

- UI for switching between mock and real modes (environment variables only)
- Mock data for Compass API endpoints not currently used by Bellweaver
- Automated mock data refresh (manual command only)
- Performance testing of mock vs. real API modes
- Mock data versioning or historical tracking
- Support for partial mock mode (all endpoints must use same mode)
- API recording/replay capabilities beyond simple mock data storage
