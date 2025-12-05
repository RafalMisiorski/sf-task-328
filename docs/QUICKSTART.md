# Quick Start Guide: Adding a New Entity

This guide shows you **exactly** how to add a new entity with full CRUD operations.

**Time to complete**: 10-15 minutes

**Pattern**: Copy from `app/examples/` module and adapt.

---

## Overview

The template includes **complete working examples** that you can copy:
- **Auth module** (`app/auth/`): User authentication with JWT
- **Examples module** (`app/examples/`): Full CRUD operations with authorization

**To add a new entity**, copy the Examples module and adapt it.

---

## Step-by-Step: Adding a "Todo" Entity

### Step 1: Create the Model (Database Layer)

**File**: `app/todos/models.py`

**Copy from**: `app/examples/models.py`

**Changes**:
```python
# 1. Rename class
class ExampleItem(Base):  → class Todo(Base):

# 2. Change table name
__tablename__ = "example_items"  → __tablename__ = "todos"

# 3. Update fields (keep user_id!)
title = Column(String(200), ...)       → title = Column(String(200), ...)
description = Column(Text, ...)        → description = Column(Text, ...)
is_completed = Column(Boolean, ...)    → is_completed = Column(Boolean, ...)
# Add/remove fields as needed

# 4. Update relationship name
owner = relationship("User", back_populates="items")
→ owner = relationship("User", back_populates="todos")
```

**✅ Checklist**:
- [ ] Class renamed (ExampleItem → Todo)
- [ ] `__tablename__` changed
- [ ] Fields match your requirements
- [ ] `user_id` foreign key kept (for authorization)
- [ ] Relationship name updated

---

### Step 2: Create the Schemas (API Layer)

**File**: `app/todos/schemas.py`

**Copy from**: `app/examples/schemas.py`

**Changes**:
```python
# 1. Rename all schemas
class ExampleItemBase       → class TodoBase
class ExampleItemCreate     → class TodoCreate
class ExampleItemUpdate     → class TodoUpdate
class ExampleItemResponse   → class TodoResponse

# 2. Update field names/types as needed
# 3. Keep the pattern: Base → Create → Update → Response
```

**✅ Checklist**:
- [ ] All 4 schemas renamed
- [ ] Fields match your model
- [ ] Create schema has required fields only
- [ ] Update schema has all fields optional
- [ ] Response schema includes id, timestamps, user_id

---

### Step 3: Create the Router (Endpoints Layer)

**File**: `app/todos/router.py`

**Copy from**: `app/examples/router.py`

**Changes**:
```python
# 1. Update imports
from app.examples.models import ExampleItem → from app.todos.models import Todo
from app.examples.schemas import ... → from app.todos.schemas import ...

# 2. Change router prefix
router = APIRouter(prefix="/items", tags=["items"])
→ router = APIRouter(prefix="/todos", tags=["todos"])

# 3. Replace ExampleItem with Todo throughout
db.query(ExampleItem) → db.query(Todo)
new_item = ExampleItem(...) → new_todo = Todo(...)

# 4. Update variable names for clarity
new_item → new_todo
item → todo
items → todos
item_data → todo_data
item_id → todo_id

# 5. Update error messages
"Item with id {item_id} not found" → "Todo with id {todo_id} not found"
```

**✅ Checklist**:
- [ ] Router prefix changed (/items → /todos)
- [ ] Tags changed (["items"] → ["todos"])
- [ ] All imports updated
- [ ] All variable names updated
- [ ] Authorization checks kept (`if todo.user_id != current_user.id`)
- [ ] All 5 endpoints present (POST, GET all, GET one, PUT, DELETE)

---

### Step 4: Update Database Initialization

**File**: `app/core/database.py`

**Add import in `init_db()` function**:
```python
def init_db() -> None:
    from app.auth import models as auth_models
    from app.examples import models as example_models
    from app.todos import models as todo_models  # ← ADD THIS

    Base.metadata.create_all(bind=engine)
```

**✅ Checklist**:
- [ ] Import added to `init_db()`

---

### Step 5: Add Relationship to User Model

**File**: `app/auth/models.py`

**Add relationship**:
```python
class User(Base):
    ...
    items = relationship("ExampleItem", back_populates="owner", cascade="all, delete-orphan")
    todos = relationship("Todo", back_populates="owner", cascade="all, delete-orphan")  # ← ADD THIS
```

**✅ Checklist**:
- [ ] Relationship added to User model
- [ ] cascade="all, delete-orphan" included (deleting user deletes todos)

---

### Step 6: Register Router in Main App

**File**: `app/main.py`

**Add import and include router**:
```python
from app.todos.router import router as todos_router  # ← ADD THIS

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(items_router, prefix="/api/v1")
app.include_router(todos_router, prefix="/api/v1")  # ← ADD THIS
```

**✅ Checklist**:
- [ ] Router imported
- [ ] Router included with `app.include_router()`
- [ ] Prefix set to "/api/v1"

---

### Step 7: Create `__init__.py`

**File**: `app/todos/__init__.py`

**Content**:
```python
"""Todo module with CRUD operations"""
```

**✅ Checklist**:
- [ ] `__init__.py` created

---

### Step 8: Test Your New Entity

**Run the application**:
```bash
uvicorn app.main:app --reload
```

**Test in Swagger UI** (http://localhost:8000/docs):

1. **Register** (POST /api/v1/auth/register)
   - Email: test@example.com
   - Password: testpassword123

2. **Login** (POST /api/v1/auth/login)
   - Copy the `access_token`

3. **Authorize** (Click "Authorize" button in Swagger)
   - Paste token

4. **Create Todo** (POST /api/v1/todos)
   ```json
   {
     "title": "My first todo",
     "description": "This is a test",
     "is_completed": false
   }
   ```

5. **Get All Todos** (GET /api/v1/todos)
   - Should return array with your todo

6. **Update Todo** (PUT /api/v1/todos/{id})
   ```json
   {
     "is_completed": true
   }
   ```

7. **Delete Todo** (DELETE /api/v1/todos/{id})
   - Should return 204 No Content

**✅ Checklist**:
- [ ] App starts without errors
- [ ] All 5 endpoints appear in Swagger docs
- [ ] Create todo works (201 Created)
- [ ] Get all todos works (200 OK)
- [ ] Get single todo works (200 OK)
- [ ] Update todo works (200 OK)
- [ ] Delete todo works (204 No Content)
- [ ] Authorization works (can't access other users' todos)

---

## Summary of Files to Create/Modify

**New files (3)**:
1. `app/todos/__init__.py`
2. `app/todos/models.py` (copy from `app/examples/models.py`)
3. `app/todos/schemas.py` (copy from `app/examples/schemas.py`)
4. `app/todos/router.py` (copy from `app/examples/router.py`)

**Modified files (3)**:
1. `app/auth/models.py` (add relationship)
2. `app/core/database.py` (add import in `init_db()`)
3. `app/main.py` (import and include router)

**Total**: 4 new files + 3 modifications = **7 changes**

---

## Common Mistakes to Avoid

### ❌ Mistake #1: Forgetting to update `init_db()`
**Error**: `Table not created`
**Fix**: Add import in `app/core/database.py`:
```python
from app.todos import models as todo_models
```

### ❌ Mistake #2: Wrong router prefix
**Error**: Endpoints not found (404)
**Fix**: Check `router = APIRouter(prefix="/todos", ...)` matches URLs you're calling

### ❌ Mistake #3: Importing schemas from models file
**Error**: `ImportError: cannot import name 'TodoCreate' from 'app.todos.models'`
**Fix**: Import from correct file:
```python
from app.todos.schemas import TodoCreate  # ← schemas, not models!
```

### ❌ Mistake #4: Missing authorization check
**Error**: Users can access each other's data
**Fix**: Keep this check in all endpoints:
```python
if todo.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized")
```

### ❌ Mistake #5: Forgetting `user_id` when creating
**Error**: `IntegrityError: NOT NULL constraint failed: todos.user_id`
**Fix**: Always set `user_id=current_user.id` when creating:
```python
new_todo = Todo(
    user_id=current_user.id,  # ← Don't forget this!
    title=todo_data.title,
    ...
)
```

---

## Advanced: Adding Custom Fields

### Example: Adding a "priority" field to Todo

**1. Update Model**:
```python
from sqlalchemy import Enum
import enum

class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Todo(Base):
    ...
    priority = Column(Enum(Priority), default=Priority.MEDIUM, nullable=False)
```

**2. Update Schemas**:
```python
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TodoCreate(BaseModel):
    ...
    priority: Priority = Field(default=Priority.MEDIUM)

class TodoUpdate(BaseModel):
    ...
    priority: Optional[Priority] = None

class TodoResponse(BaseModel):
    ...
    priority: Priority
```

**3. No changes needed in router** (it just passes data through)

---

## Next Steps

Once you've added your entity successfully:

1. **Write tests** (see `tests/test_examples.py` for pattern)
2. **Add business logic** in a `service.py` file (optional)
3. **Add validation** in schemas (min_length, regex, etc)
4. **Add search/filter** in GET endpoint (e.g., `?completed=true`)
5. **Add pagination** (see `ExampleItemListResponse` schema)

---

## Need Help?

- **Examples**: Look at `app/examples/` for complete working code
- **Patterns**: See `docs/PATTERNS.md` for common patterns
- **Architecture**: See `docs/ARCHITECTURE.md` for system overview
- **Tests**: See `tests/test_examples.py` for testing patterns
