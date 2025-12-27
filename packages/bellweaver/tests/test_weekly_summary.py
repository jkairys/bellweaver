"""
Tests for weekly summary feature.

Tests the OpenAISummarizer class and models.
"""

import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from bellweaver.models.weekly_summary import (
    WeeklySummaryRequest,
    RelevantEvent,
    RecurringEventGroup,
    EventHighlight,
    WeeklySummaryResponse,
)
from bellweaver.filtering.openai_summarizer import OpenAISummarizer


class TestWeeklySummaryModels:
    """Tests for Pydantic models."""

    def test_weekly_summary_request_valid_monday(self):
        """Test that valid Monday dates are accepted."""
        req = WeeklySummaryRequest(week_start=date(2025, 12, 22))  # Monday
        assert req.week_start == date(2025, 12, 22)

    def test_weekly_summary_request_invalid_not_monday(self):
        """Test that non-Monday dates are rejected."""
        with pytest.raises(ValueError, match="Monday"):
            WeeklySummaryRequest(week_start=date(2025, 12, 23))  # Tuesday

    def test_weekly_summary_request_sunday_rejected(self):
        """Test that Sunday dates are rejected."""
        with pytest.raises(ValueError, match="Monday"):
            WeeklySummaryRequest(week_start=date(2025, 12, 21))  # Sunday

    def test_relevant_event_model(self):
        """Test RelevantEvent model creation."""
        event = RelevantEvent(
            id="event-123",
            title="School Assembly",
            start="2025-12-22T09:00:00",
            relevance_reason="Whole school event",
            child_name="Emma",
        )
        assert event.id == "event-123"
        assert event.title == "School Assembly"
        assert event.child_name == "Emma"

    def test_recurring_event_group_model(self):
        """Test RecurringEventGroup model creation."""
        group = RecurringEventGroup(
            pattern="Daily 9am Assembly",
            event_ids=["e1", "e2", "e3"],
            count=3,
        )
        assert group.pattern == "Daily 9am Assembly"
        assert len(group.event_ids) == 3
        assert group.count == 3

    def test_event_highlight_model(self):
        """Test EventHighlight model creation."""
        highlight = EventHighlight(
            id="event-456",
            title="School Excursion",
            why_notable="Annual zoo visit",
            action_needed="Pack lunch",
        )
        assert highlight.id == "event-456"
        assert highlight.action_needed == "Pack lunch"

    def test_weekly_summary_response_model(self):
        """Test WeeklySummaryResponse model creation."""
        response = WeeklySummaryResponse(
            week_start=date(2025, 12, 22),
            week_end=date(2025, 12, 28),
            relevant_events=[],
            recurring_events=[],
            highlights=[],
            summary="A quiet week with no major events.",
            children_included=["Emma", "Jack"],
        )
        assert response.week_start == date(2025, 12, 22)
        assert response.summary == "A quiet week with no major events."
        assert len(response.children_included) == 2


class TestOpenAISummarizer:
    """Tests for OpenAISummarizer class."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        with patch("bellweaver.filtering.openai_summarizer.OpenAI"):
            summarizer = OpenAISummarizer(api_key="test-key")
            assert summarizer.model == "gpt-4o-mini"

    @patch("bellweaver.filtering.openai_summarizer.OpenAI")
    def test_filter_and_summarize_success(self, mock_openai_class):
        """Test successful filtering and summarization."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"relevant_events": [], "recurring_events": [], "highlights": [], "summary": "Test summary"}'
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        summarizer = OpenAISummarizer(api_key="test-key")
        result = summarizer.filter_and_summarize(
            events=[],
            children=[{"name": "Test Child", "year_level": "5"}],
            week_start="2025-12-22",
            week_end="2025-12-28",
        )

        assert "summary" in result
        assert result["summary"] == "Test summary"
        assert result["relevant_events"] == []

    @patch("bellweaver.filtering.openai_summarizer.OpenAI")
    def test_filter_and_summarize_with_markdown_json(self, mock_openai_class):
        """Test parsing JSON from markdown code block."""
        # Mock OpenAI response with markdown JSON
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='Here is the result:\n```json\n{"relevant_events": [], "summary": "Markdown test"}\n```'
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        summarizer = OpenAISummarizer(api_key="test-key")
        result = summarizer.filter_and_summarize(
            events=[],
            children=[],
            week_start="2025-12-22",
            week_end="2025-12-28",
        )

        assert result["summary"] == "Markdown test"

    @patch("bellweaver.filtering.openai_summarizer.OpenAI")
    def test_filter_and_summarize_json_parsing_fallback(self, mock_openai_class):
        """Test fallback when JSON parsing fails."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Invalid JSON response"))
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        summarizer = OpenAISummarizer(api_key="test-key")
        result = summarizer.filter_and_summarize(
            events=[],
            children=[],
            week_start="2025-12-22",
            week_end="2025-12-28",
        )

        assert "raw_response" in result
        assert result["summary"] == "Unable to generate summary"

    @patch("bellweaver.filtering.openai_summarizer.OpenAI")
    def test_build_prompt_includes_children_info(self, mock_openai_class):
        """Test that prompt includes children information."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"relevant_events": [], "summary": "Test"}'
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        summarizer = OpenAISummarizer(api_key="test-key")
        summarizer.filter_and_summarize(
            events=[{"id": "1", "title": "Test Event"}],
            children=[
                {
                    "name": "Emma",
                    "year_level": "5",
                    "interests": "soccer",
                    "organisations": [{"name": "Test School"}],
                }
            ],
            week_start="2025-12-22",
            week_end="2025-12-28",
        )

        # Check that create was called with the right messages
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        user_message = messages[1]["content"]

        assert "Emma" in user_message
        assert "2025-12-22" in user_message
        assert "Test Event" in user_message
