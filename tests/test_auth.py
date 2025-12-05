"""
Authentication Tests

Tests for user registration, login, and authentication endpoints.

WHY: Ensures authentication works correctly.
WHY: Tests security features (password hashing, JWT).
WHY: Validates error handling.

COPY THIS PATTERN for your feature tests!
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.security import verify_password


class TestRegistration:
    """Tests for POST /api/v1/auth/register endpoint."""

    def test_register_success(self, client: TestClient, test_db: Session):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123"
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Check response structure
        assert "id" in data
        assert data["email"] == "newuser@example.com"
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "created_at" in data

        # Ensure password is NOT in response
        assert "password" not in data
        assert "hashed_password" not in data

        # Verify user was created in database
        user = test_db.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.email == "newuser@example.com"

        # Verify password was hashed
        assert user.hashed_password != "securepassword123"
        assert verify_password("securepassword123", user.hashed_password)

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with existing email (should fail)."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,  # Already exists
                "password": "anotherpassword123"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepassword123"
            }
        )

        # Pydantic validation should reject this
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        """Test registration with password too short."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "short"  # Less than 8 characters
            }
        )

        # Pydantic validation should reject this
        assert response.status_code == 422

    def test_register_missing_fields(self, client: TestClient):
        """Test registration with missing required fields."""
        # Missing password
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "newuser@example.com"}
        )
        assert response.status_code == 422

        # Missing email
        response = client.post(
            "/api/v1/auth/register",
            json={"password": "securepassword123"}
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login endpoint."""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check JWT token in response
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent email."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword"
            }
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_inactive_user(self, client: TestClient, test_db: Session):
        """Test login with inactive user account."""
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            hashed_password="somehash",
            is_active=False
        )
        test_db.add(inactive_user)
        test_db.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "inactive@example.com",
                "password": "somepassword"
            }
        )

        # Should fail before checking password (inactive check comes first)
        assert response.status_code in [401, 403]

    def test_login_invalid_email_format(self, client: TestClient):
        """Test login with invalid email format."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "not-an-email",
                "password": "somepassword"
            }
        )

        # Pydantic validation should reject this
        assert response.status_code == 422

    def test_login_missing_fields(self, client: TestClient):
        """Test login with missing required fields."""
        # Missing password
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 422

        # Missing email
        response = client.post(
            "/api/v1/auth/login",
            json={"password": "somepassword"}
        )
        assert response.status_code == 422


class TestGetCurrentUser:
    """Tests for GET /api/v1/auth/me endpoint."""

    def test_get_current_user_success(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test getting current user info with valid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check response matches test user
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["is_active"] == test_user.is_active
        assert data["is_superuser"] == test_user.is_superuser

        # Ensure password is NOT in response
        assert "password" not in data
        assert "hashed_password" not in data

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without auth token (should fail)."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403  # FastAPI HTTPBearer returns 403

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401

    def test_get_current_user_expired_token(self, client: TestClient):
        """Test getting current user with expired token."""
        # Create token with negative expiration (already expired)
        from datetime import timedelta
        from app.core.security import create_access_token

        expired_token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(seconds=-1)  # Expired 1 second ago
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    def test_get_current_user_malformed_header(self, client: TestClient):
        """Test getting current user with malformed Authorization header."""
        # Missing "Bearer" prefix
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "some_token"}
        )

        assert response.status_code == 403

    def test_get_current_user_deleted_user(self, client: TestClient, test_db: Session, auth_headers: dict, test_user: User):
        """Test getting current user after user is deleted."""
        # Get valid token
        # (auth_headers fixture already created it)

        # Delete user from database
        test_db.delete(test_user)
        test_db.commit()

        # Try to use token
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        # Should fail because user no longer exists
        assert response.status_code == 401


class TestSecurity:
    """Tests for security features."""

    def test_password_is_hashed(self, client: TestClient, test_db: Session):
        """Test that passwords are hashed, not stored as plain text."""
        # Register new user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "secure@example.com",
                "password": "mysecretpassword"
            }
        )

        # Get user from database
        user = test_db.query(User).filter(User.email == "secure@example.com").first()

        # Password should be hashed, not plain text
        assert user.hashed_password != "mysecretpassword"
        assert user.hashed_password.startswith("$2b$")  # bcrypt hash prefix

    def test_jwt_contains_user_email(self, client: TestClient, test_user: User):
        """Test that JWT token contains user email in 'sub' claim."""
        # Login to get token
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )

        token = response.json()["access_token"]

        # Decode token (without verification for testing)
        from jose import jwt
        from app.core.config import settings

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

        # Check 'sub' claim contains email
        assert payload["sub"] == "test@example.com"
        assert "exp" in payload  # Expiration time

    def test_different_passwords_different_hashes(self, client: TestClient, test_db: Session):
        """Test that same password for different users gets different hashes."""
        # Register two users with same password
        client.post(
            "/api/v1/auth/register",
            json={"email": "user1@example.com", "password": "samepassword"}
        )
        client.post(
            "/api/v1/auth/register",
            json={"email": "user2@example.com", "password": "samepassword"}
        )

        # Get users from database
        user1 = test_db.query(User).filter(User.email == "user1@example.com").first()
        user2 = test_db.query(User).filter(User.email == "user2@example.com").first()

        # Hashes should be different (bcrypt uses salt)
        assert user1.hashed_password != user2.hashed_password
