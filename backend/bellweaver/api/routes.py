"""
Domain-specific route handlers for Bellweaver API.

This module contains all the route handlers organized by domain (users, events, etc.).
"""

from flask import Flask, jsonify, Blueprint
from sqlalchemy import select
from sqlalchemy.orm import Session

from bellweaver.db.database import get_db
from bellweaver.db.models import ApiPayload, Batch, Event, Child as DBChild
from bellweaver.models.compass import CompassUser, CompassEvent
from bellweaver.models.family import ChildCreate, ChildUpdate, Child as ChildResponse
from bellweaver.parsers.compass import CompassParser
import uuid
from datetime import datetime

# Create blueprint for user-related routes
user_bp = Blueprint("users", __name__, url_prefix="/api/user")

# Create blueprint for events-related routes
events_bp = Blueprint("events", __name__, url_prefix="/api/events")

# Create blueprint for family management routes
family_bp = Blueprint("family", __name__, url_prefix="/api")


@user_bp.route("", methods=["GET"])
def get_user():
    """
    Get user details from the latest user batch.

    Fetches the most recent batch for the get_user_details method,
    retrieves all API payloads within that batch, and parses them
    using the CompassUser Pydantic model.

    Returns:
        JSON response with parsed user data or error message

    Example response (single user):
        {
            "batch_id": "uuid-string",
            "created_at": "2025-12-01T12:00:00Z",
            "user": {
                "user_id": 123,
                "user_full_name": "John Doe",
                "user_email": "john@example.com",
                ...
            }
        }

    Example response (multiple users - should be rare):
        {
            "batch_id": "uuid-string",
            "created_at": "2025-12-01T12:00:00Z",
            "users": [
                {...},
                {...}
            ]
        }
    """
    db: Session = next(get_db())
    try:
        # Find the latest batch for get_user_details method
        stmt = (
            select(Batch)
            .where(Batch.method_name == "get_user_details")
            .order_by(Batch.created_at.desc())
            .limit(1)
        )
        latest_batch = db.execute(stmt).scalar_one_or_none()

        if not latest_batch:
            return jsonify({"error": "No user batches found"}), 404

        # Get all API payloads for this batch
        stmt = select(ApiPayload).where(ApiPayload.batch_id == latest_batch.id)
        payloads = db.execute(stmt).scalars().all()

        if not payloads:
            return jsonify({"error": "No payloads found in batch"}), 404

        # Parse each payload using CompassUser model
        users = []
        for payload in payloads:
            raw_data = payload.get_payload()
            try:
                user = CompassParser.parse(CompassUser, raw_data)
                users.append(user.model_dump(mode="json"))
            except Exception as e:
                # Log error but continue processing other payloads
                print(f"Failed to parse payload {payload.id}: {e}")
                continue

        if not users:
            return jsonify({"error": "Failed to parse any user data"}), 500

        # Return single user or list depending on count
        response = {
            "batch_id": latest_batch.id,
            "created_at": latest_batch.created_at.isoformat(),
        }

        if len(users) == 1:
            response["user"] = users[0]
        else:
            response["users"] = users

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    finally:
        db.close()


@events_bp.route("", methods=["GET"])
def get_events():
    """
    Get normalized calendar events from the database.

    Fetches all Event records from the database, ordered by start date.
    These are platform-agnostic normalized events that have been processed
    from raw API payloads.

    Returns:
        JSON response with normalized event data or error message

    Example response:
        {
            "event_count": 42,
            "events": [
                {
                    "id": "uuid-string",
                    "title": "School Assembly",
                    "description": "Whole school assembly",
                    "start": "2025-12-05T09:00:00Z",
                    "end": "2025-12-05T10:00:00Z",
                    "location": "Main Hall",
                    "all_day": false,
                    "organizer": null,
                    "attendees": [],
                    "status": "EventScheduled",
                    "created_at": "2025-12-01T12:00:00Z",
                    "updated_at": "2025-12-01T12:00:00Z"
                },
                ...
            ]
        }

    Note:
        If no events are found, this may indicate that the 'compass process'
        command hasn't been run yet. Raw API data needs to be processed
        into Event models first.
    """
    db: Session = next(get_db())
    try:
        # Get all events ordered by start date
        stmt = (
            select(Event)
            .order_by(Event.start.asc())
        )
        events = db.execute(stmt).scalars().all()

        if not events:
            return jsonify({
                "error": "No events found",
                "hint": "Run 'poetry run bellweaver compass process' to process raw API data into events"
            }), 404

        # Convert Event ORM models to JSON
        event_list = []
        for event in events:
            event_dict = {
                "id": event.id,
                "title": event.title,
                "start": event.start.isoformat(),
                "end": event.end.isoformat(),
                "description": event.description,
                "location": event.location,
                "all_day": event.all_day,
                "organizer": event.organizer,
                "attendees": event.attendees or [],
                "status": event.status,
                "created_at": event.created_at.isoformat(),
                "updated_at": event.updated_at.isoformat(),
            }
            event_list.append(event_dict)

        # Build response
        response = {
            "event_count": len(event_list),
            "events": event_list,
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    finally:
        db.close()


# ==================== FAMILY MANAGEMENT ENDPOINTS ====================

@family_bp.route("/children", methods=["POST"])
def create_child():
    """
    Create a new child profile.

    Request body should match ChildCreate schema:
        {
            "name": "Emma Johnson",
            "date_of_birth": "2015-06-15",
            "gender": "female",  # optional
            "interests": "Soccer, reading"  # optional
        }

    Returns:
        201: Child created successfully
        400: Validation error (missing fields, future date, etc.)
    """
    from flask import request
    db: Session = next(get_db())
    try:
        # Validate request data with Pydantic
        data = request.get_json()
        if not data:
            raise ValidationError("Request body is required", "MISSING_BODY")

        try:
            child_data = ChildCreate(**data)
        except Exception as e:
            raise ValidationError(str(e), "VALIDATION_ERROR")

        # Create ORM model
        child = DBChild(
            id=str(uuid.uuid4()),
            name=child_data.name,
            date_of_birth=child_data.date_of_birth,
            gender=child_data.gender,
            interests=child_data.interests,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(child)
        db.commit()
        db.refresh(child)

        # Return response using Pydantic model
        response = ChildResponse.model_validate(child)
        return jsonify(response.model_dump(mode="json")), 201

    except ValidationError:
        raise
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    finally:
        db.close()


@family_bp.route("/children/<child_id>", methods=["GET"])
def get_child(child_id: str):
    """
    Get a child profile by ID.

    Args:
        child_id: UUID of the child

    Returns:
        200: Child data
        404: Child not found
    """
    db: Session = next(get_db())
    try:
        stmt = select(DBChild).where(DBChild.id == child_id)
        child = db.execute(stmt).scalar_one_or_none()

        if not child:
            return jsonify({"error": "Child not found"}), 404

        response = ChildResponse.model_validate(child)
        return jsonify(response.model_dump(mode="json")), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    finally:
        db.close()


@family_bp.route("/children", methods=["GET"])
def list_children():
    """
    List all children.

    Returns:
        200: List of all children
    """
    db: Session = next(get_db())
    try:
        stmt = select(DBChild).order_by(DBChild.created_at.asc())
        children = db.execute(stmt).scalars().all()

        response = [ChildResponse.model_validate(child).model_dump(mode="json") for child in children]
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    finally:
        db.close()


@family_bp.route("/children/<child_id>", methods=["PUT"])
def update_child(child_id: str):
    """
    Update a child profile.

    Args:
        child_id: UUID of the child

    Request body should match ChildUpdate schema.

    Returns:
        200: Child updated successfully
        400: Validation error
        404: Child not found
    """
    from flask import request
    db: Session = next(get_db())
    try:
        # Find child
        stmt = select(DBChild).where(DBChild.id == child_id)
        child = db.execute(stmt).scalar_one_or_none()

        if not child:
            return jsonify({"error": "Child not found"}), 404

        # Validate request data
        data = request.get_json()
        if not data:
            raise ValidationError("Request body is required", "MISSING_BODY")

        try:
            update_data = ChildUpdate(**data)
        except Exception as e:
            raise ValidationError(str(e), "VALIDATION_ERROR")

        # Update fields
        child.name = update_data.name
        child.date_of_birth = update_data.date_of_birth
        child.gender = update_data.gender
        child.interests = update_data.interests
        child.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(child)

        response = ChildResponse.model_validate(child)
        return jsonify(response.model_dump(mode="json")), 200

    except ValidationError:
        raise
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    finally:
        db.close()


@family_bp.route("/children/<child_id>", methods=["DELETE"])
def delete_child(child_id: str):
    """
    Delete a child profile.

    Cascades to remove all child-organisation associations per FR-017.

    Args:
        child_id: UUID of the child

    Returns:
        204: Child deleted successfully
        404: Child not found
    """
    db: Session = next(get_db())
    try:
        stmt = select(DBChild).where(DBChild.id == child_id)
        child = db.execute(stmt).scalar_one_or_none()

        if not child:
            return jsonify({"error": "Child not found"}), 404

        db.delete(child)
        db.commit()

        return "", 204

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    finally:
        db.close()


# ==================== ERROR HANDLERS ====================

class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ConflictError(Exception):
    """Raised when a business rule conflict occurs."""

    def __init__(self, message: str, code: str = "CONFLICT_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


@family_bp.errorhandler(ValidationError)
def handle_validation_error(error: ValidationError):
    """Handle validation errors."""
    return jsonify({
        "error": "Validation Error",
        "message": error.message,
        "code": error.code
    }), 400


@family_bp.errorhandler(ConflictError)
def handle_conflict_error(error: ConflictError):
    """Handle conflict errors."""
    return jsonify({
        "error": "Conflict",
        "message": error.message,
        "code": error.code
    }), 409


def register_routes(app: Flask) -> None:
    """
    Register all route blueprints with the Flask application.

    Args:
        app: The Flask application instance
    """
    app.register_blueprint(user_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(family_bp)
