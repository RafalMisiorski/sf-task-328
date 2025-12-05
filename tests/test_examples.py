"""
Example Items CRUD Tests

Tests for full CRUD operations with authorization.

WHY: Ensures CRUD endpoints work correctly.
WHY: Validates authorization (users can only access their own data).
WHY: Tests error handling.

COPY THIS PATTERN when testing new entities!
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.models import User
from app.examples.models import ExampleItem


class TestCreateItem:
    """Tests for POST /api/v1/items endpoint."""

    def test_create_item_success(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test successfully creating an item."""
        response = client.post(
            "/api/v1/items",
            json={
                "title": "New Item",
                "description": "Test description",
                "is_completed": False
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()

        # Check response structure
        assert data["title"] == "New Item"
        assert data["description"] == "Test description"
        assert data["is_completed"] is False
        assert data["user_id"] == test_user.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_item_minimal(self, client: TestClient, auth_headers: dict):
        """Test creating item with minimal required fields."""
        response = client.post(
            "/api/v1/items",
            json={"title": "Minimal Item"},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()

        assert data["title"] == "Minimal Item"
        assert data["description"] is None  # Optional field
        assert data["is_completed"] is False  # Default value

    def test_create_item_no_auth(self, client: TestClient):
        """Test creating item without authentication (should fail)."""
        response = client.post(
            "/api/v1/items",
            json={"title": "New Item"}
        )

        assert response.status_code == 403  # No token

    def test_create_item_invalid_token(self, client: TestClient):
        """Test creating item with invalid token."""
        response = client.post(
            "/api/v1/items",
            json={"title": "New Item"},
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_create_item_missing_title(self, client: TestClient, auth_headers: dict):
        """Test creating item without required title field."""
        response = client.post(
            "/api/v1/items",
            json={"description": "No title"},
            headers=auth_headers
        )

        # Pydantic validation should reject this
        assert response.status_code == 422

    def test_create_item_empty_title(self, client: TestClient, auth_headers: dict):
        """Test creating item with empty title."""
        response = client.post(
            "/api/v1/items",
            json={"title": ""},
            headers=auth_headers
        )

        # Should fail validation (min_length=1)
        assert response.status_code == 422


class TestGetAllItems:
    """Tests for GET /api/v1/items endpoint."""

    def test_get_all_items_success(self, client: TestClient, auth_headers: dict, test_items: list[ExampleItem]):
        """Test getting all items for authenticated user."""
        response = client.get(
            "/api/v1/items",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should return all test items
        assert isinstance(data, list)
        assert len(data) == len(test_items)

        # Check first item structure
        assert "id" in data[0]
        assert "title" in data[0]
        assert "user_id" in data[0]

    def test_get_all_items_empty(self, client: TestClient, auth_headers: dict):
        """Test getting items when user has no items."""
        response = client.get(
            "/api/v1/items",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty list
        assert data == []

    def test_get_all_items_pagination(self, client: TestClient, auth_headers: dict, test_items: list[ExampleItem]):
        """Test pagination with skip and limit parameters."""
        # Get first 2 items
        response = client.get(
            "/api/v1/items?skip=0&limit=2",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Get next 2 items
        response = client.get(
            "/api/v1/items?skip=2&limit=2",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_all_items_no_auth(self, client: TestClient):
        """Test getting items without authentication."""
        response = client.get("/api/v1/items")

        assert response.status_code == 403

    def test_get_all_items_only_own_items(self, client: TestClient, test_db: Session, auth_headers: dict, test_user: User):
        """Test that user only sees their own items, not others'."""
        # Create another user with items
        other_user = User(
            email="other@example.com",
            hashed_password="somehash",
            is_active=True
        )
        test_db.add(other_user)
        test_db.commit()
        test_db.refresh(other_user)

        # Create items for other user
        other_item = ExampleItem(
            user_id=other_user.id,
            title="Other user's item",
            is_completed=False
        )
        test_db.add(other_item)
        test_db.commit()

        # Create item for test user
        test_item = ExampleItem(
            user_id=test_user.id,
            title="Test user's item",
            is_completed=False
        )
        test_db.add(test_item)
        test_db.commit()

        # Get items as test user
        response = client.get("/api/v1/items", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should only see own item
        assert len(data) == 1
        assert data[0]["title"] == "Test user's item"
        assert data[0]["user_id"] == test_user.id


class TestGetSingleItem:
    """Tests for GET /api/v1/items/{item_id} endpoint."""

    def test_get_item_success(self, client: TestClient, auth_headers: dict, test_item: ExampleItem):
        """Test getting a specific item by ID."""
        response = client.get(
            f"/api/v1/items/{test_item.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_item.id
        assert data["title"] == test_item.title
        assert data["description"] == test_item.description

    def test_get_item_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent item."""
        response = client.get(
            "/api/v1/items/99999",  # Non-existent ID
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_item_no_auth(self, client: TestClient, test_item: ExampleItem):
        """Test getting item without authentication."""
        response = client.get(f"/api/v1/items/{test_item.id}")

        assert response.status_code == 403

    def test_get_item_other_users_item(self, client: TestClient, test_db: Session, auth_headers: dict):
        """Test getting item that belongs to another user (should fail)."""
        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password="somehash",
            is_active=True
        )
        test_db.add(other_user)
        test_db.commit()
        test_db.refresh(other_user)

        # Create item for other user
        other_item = ExampleItem(
            user_id=other_user.id,
            title="Other user's item",
            is_completed=False
        )
        test_db.add(other_item)
        test_db.commit()
        test_db.refresh(other_item)

        # Try to access other user's item
        response = client.get(
            f"/api/v1/items/{other_item.id}",
            headers=auth_headers
        )

        # Should be forbidden (not authorized)
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()


class TestUpdateItem:
    """Tests for PUT /api/v1/items/{item_id} endpoint."""

    def test_update_item_success(self, client: TestClient, auth_headers: dict, test_item: ExampleItem):
        """Test successfully updating an item."""
        response = client.put(
            f"/api/v1/items/{test_item.id}",
            json={
                "title": "Updated Title",
                "description": "Updated description",
                "is_completed": True
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_item.id
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"
        assert data["is_completed"] is True

    def test_update_item_partial(self, client: TestClient, auth_headers: dict, test_item: ExampleItem):
        """Test updating only some fields (partial update)."""
        original_description = test_item.description

        response = client.put(
            f"/api/v1/items/{test_item.id}",
            json={"is_completed": True},  # Only update this field
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Updated field
        assert data["is_completed"] is True

        # Unchanged fields
        assert data["title"] == test_item.title
        assert data["description"] == original_description

    def test_update_item_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent item."""
        response = client.put(
            "/api/v1/items/99999",
            json={"title": "Updated"},
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_item_no_auth(self, client: TestClient, test_item: ExampleItem):
        """Test updating item without authentication."""
        response = client.put(
            f"/api/v1/items/{test_item.id}",
            json={"title": "Updated"}
        )

        assert response.status_code == 403

    def test_update_item_other_users_item(self, client: TestClient, test_db: Session, auth_headers: dict):
        """Test updating item that belongs to another user (should fail)."""
        # Create another user with an item
        other_user = User(
            email="other@example.com",
            hashed_password="somehash",
            is_active=True
        )
        test_db.add(other_user)
        test_db.commit()

        other_item = ExampleItem(
            user_id=other_user.id,
            title="Other's item",
            is_completed=False
        )
        test_db.add(other_item)
        test_db.commit()
        test_db.refresh(other_item)

        # Try to update other user's item
        response = client.put(
            f"/api/v1/items/{other_item.id}",
            json={"title": "Hacked"},
            headers=auth_headers
        )

        assert response.status_code == 403

    def test_update_item_invalid_data(self, client: TestClient, auth_headers: dict, test_item: ExampleItem):
        """Test updating item with invalid data."""
        response = client.put(
            f"/api/v1/items/{test_item.id}",
            json={"title": ""},  # Empty title (should fail validation)
            headers=auth_headers
        )

        assert response.status_code == 422


class TestDeleteItem:
    """Tests for DELETE /api/v1/items/{item_id} endpoint."""

    def test_delete_item_success(self, client: TestClient, test_db: Session, auth_headers: dict, test_item: ExampleItem):
        """Test successfully deleting an item."""
        item_id = test_item.id

        response = client.delete(
            f"/api/v1/items/{item_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify item was deleted from database
        deleted_item = test_db.query(ExampleItem).filter(ExampleItem.id == item_id).first()
        assert deleted_item is None

    def test_delete_item_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent item."""
        response = client.delete(
            "/api/v1/items/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_delete_item_no_auth(self, client: TestClient, test_item: ExampleItem):
        """Test deleting item without authentication."""
        response = client.delete(f"/api/v1/items/{test_item.id}")

        assert response.status_code == 403

    def test_delete_item_other_users_item(self, client: TestClient, test_db: Session, auth_headers: dict):
        """Test deleting item that belongs to another user (should fail)."""
        # Create another user with an item
        other_user = User(
            email="other@example.com",
            hashed_password="somehash",
            is_active=True
        )
        test_db.add(other_user)
        test_db.commit()

        other_item = ExampleItem(
            user_id=other_user.id,
            title="Other's item",
            is_completed=False
        )
        test_db.add(other_item)
        test_db.commit()
        test_db.refresh(other_item)

        # Try to delete other user's item
        response = client.delete(
            f"/api/v1/items/{other_item.id}",
            headers=auth_headers
        )

        assert response.status_code == 403

        # Verify item was NOT deleted
        still_exists = test_db.query(ExampleItem).filter(ExampleItem.id == other_item.id).first()
        assert still_exists is not None


class TestCompleteWorkflow:
    """Test complete workflow: register → login → create → update → delete."""

    def test_complete_workflow(self, client: TestClient):
        """Test complete user workflow from registration to item management."""
        # 1. Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "workflow@example.com",
                "password": "workflowpass123"
            }
        )
        assert register_response.status_code == 201

        # 2. Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "workflow@example.com",
                "password": "workflowpass123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create item
        create_response = client.post(
            "/api/v1/items",
            json={"title": "Workflow Item", "is_completed": False},
            headers=headers
        )
        assert create_response.status_code == 201
        item_id = create_response.json()["id"]

        # 4. Get all items
        get_all_response = client.get("/api/v1/items", headers=headers)
        assert get_all_response.status_code == 200
        assert len(get_all_response.json()) == 1

        # 5. Get single item
        get_one_response = client.get(f"/api/v1/items/{item_id}", headers=headers)
        assert get_one_response.status_code == 200
        assert get_one_response.json()["title"] == "Workflow Item"

        # 6. Update item
        update_response = client.put(
            f"/api/v1/items/{item_id}",
            json={"is_completed": True},
            headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["is_completed"] is True

        # 7. Delete item
        delete_response = client.delete(f"/api/v1/items/{item_id}", headers=headers)
        assert delete_response.status_code == 204

        # 8. Verify deletion
        get_after_delete = client.get("/api/v1/items", headers=headers)
        assert get_after_delete.status_code == 200
        assert len(get_after_delete.json()) == 0
