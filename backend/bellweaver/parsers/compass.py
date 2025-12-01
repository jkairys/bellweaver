"""
Parser for Compass API responses.

This module provides a parsing layer between raw API responses (dicts) and
validated Pydantic models. It separates concerns:
- Adapters handle HTTP communication and return raw dicts
- Parsers handle validation and transformation into domain models
- Application code works with type-safe, validated models

Example usage:
    >>> from bellweaver.adapters.compass import CompassClient
    >>> from bellweaver.parsers.compass import CompassParser
    >>>
    >>> client = CompassClient(base_url, username, password)
    >>> client.login()
    >>>
    >>> # Get raw data from adapter
    >>> raw_events = client.get_calendar_events("2025-01-01", "2025-01-31")
    >>>
    >>> # Parse into validated models
    >>> events = CompassParser.parse_events(raw_events)
    >>> for event in events:
    ...     print(f"{event.title} at {event.start}")
"""

from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from bellweaver.models.compass import CompassEvent, CompassUser


class CompassParseError(Exception):
    """Raised when parsing Compass API response fails."""

    def __init__(self, message: str, raw_data: Any = None, validation_errors: Optional[List[Any]] = None):
        """
        Initialize parse error with context.

        Args:
            message: Human-readable error message
            raw_data: The raw data that failed to parse
            validation_errors: Pydantic validation errors if available
        """
        super().__init__(message)
        self.raw_data = raw_data
        self.validation_errors = validation_errors


class CompassParser:
    """
    Parser for Compass Education API responses.

    Transforms raw API responses (dicts) into validated Pydantic models.
    Provides clear separation between HTTP communication and data validation.
    """

    @staticmethod
    def parse_event(raw: Dict[str, Any]) -> CompassEvent:
        """
        Parse and validate a single calendar event.

        Args:
            raw: Raw event dictionary from Compass API

        Returns:
            Validated CompassEvent model

        Raises:
            CompassParseError: If validation fails
        """
        try:
            return CompassEvent.model_validate(raw)
        except ValidationError as e:
            raise CompassParseError(
                f"Failed to parse Compass event: {e.error_count()} validation error(s)",
                raw_data=raw,
                validation_errors=e.errors(),
            ) from e

    @staticmethod
    def parse_events(raw_list: List[Dict[str, Any]]) -> List[CompassEvent]:
        """
        Parse and validate multiple calendar events.

        Args:
            raw_list: List of raw event dictionaries from Compass API

        Returns:
            List of validated CompassEvent models

        Raises:
            CompassParseError: If any event fails validation

        Note:
            Stops at first validation error. For partial parsing with error handling,
            use parse_events_safe() instead.
        """
        try:
            return [CompassEvent.model_validate(event) for event in raw_list]
        except ValidationError as e:
            # Find which event failed (if possible)
            for idx, event in enumerate(raw_list):
                try:
                    CompassEvent.model_validate(event)
                except ValidationError:
                    raise CompassParseError(
                        f"Failed to parse Compass event at index {idx}: {e.error_count()} validation error(s)",
                        raw_data=event,
                        validation_errors=e.errors(),
                    ) from e
            # If we can't find the specific event, raise generic error
            raise CompassParseError(
                f"Failed to parse Compass events: {e.error_count()} validation error(s)",
                raw_data=raw_list,
                validation_errors=e.errors(),
            ) from e

    @staticmethod
    def parse_events_safe(
        raw_list: List[Dict[str, Any]], skip_invalid: bool = True
    ) -> tuple[List[CompassEvent], List[CompassParseError]]:
        """
        Parse calendar events with error handling for individual items.

        Args:
            raw_list: List of raw event dictionaries from Compass API
            skip_invalid: If True, skip invalid events and continue parsing.
                         If False, collect errors but parse all valid events.

        Returns:
            Tuple of (valid_events, errors):
                - valid_events: List of successfully parsed CompassEvent models
                - errors: List of CompassParseError for failed events
        """
        valid_events: List[CompassEvent] = []
        errors: List[CompassParseError] = []

        for idx, raw_event in enumerate(raw_list):
            try:
                event = CompassEvent.model_validate(raw_event)
                valid_events.append(event)
            except ValidationError as e:
                error = CompassParseError(
                    f"Failed to parse event at index {idx}: {e.error_count()} validation error(s)",
                    raw_data=raw_event,
                    validation_errors=e.errors(),
                )
                errors.append(error)
                if not skip_invalid:
                    # Still collect the error but continue parsing
                    continue

        return valid_events, errors

    @staticmethod
    def parse_user(raw: Dict[str, Any]) -> CompassUser:
        """
        Parse and validate user details.

        Args:
            raw: Raw user details dictionary from Compass API

        Returns:
            Validated CompassUser model

        Raises:
            CompassParseError: If validation fails
        """
        try:
            return CompassUser.model_validate(raw)
        except ValidationError as e:
            raise CompassParseError(
                f"Failed to parse Compass user: {e.error_count()} validation error(s)",
                raw_data=raw,
                validation_errors=e.errors(),
            ) from e

    @staticmethod
    def parse_users(raw_list: List[Dict[str, Any]]) -> List[CompassUser]:
        """
        Parse and validate multiple user details.

        Args:
            raw_list: List of raw user dictionaries from Compass API

        Returns:
            List of validated CompassUser models

        Raises:
            CompassParseError: If any user fails validation
        """
        try:
            return [CompassUser.model_validate(user) for user in raw_list]
        except ValidationError as e:
            # Find which user failed (if possible)
            for idx, user in enumerate(raw_list):
                try:
                    CompassUser.model_validate(user)
                except ValidationError:
                    raise CompassParseError(
                        f"Failed to parse Compass user at index {idx}: {e.error_count()} validation error(s)",
                        raw_data=user,
                        validation_errors=e.errors(),
                    ) from e
            # If we can't find the specific user, raise generic error
            raise CompassParseError(
                f"Failed to parse Compass users: {e.error_count()} validation error(s)",
                raw_data=raw_list,
                validation_errors=e.errors(),
            ) from e
