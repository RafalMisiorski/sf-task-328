# FastAPI Patterns and Best Practices

This document explains the **patterns and architecture** used in this template.

**Purpose**: Prevent common mistakes (import loops, wrong structure, security issues).

---

## Table of Contents

1. [Three-Layer Architecture](#three-layer-architecture)
2. [Import Organization](#import-organization)
3. [Common Anti-Patterns](#common-anti-patterns)
4. [Authorization Pattern](#authorization-pattern)
5. [Error Handling Pattern](#error-handling-pattern)
6. [Testing Pattern](#testing-pattern)

---

## Three-Layer Architecture

This template uses a **strict three-layer architecture**:

```
┌─────────────────────────────────────────────┐
│              API Layer (FastAPI)            │
│         app/*/router.py                     │
│  - HTTP requests/responses                  │
│  - Endpoints (@app.get, @app.post, etc)     │
│  - Status codes (200, 201, 404, etc)        │
└─────────────────┬───────────────────────────┘
                  │ calls
                  ▼
┌─────────────────────────────────────────────┐
│         Validation Layer (Pydantic)         │
│         app/*/schemas.py                    │
│  - Request validation                       │
│  - Response serialization                   │
│  - Data types and constraints               │
└─────────────────┬───────────────────────────┘
                  │ validates
                  ▼
┌─────────────────────────────────────────────┐
│       Database Layer (SQLAlchemy)           │
│         app/*/models.py                     │
│  - ORM models (tables)                      │
│  - Relationships                            │
│  - Database constraints                     │
└─────────────────────────────────────────────┘
```

**Why this matters**: Each layer has ONE job. Don't mix them!

---

## Import Organization

### ✅ CORRECT Import Order

**In `models.py` (Database Layer)**:
```python
# 1. Standard library
from datetime import datetime, timezone

# 2. Third-party (SQLAlchemy)
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

# 3. Local (only core)
from app.core.database import Base

# ❌ NEVER import from app.auth.schemas
# ❌ NEVER import from app.*.router
```

**In `schemas.py` (Validation Layer)**:
```python
# 1. Standard library
from datetime import datetime
from typing import Optional

# 2. Third-party (Pydantic)
from pydantic import BaseModel, EmailStr, Field

# ❌ NEVER import from app.*.models
# ❌ NEVER import from app.*.router
# ✅ OK to import from other schemas if needed
```

**In `router.py` (API Layer)**:
```python
# 1. Standard library
from typing import List

# 2. Third-party (FastAPI)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# 3. Local imports - SAFE ORDER:
from app.core.database import get_db              # ← Core first
from app.auth.models import User                  # ← Models second
from app.auth.dependencies import get_current_user # ← Dependencies third
from app.todos.models import Todo                 # ← Other models fourth
from app.todos.schemas import (                   # ← Schemas LAST
    TodoCreate,
    TodoUpdate,
    TodoResponse
)

# ✅ This order prevents circular imports
```

---

### ❌ WRONG: Import Patterns That Cause Loops

**Don't do this**:
```python
# ❌ BAD: Importing schema from models.py
# File: app/todos/models.py
from app.todos.schemas import TodoCreate  # ← CIRCULAR IMPORT!

# ❌ BAD: Importing model from schemas.py
# File: app/todos/schemas.py
from app.todos.models import Todo  # ← CIRCULAR IMPORT!

# ❌ BAD: Importing router from anywhere
# File: app/todos/models.py
from app.todos.router import router  # ← NEVER DO THIS!
```

**Why**: This creates circular dependency: models.py → schemas.py → models.py

---

### 🔧 Rule of Thumb: Dependency Direction

```
router.py → schemas.py  ✅
router.py → models.py   ✅
models.py → Base        ✅
schemas.py → (nothing)  ✅

schemas.py → models.py  ❌
models.py → schemas.py  ❌
models.py → router.py   ❌
```

**Simple rule**: Imports flow **downward** in the three-layer stack, never upward.

---

## Common Anti-Patterns

### Anti-Pattern #1: Importing Schema into Model

**❌ WRONG**:
```python
# File: app/todos/models.py
from app.todos.schemas import TodoCreate  # ← NO!

class Todo(Base):
    @classmethod
    def from_schema(cls, schema: TodoCreate):
        ...
```

**✅ CORRECT**:
```python
# File: app/todos/models.py
# No schema imports!

class Todo(Base):
    # Just define the model
    ...

# File: app/todos/router.py
def create_todo(todo_data: TodoCreate, db: Session):
    new_todo = Todo(
        title=todo_data.title,
        description=todo_data.description,
        ...
    )
```

**Why**: Models should not know about schemas. Routers convert schemas to models.

---

### Anti-Pattern #2: Putting Business Logic in Models

**❌ WRONG**:
```python
# File: app/todos/models.py
class Todo(Base):
    def complete(self, db):
        self.is_completed = True
        db.commit()  # ← Business logic in model!
```

**✅ CORRECT**:
```python
# File: app/todos/router.py
def complete_todo(todo_id: int, db: Session, current_user: User):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    todo.is_completed = True  # ← Logic in router
    db.commit()
```

**Even better** (optional):
```python
# File: app/todos/service.py
def complete_todo(todo: Todo, db: Session) -> Todo:
    todo.is_completed = True
    db.commit()
    db.refresh(todo)
    return todo

# File: app/todos/router.py
def complete_todo_endpoint(todo_id: int, db: Session):
    todo = get_todo_or_404(todo_id, db)
    return service.complete_todo(todo, db)
```

---

### Anti-Pattern #3: Missing Authorization Checks

**❌ WRONG**:
```python
@router.get("/{todo_id}")
def get_todo(todo_id: int, db: Session):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    # ← Anyone can access anyone's todo!
    return todo
```

**✅ CORRECT**:
```python
@router.get("/{todo_id}")
def get_todo(todo_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    # ← Authorization check!
    if todo.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return todo
```

---

### Anti-Pattern #4: Not Using Pydantic for Validation

**❌ WRONG**:
```python
@router.post("/todos")
def create_todo(title: str, description: str, db: Session):
    # ← Manual validation, no auto-docs
    if not title or len(title) > 200:
        raise HTTPException(400, "Invalid title")
    ...
```

**✅ CORRECT**:
```python
@router.post("/todos", response_model=TodoResponse)
def create_todo(todo_data: TodoCreate, db: Session):
    # ← Pydantic validates automatically
    new_todo = Todo(**todo_data.model_dump())
    ...
```

---

## Authorization Pattern

**Every endpoint that accesses user data must check ownership.**

### Pattern: Authorization Helper

**Create helper function**:
```python
# File: app/todos/router.py

def get_todo_or_404(todo_id: int, current_user: User, db: Session) -> Todo:
    """
    Get todo by ID and verify ownership.

    Raises:
        HTTPException(404): Todo not found
        HTTPException(403): User doesn't own todo
    """
    todo = db.query(Todo).filter(Todo.id == todo_id).first()

    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )

    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this todo"
        )

    return todo
```

**Use in endpoints**:
```python
@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    todo = get_todo_or_404(todo_id, current_user, db)
    return todo

@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    todo = get_todo_or_404(todo_id, current_user, db)

    update_dict = todo_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(todo, field, value)

    db.commit()
    db.refresh(todo)
    return todo
```

**Why**: Reduces duplication, ensures consistent authorization checks.

---

## Error Handling Pattern

### Standard HTTP Status Codes

Use these consistently:

- **200 OK**: Successful GET, PUT
- **201 Created**: Successful POST (resource created)
- **204 No Content**: Successful DELETE
- **400 Bad Request**: Validation error (Pydantic handles this)
- **401 Unauthorized**: Not authenticated (no token or invalid token)
- **403 Forbidden**: Authenticated but not authorized (wrong user)
- **404 Not Found**: Resource doesn't exist
- **500 Internal Server Error**: Unexpected error

### Pattern: Consistent Error Responses

**All errors return JSON**:
```json
{
  "detail": "Error message here"
}
```

**Examples**:
```python
# 404 Not Found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Todo with id {todo_id} not found"
)

# 403 Forbidden
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not authorized to access this resource"
)

# 400 Bad Request (custom validation)
if len(title) > 200:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Title must be 200 characters or less"
    )
```

---

## Testing Pattern

### Pattern: Test Fixtures

**File**: `tests/conftest.py`

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.auth.models import User

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    yield db
    db.close()

@pytest.fixture
def client(test_db):
    """Create test client."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(test_db):
    """Create test user."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword"),
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def auth_headers(client, test_user):
    """Get authorization headers."""
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### Pattern: Testing CRUD Operations

**File**: `tests/test_todos.py`

```python
def test_create_todo(client, auth_headers):
    """Test creating a todo."""
    response = client.post(
        "/api/v1/todos",
        json={"title": "Test todo", "description": "Test description"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test todo"
    assert "id" in data

def test_get_todos(client, auth_headers, test_db, test_user):
    """Test getting all todos."""
    # Create test todo
    todo = Todo(user_id=test_user.id, title="Test", is_completed=False)
    test_db.add(todo)
    test_db.commit()

    # Get todos
    response = client.get("/api/v1/todos", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test"

def test_authorization(client, auth_headers, test_db):
    """Test that users can't access other users' todos."""
    # Create another user
    other_user = User(email="other@example.com", hashed_password=hash_password("pass"))
    test_db.add(other_user)
    test_db.commit()

    # Create todo for other user
    todo = Todo(user_id=other_user.id, title="Other's todo")
    test_db.add(todo)
    test_db.commit()

    # Try to access it
    response = client.get(f"/api/v1/todos/{todo.id}", headers=auth_headers)
    assert response.status_code == 403  # Forbidden
```

---

## Summary: Key Rules

1. **Three layers**: models.py → schemas.py → router.py
2. **Imports flow downward**: Never import upward (schemas ← models)
3. **Authorization**: Always check `item.user_id == current_user.id`
4. **Error handling**: Use standard HTTP status codes
5. **Testing**: Use fixtures for db, client, auth_headers
6. **DRY**: Extract common authorization checks into helpers

---

## When You Get Stuck

**Symptom**: Circular import error
**Fix**: Check import direction. Remove any upward imports.

**Symptom**: Tests fail with "table not found"
**Fix**: Ensure `Base.metadata.create_all()` is called in test setup.

**Symptom**: 401 Unauthorized on protected endpoint
**Fix**: Check that token is included in headers: `Authorization: Bearer <token>`

**Symptom**: Users can see each other's data
**Fix**: Add authorization check: `if item.user_id != current_user.id: raise 403`

---

**Next**: See `ARCHITECTURE.md` for overall system design.
