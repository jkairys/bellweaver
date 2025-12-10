"""Unit tests for CompassClient."""

import json
from unittest.mock import Mock, patch, MagicMock

import pytest
import requests

from compass_client import CompassClient
from compass_client.exceptions import CompassAuthenticationError, CompassClientError


class TestCompassClientInit:
    """Tests for CompassClient initialization."""

    def test_init_basic(self):
        """Test basic initialization."""
        client = CompassClient("https://example.compass.education", "user", "pass")
        assert client.base_url == "https://example.compass.education"
        assert client.username == "user"
        assert client.password == "pass"
        assert client.session is not None
        assert client.user_id is None
        assert client.school_config_key is None
        assert client._authenticated is False

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from base_url."""
        client = CompassClient("https://example.compass.education/", "user", "pass")
        assert client.base_url == "https://example.compass.education"

    def test_init_sets_headers(self):
        """Test that session headers are set correctly."""
        client = CompassClient("https://example.compass.education", "user", "pass")
        assert "User-Agent" in client.session.headers
        assert "Mozilla" in client.session.headers["User-Agent"]
        assert client.session.headers["Accept-Language"] == "en-AU,en;q=0.9"


class TestCompassClientLogin:
    """Tests for CompassClient.login() method."""

    @patch("requests.Session")
    def test_login_success(self, mock_session_class):
        """Test successful login."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock login page response
        login_response = Mock()
        login_response.text = """
        <form>
            <input name="__VIEWSTATE" value="test_viewstate" />
            <input name="__VIEWSTATEGENERATOR" value="test_generator" />
            <input name="__EVENTVALIDATION" value="test_validation" />
        </form>
        """
        login_response.raise_for_status = Mock()

        # Mock post response (successful login)
        post_response = Mock()
        post_response.text = "redirect"
        post_response.raise_for_status = Mock()

        # Configure session mocks
        mock_session.get.return_value = login_response
        mock_session.post.return_value = post_response

        client = CompassClient("https://example.compass.education", "user", "pass")
        client.session = mock_session

        result = client.login()

        assert result is True
        assert mock_session.get.called
        assert mock_session.post.called

    @patch("requests.Session")
    def test_login_invalid_credentials(self, mock_session_class):
        """Test login with invalid credentials."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock login page response
        login_response = Mock()
        login_response.text = """
        <form>
            <input name="__VIEWSTATE" value="test_viewstate" />
        </form>
        """
        login_response.raise_for_status = Mock()

        # Mock post response (failed login)
        post_response = Mock()
        post_response.text = "Incorrect username or password"
        post_response.raise_for_status = Mock()

        mock_session.get.return_value = login_response
        mock_session.post.return_value = post_response

        client = CompassClient("https://example.compass.education", "user", "wrong_pass")
        client.session = mock_session

        with pytest.raises(CompassAuthenticationError) as exc_info:
            client.login()

        assert "Login failed" in str(exc_info.value)

    @patch("requests.Session")
    def test_login_network_error(self, mock_session_class):
        """Test login with network error."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock network error
        mock_session.get.side_effect = requests.exceptions.RequestException("Network error")

        client = CompassClient("https://example.compass.education", "user", "pass")
        client.session = mock_session

        with pytest.raises(CompassClientError) as exc_info:
            client.login()

        assert "Network error" in str(exc_info.value)


class TestCompassClientGetUserDetails:
    """Tests for CompassClient.get_user_details() method."""

    @patch("requests.Session")
    def test_get_user_details_success(self, mock_session_class):
        """Test successful retrieval of user details."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock API response
        api_response = Mock()
        api_response.json.return_value = {
            "d": {
                "userId": 12345,
                "username": "testuser",
                "firstName": "Test",
                "lastName": "User",
            }
        }
        api_response.raise_for_status = Mock()

        mock_session.get.return_value = api_response

        client = CompassClient("https://example.compass.education", "user", "pass")
        client.session = mock_session
        client._authenticated = True

        result = client.get_user_details()

        assert result["userId"] == 12345
        assert result["username"] == "testuser"
        assert client.user_id == 12345

    @patch("requests.Session")
    def test_get_user_details_not_authenticated(self, mock_session_class):
        """Test get_user_details when not authenticated."""
        client = CompassClient("https://example.compass.education", "user", "pass")
        client._authenticated = False

        with pytest.raises(CompassClientError) as exc_info:
            client.get_user_details()

        assert "not authenticated" in str(exc_info.value).lower()


class TestCompassClientGetCalendarEvents:
    """Tests for CompassClient.get_calendar_events() method."""

    @patch("requests.Session")
    def test_get_calendar_events_success(self, mock_session_class):
        """Test successful retrieval of calendar events."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock API response
        api_response = Mock()
        api_response.json.return_value = {
            "d": [
                {
                    "title": "Event 1",
                    "start": "2025-12-01T09:00:00",
                    "finish": "2025-12-01T10:00:00",
                },
                {
                    "title": "Event 2",
                    "start": "2025-12-02T14:00:00",
                    "finish": "2025-12-02T15:00:00",
                },
            ]
        }
        api_response.raise_for_status = Mock()

        mock_session.post.return_value = api_response

        client = CompassClient("https://example.compass.education", "user", "pass")
        client.session = mock_session
        client._authenticated = True
        client.user_id = 12345

        result = client.get_calendar_events("2025-12-01", "2025-12-31", 100)

        assert len(result) == 2
        assert result[0]["title"] == "Event 1"
        assert result[1]["title"] == "Event 2"

    @patch("requests.Session")
    def test_get_calendar_events_not_authenticated(self, mock_session_class):
        """Test get_calendar_events when not authenticated."""
        client = CompassClient("https://example.compass.education", "user", "pass")
        client._authenticated = False

        with pytest.raises(CompassClientError) as exc_info:
            client.get_calendar_events("2025-12-01", "2025-12-31", 100)

        assert "not authenticated" in str(exc_info.value).lower()

    @patch("requests.Session")
    def test_get_calendar_events_empty_response(self, mock_session_class):
        """Test get_calendar_events with empty response."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock empty API response
        api_response = Mock()
        api_response.json.return_value = {"d": []}
        api_response.raise_for_status = Mock()

        mock_session.post.return_value = api_response

        client = CompassClient("https://example.compass.education", "user", "pass")
        client.session = mock_session
        client._authenticated = True
        client.user_id = 12345

        result = client.get_calendar_events("2025-12-01", "2025-12-31", 100)

        assert result == []


class TestCompassClientHelpers:
    """Tests for CompassClient helper methods."""

    def test_extract_form_fields(self):
        """Test _extract_form_fields method."""
        html = """
        <form>
            <input name="field1" value="value1" />
            <input name="field2" value="value2" />
            <input type="checkbox" name="checkbox1" value="on" />
        </form>
        """

        client = CompassClient("https://example.compass.education", "user", "pass")
        result = client._extract_form_fields(html)

        assert "field1" in result
        assert result["field1"] == "value1"
        assert "field2" in result
        assert result["field2"] == "value2"

    def test_extract_form_fields_empty(self):
        """Test _extract_form_fields with no form fields."""
        html = "<div>No form here</div>"

        client = CompassClient("https://example.compass.education", "user", "pass")
        result = client._extract_form_fields(html)

        assert result == {}
