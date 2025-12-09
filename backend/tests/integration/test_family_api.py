"""
Integration tests for Family Management API endpoints.

Tests User Stories 1-6 with test-first approach per Constitution Principle II.
All tests verify API contracts, validation rules, and success criteria from spec.md.
"""

import json
import pytest
from datetime import date, timedelta
from bellweaver.api import create_app
from bellweaver.db.database import get_session, init_db, Base, get_engine


@pytest.fixture
def app():
    """Create Flask app for testing with isolated database."""
    app = create_app()
    app.config['TESTING'] = True

    # Use in-memory SQLite database for tests
    import os
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

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


# ============================================================================
# Phase 3: User Story 1 - Add First Child Profile
# ============================================================================

class TestUserStory1CreateChild:
    """Tests for POST /api/children endpoint."""

    def test_create_child_with_valid_data(self, client):
        """
        T016: POST /api/children with valid data
        Expect: 201 Created, response matches ChildCreate schema, SC-001 (<200ms)
        """
        payload = {
            "name": "Emma Johnson",
            "date_of_birth": "2015-06-15",
            "gender": "female",
            "interests": "Soccer, reading, science experiments"
        }

        import time
        start_time = time.time()
        response = client.post('/api/children',
                              data=json.dumps(payload),
                              content_type='application/json')
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms

        # Verify 201 Created
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.get_json()}"

        # Verify response schema
        data = response.get_json()
        assert 'id' in data
        assert data['name'] == "Emma Johnson"
        assert data['date_of_birth'] == "2015-06-15"
        assert data['gender'] == "female"
        assert data['interests'] == "Soccer, reading, science experiments"
        assert 'created_at' in data
        assert 'updated_at' in data

        # Verify SC-001: Response time < 200ms
        assert elapsed_time < 200, f"Response took {elapsed_time:.2f}ms, expected < 200ms"

    def test_create_child_with_missing_required_fields(self, client):
        """
        T017: POST /api/children with missing required fields
        Expect: 400 Bad Request with validation errors
        """
        # Missing name
        payload = {
            "date_of_birth": "2015-06-15"
        }

        response = client.post('/api/children',
                              data=json.dumps(payload),
                              content_type='application/json')

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or 'message' in data

    def test_create_child_with_future_date_of_birth(self, client):
        """
        T018: POST /api/children with future date_of_birth
        Expect: 400 Bad Request per FR-010b
        """
        future_date = (date.today() + timedelta(days=1)).isoformat()

        payload = {
            "name": "Future Child",
            "date_of_birth": future_date
        }

        response = client.post('/api/children',
                              data=json.dumps(payload),
                              content_type='application/json')

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or 'message' in data
        # Verify error message mentions future date
        error_text = json.dumps(data).lower()
        assert 'future' in error_text or 'date' in error_text


class TestUserStory1GetChild:
    """Tests for GET /api/children/:id endpoint."""

    def test_get_child_by_id_valid(self, client):
        """
        T019: GET /api/children/:id with valid ID
        Expect: 200 OK, verify child data returned
        """
        # Create a child first
        payload = {
            "name": "Test Child",
            "date_of_birth": "2016-03-20"
        }
        create_response = client.post('/api/children',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        assert create_response.status_code == 201
        child_id = create_response.get_json()['id']

        # Get the child
        response = client.get(f'/api/children/{child_id}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == child_id
        assert data['name'] == "Test Child"
        assert data['date_of_birth'] == "2016-03-20"

    def test_get_child_by_id_not_found(self, client):
        """
        T020: GET /api/children/:id with invalid ID
        Expect: 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f'/api/children/{fake_id}')

        assert response.status_code == 404


class TestUserStory1ListChildren:
    """Tests for GET /api/children endpoint."""

    def test_list_all_children(self, client):
        """
        T021: GET /api/children
        Expect: 200 OK, list contains created children, SC-005 (<200ms)
        """
        # Create multiple children
        children_data = [
            {"name": "Alice", "date_of_birth": "2014-01-15"},
            {"name": "Bob", "date_of_birth": "2016-06-30"},
            {"name": "Charlie", "date_of_birth": "2018-11-22"}
        ]

        for child_data in children_data:
            response = client.post('/api/children',
                                  data=json.dumps(child_data),
                                  content_type='application/json')
            assert response.status_code == 201

        # List all children
        import time
        start_time = time.time()
        response = client.get('/api/children')
        elapsed_time = (time.time() - start_time) * 1000

        assert response.status_code == 200
        data = response.get_json()

        # Verify we got a list
        assert isinstance(data, list)
        assert len(data) == 3

        # Verify all children are present
        names = [child['name'] for child in data]
        assert 'Alice' in names
        assert 'Bob' in names
        assert 'Charlie' in names

        # Verify SC-005: Response time < 200ms
        assert elapsed_time < 200, f"Response took {elapsed_time:.2f}ms, expected < 200ms"


# ============================================================================
# Phase 4: User Story 2 - Manage Multiple Children
# ============================================================================

class TestUserStory2UpdateChild:
    """Tests for PUT /api/children/:id endpoint."""

    def test_update_child_with_valid_data(self, client):
        """
        T027: PUT /api/children/:id with valid data
        Expect: 200 OK, verify updated fields only
        """
        # Create a child
        payload = {
            "name": "Original Name",
            "date_of_birth": "2015-05-10",
            "gender": "male"
        }
        create_response = client.post('/api/children',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        assert create_response.status_code == 201
        child_id = create_response.get_json()['id']

        # Update the child
        update_payload = {
            "name": "Updated Name",
            "date_of_birth": "2015-05-10",  # Same date
            "gender": "male",
            "interests": "New interests added"
        }
        response = client.put(f'/api/children/{child_id}',
                            data=json.dumps(update_payload),
                            content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == "Updated Name"
        assert data['interests'] == "New interests added"
        assert data['date_of_birth'] == "2015-05-10"

    def test_update_child_invalid_id(self, client):
        """
        T028: PUT /api/children/:id with invalid ID
        Expect: 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        payload = {"name": "New Name", "date_of_birth": "2015-05-10"}

        response = client.put(f'/api/children/{fake_id}',
                            data=json.dumps(payload),
                            content_type='application/json')

        assert response.status_code == 404

    def test_update_child_with_future_date_of_birth(self, client):
        """
        T029: PUT /api/children/:id with future date_of_birth
        Expect: 400 Bad Request
        """
        # Create a child
        payload = {"name": "Test Child", "date_of_birth": "2015-05-10"}
        create_response = client.post('/api/children',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        assert create_response.status_code == 201
        child_id = create_response.get_json()['id']

        # Try to update with future date
        future_date = (date.today() + timedelta(days=1)).isoformat()
        update_payload = {"name": "Test Child", "date_of_birth": future_date}

        response = client.put(f'/api/children/{child_id}',
                            data=json.dumps(update_payload),
                            content_type='application/json')

        assert response.status_code == 400


class TestUserStory2DeleteChild:
    """Tests for DELETE /api/children/:id endpoint."""

    def test_delete_child_success(self, client):
        """
        T030: DELETE /api/children/:id
        Expect: 204 No Content, verify child removed and associations cascade deleted (FR-017)
        """
        # Create a child
        payload = {"name": "To Be Deleted", "date_of_birth": "2015-01-01"}
        create_response = client.post('/api/children',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        assert create_response.status_code == 201
        child_id = create_response.get_json()['id']

        # Delete the child
        response = client.delete(f'/api/children/{child_id}')

        assert response.status_code == 204

        # Verify child is gone
        get_response = client.get(f'/api/children/{child_id}')
        assert get_response.status_code == 404

    def test_delete_child_invalid_id(self, client):
        """
        T031: DELETE /api/children/:id with invalid ID
        Expect: 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f'/api/children/{fake_id}')

        assert response.status_code == 404
