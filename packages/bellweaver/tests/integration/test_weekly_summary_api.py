"""
Integration tests for Weekly Summary API endpoint.

Tests POST /api/summary/weekly endpoint.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from bellweaver.api import create_app
from bellweaver.db.database import get_session, init_db, Base, get_engine


@pytest.fixture
def app():
    """Create Flask app for testing with isolated database."""
    app = create_app()
    app.config["TESTING"] = True

    # Use in-memory SQLite database for tests
    import os

    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["OPENAI_API_KEY"] = "test-key"

    # Ensure encryption key is set for CredentialManager
    from cryptography.fernet import Fernet

    os.environ["BELLWEAVER_ENCRYPTION_KEY"] = Fernet.generate_key().decode()

    with app.app_context():
        # Initialize database schema
        init_db()

    yield app

    # Cleanup
    with app.app_context():
        session = get_session()
        session.close()
        engine = get_engine()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(app):
    """Create test client for API requests."""
    return app.test_client()


class TestWeeklySummaryAPI:
    """Tests for POST /api/summary/weekly endpoint."""

    def test_weekly_summary_missing_body(self, client):
        """Test that missing body returns 400."""
        response = client.post(
            "/api/summary/weekly",
            data="",
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_weekly_summary_invalid_date_not_monday(self, client):
        """Test that non-Monday dates are rejected."""
        payload = {"week_start": "2025-12-23"}  # Tuesday

        response = client.post(
            "/api/summary/weekly",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Monday" in data.get("message", "")

    def test_weekly_summary_invalid_date_format(self, client):
        """Test that invalid date format is rejected."""
        payload = {"week_start": "not-a-date"}

        response = client.post(
            "/api/summary/weekly",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_weekly_summary_no_children_returns_all_events(self, client):
        """Test that when no children exist, all events are returned."""
        payload = {"week_start": "2025-12-22"}  # Monday

        response = client.post(
            "/api/summary/weekly",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Should succeed but with a message about no children
        assert response.status_code == 200
        data = response.get_json()
        assert data["week_start"] == "2025-12-22"
        assert data["week_end"] == "2025-12-28"
        assert "No children configured" in data["summary"]
        assert data["children_included"] == []

    @patch("bellweaver.filtering.openai_summarizer.OpenAI")
    def test_weekly_summary_success_with_children(self, mock_openai_class, client):
        """Test successful weekly summary generation with children."""
        # First create a child
        child_payload = {
            "name": "Emma Johnson",
            "date_of_birth": "2015-06-15",
        }
        child_response = client.post(
            "/api/children",
            data=json.dumps(child_payload),
            content_type="application/json",
        )
        assert child_response.status_code == 201

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"relevant_events": [], "recurring_events": [], "highlights": [], "summary": "Test summary for the week"}'
                )
            )
        ]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Now request summary
        payload = {"week_start": "2025-12-22"}

        response = client.post(
            "/api/summary/weekly",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["week_start"] == "2025-12-22"
        assert data["week_end"] == "2025-12-28"
        assert data["summary"] == "Test summary for the week"
        assert "Emma Johnson" in data["children_included"]

        # Verify OpenAI was called
        mock_openai_class.assert_called_once()
        mock_client.chat.completions.create.assert_called_once()

    def test_weekly_summary_missing_api_key(self, client):
        """Test that missing API key returns appropriate error."""
        import os

        # Remove the API key
        original_key = os.environ.get("OPENAI_API_KEY")
        del os.environ["OPENAI_API_KEY"]

        try:
            # First create a child so we trigger the OpenAI path
            child_payload = {
                "name": "Test Child",
                "date_of_birth": "2015-06-15",
            }
            client.post(
                "/api/children",
                data=json.dumps(child_payload),
                content_type="application/json",
            )

            payload = {"week_start": "2025-12-22"}

            response = client.post(
                "/api/summary/weekly",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 400
            data = response.get_json()
            assert "OPENAI_API_KEY" in data.get("message", "")
        finally:
            # Restore the API key
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key

    def test_weekly_summary_response_structure(self, client):
        """Test that response has correct structure."""
        payload = {"week_start": "2025-12-22"}

        response = client.post(
            "/api/summary/weekly",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify all expected fields are present
        assert "week_start" in data
        assert "week_end" in data
        assert "relevant_events" in data
        assert "recurring_events" in data
        assert "highlights" in data
        assert "summary" in data
        assert "children_included" in data

        # Verify types
        assert isinstance(data["relevant_events"], list)
        assert isinstance(data["recurring_events"], list)
        assert isinstance(data["highlights"], list)
        assert isinstance(data["summary"], str)
        assert isinstance(data["children_included"], list)
