"""
Test Configuration and Fixtures

This module provides pytest fixtures for testing.

WHY: Fixtures set up test environment (database, client, auth) automatically.
WHY: Each test gets a clean database (no interference between tests).
WHY: DRY principle - don't repeat setup code in every test.

COPY THIS PATTERN for your tests!
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.auth.models import User
from app.examples.models import ExampleItem


# Use in-memory SQLite for tests
# WHY: Fast (no disk I/O), isolated (each test gets fresh database)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db() -> Session:
    """
    Create test database and return session.

    WHY: Each test gets a clean database.
    WHY: In-memory SQLite is fast and isolated.
    WHY: Automatic cleanup (database deleted after test).

    Yields:
        Session: Database session for test

    Example:
        def test_something(test_db):
            user = User(email="test@example.com")
            test_db.add(user)
            test_db.commit()
    """
    # Create test engine
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    # Create session factory
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db: Session) -> TestClient:
    """
    Create test client with test database.

    WHY: TestClient simulates HTTP requests without running server.
    WHY: Dependency override replaces real database with test database.
    WHY: Each test gets isolated client.

    Args:
        test_db: Test database session (from test_db fixture)

    Returns:
        TestClient: FastAPI test client

    Example:
        def test_endpoint(client):
            response = client.get("/api/v1/items")
            assert response.status_code == 200
    """
    # Override get_db dependency to use test database
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    test_client = TestClient(app)

    yield test_client

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db: Session) -> User:
    """
    Create test user in database.

    WHY: Many tests need a user to authenticate.
    WHY: Fixture avoids repeating user creation in every test.

    Args:
        test_db: Test database session

    Returns:
        User: Created test user

    Example:
        def test_user_login(client, test_user):
            response = client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": "testpassword123"
            })
            assert response.status_code == 200
    """
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
        is_superuser=False
    )

    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    return user


@pytest.fixture
def test_superuser(test_db: Session) -> User:
    """
    Create test superuser (admin) in database.

    WHY: Some tests need admin privileges.
    WHY: Separate fixture from regular user.

    Args:
        test_db: Test database session

    Returns:
        User: Created test superuser

    Example:
        def test_admin_endpoint(client, test_superuser, auth_headers_superuser):
            response = client.delete("/api/v1/admin/users/1", headers=auth_headers_superuser)
            assert response.status_code == 200
    """
    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        is_active=True,
        is_superuser=True
    )

    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)

    return admin


@pytest.fixture
def auth_headers(client: TestClient, test_user: User) -> dict:
    """
    Get authorization headers with JWT token for test user.

    WHY: Protected endpoints require Authorization header.
    WHY: Fixture handles login and token extraction automatically.

    Args:
        client: Test client
        test_user: Test user (must exist in database)

    Returns:
        dict: Headers with Authorization: Bearer <token>

    Example:
        def test_protected_endpoint(client, auth_headers):
            response = client.get("/api/v1/items", headers=auth_headers)
            assert response.status_code == 200
    """
    # Login to get token
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 200, "Login failed in auth_headers fixture"

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_superuser(client: TestClient, test_superuser: User) -> dict:
    """
    Get authorization headers with JWT token for superuser.

    WHY: Admin endpoints require superuser token.

    Args:
        client: Test client
        test_superuser: Test superuser (must exist in database)

    Returns:
        dict: Headers with Authorization: Bearer <token>

    Example:
        def test_admin_only_endpoint(client, auth_headers_superuser):
            response = client.get("/api/v1/admin/stats", headers=auth_headers_superuser)
            assert response.status_code == 200
    """
    # Login as superuser
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "adminpassword123"
        }
    )

    assert response.status_code == 200, "Superuser login failed"

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_item(test_db: Session, test_user: User) -> ExampleItem:
    """
    Create test item in database.

    WHY: Many tests need an existing item to test GET/PUT/DELETE.
    WHY: Fixture avoids repeating item creation.

    Args:
        test_db: Test database session
        test_user: Owner of the item

    Returns:
        ExampleItem: Created test item

    Example:
        def test_get_item(client, auth_headers, test_item):
            response = client.get(f"/api/v1/items/{test_item.id}", headers=auth_headers)
            assert response.status_code == 200
            assert response.json()["title"] == test_item.title
    """
    item = ExampleItem(
        user_id=test_user.id,
        title="Test Item",
        description="Test description",
        is_completed=False
    )

    test_db.add(item)
    test_db.commit()
    test_db.refresh(item)

    return item


@pytest.fixture
def test_items(test_db: Session, test_user: User) -> list[ExampleItem]:
    """
    Create multiple test items in database.

    WHY: Test pagination, filtering, bulk operations.

    Args:
        test_db: Test database session
        test_user: Owner of the items

    Returns:
        list[ExampleItem]: List of created test items

    Example:
        def test_get_all_items(client, auth_headers, test_items):
            response = client.get("/api/v1/items", headers=auth_headers)
            assert response.status_code == 200
            assert len(response.json()) == len(test_items)
    """
    items = [
        ExampleItem(
            user_id=test_user.id,
            title=f"Test Item {i}",
            description=f"Description {i}",
            is_completed=(i % 2 == 0)  # Every other item is completed
        )
        for i in range(1, 6)  # Create 5 items
    ]

    for item in items:
        test_db.add(item)

    test_db.commit()

    for item in items:
        test_db.refresh(item)

    return items


# Helper function for tests (not a fixture)
def assert_valid_item_response(data: dict, expected_title: str = None):
    """
    Assert that response data is a valid item.

    WHY: Avoid repeating validation logic in every test.

    Args:
        data: Response JSON data
        expected_title: Optional expected title to check

    Example:
        response = client.post("/api/v1/items", json={"title": "New item"}, headers=auth_headers)
        assert_valid_item_response(response.json(), expected_title="New item")
    """
    assert "id" in data
    assert "title" in data
    assert "user_id" in data
    assert "is_completed" in data
    assert "created_at" in data
    assert "updated_at" in data

    if expected_title:
        assert data["title"] == expected_title
