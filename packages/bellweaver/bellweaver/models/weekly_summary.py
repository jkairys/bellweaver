"""
Pydantic models for weekly summary feature.
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class WeeklySummaryRequest(BaseModel):
    """Request model for weekly summary API."""

    week_start: date = Field(..., description="Monday of the week to summarize")

    @field_validator("week_start")
    @classmethod
    def validate_is_monday(cls, v: date) -> date:
        """Validate that week_start is a Monday."""
        if v.weekday() != 0:  # 0 = Monday
            raise ValueError("week_start must be a Monday")
        return v


class RelevantEvent(BaseModel):
    """An event relevant to a child."""

    id: str
    title: str
    start: datetime
    end: Optional[datetime] = None
    relevance_reason: str
    child_name: str
    location: Optional[str] = None
    all_day: bool = False


class RecurringEventGroup(BaseModel):
    """A group of recurring events."""

    pattern: str
    event_ids: List[str]
    count: int


class EventHighlight(BaseModel):
    """A notable/unique event."""

    id: str
    title: str
    why_notable: str
    action_needed: Optional[str] = None


class WeeklySummaryResponse(BaseModel):
    """Response model for weekly summary API."""

    week_start: date
    week_end: date
    relevant_events: List[RelevantEvent]
    recurring_events: List[RecurringEventGroup]
    highlights: List[EventHighlight]
    summary: str
    children_included: List[str] = Field(
        default_factory=list, description="Names of children whose events are included"
    )
