# System Architecture

This document explains the **high-level architecture** of this FastAPI application.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Client (Browser/App)                │
│              HTTP Requests with JWT Token                │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Middleware Layer                     │  │
│  │  - CORS (Cross-Origin Resource Sharing)          │  │
│  │  - Exception handling                            │  │
│  └──────────────────┬────────────────────────────────┘  │
│                     │                                    │
│  ┌──────────────────▼────────────────────────────────┐  │
│  │              Router Layer                         │  │
│  │  - app/auth/router.py (Authentication)           │  │
│  │  - app/examples/router.py (CRUD)                 │  │
│  │  - Future: app/*/router.py                       │  │
│  └──────────────────┬────────────────────────────────┘  │
│                     │                                    │
│  ┌──────────────────▼────────────────────────────────┐  │
│  │         Dependency Injection                      │  │
│  │  - get_db() → Database session                   │  │
│  │  - get_current_user() → Authenticated user       │  │
│  └──────────────────┬────────────────────────────────┘  │
│                     │                                    │
│  ┌──────────────────▼────────────────────────────────┐  │
│  │           Validation Layer (Pydantic)             │  │
│  │  - Request validation                             │  │
│  │  - Response serialization                         │  │
│  │  - Type checking                                  │  │
│  └──────────────────┬────────────────────────────────┘  │
│                     │                                    │
│  ┌──────────────────▼────────────────────────────────┐  │
│  │        Business Logic Layer                       │  │
│  │  - Authorization checks                           │  │
│  │  - Data manipulation                              │  │
│  │  - Business rules                                 │  │
│  └──────────────────┬────────────────────────────────┘  │
│                     │                                    │
│  ┌──────────────────▼────────────────────────────────┐  │
│  │          ORM Layer (SQLAlchemy)                   │  │
│  │  - Models (Python classes)                        │  │
│  │  - Relationships                                  │  │
│  │  - Queries                                        │  │
│  └──────────────────┬────────────────────────────────┘  │
└────────────────────┬│───────────────────────────────────┘
                     ││
                     ▼▼
┌─────────────────────────────────────────────────────────┐
│              Database (SQLite/PostgreSQL/MySQL)          │
│  - users table                                           │
│  - example_items table                                   │
│  - Future: other tables                                  │
└─────────────────────────────────────────────────────────┘
```

---

## Request Flow

### Example: Creating an Item

1. **Client** sends POST request to `/api/v1/items` with JWT token:
   ```http
   POST /api/v1/items HTTP/1.1
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Content-Type: application/json

   {
     "title": "My item",
     "description": "Test",
     "is_completed": false
   }
   ```

2. **CORS Middleware** checks origin is allowed

3. **FastAPI** routes request to `app/examples/router.py:create_item()`

4. **Dependency Injection**:
   - `get_db()` provides database session
   - `get_current_user()` validates JWT and returns User

5. **Pydantic Validation** (`ExampleItemCreate` schema):
   - Validates `title` is string
   - Validates `is_completed` is boolean
   - Returns validation error if invalid

6. **Business Logic** (in router):
   - Creates `ExampleItem` with `user_id=current_user.id`
   - Saves to database via ORM

7. **Response Serialization** (`ExampleItemResponse` schema):
   - Converts ORM model to JSON
   - Returns 201 Created with item data

---

## Module Structure

### Core Modules

**`app/core/`**: Shared utilities
- `config.py`: Settings (environment variables)
- `database.py`: SQLAlchemy setup
- `security.py`: JWT and password utilities

### Feature Modules

Each feature (auth, items, etc) has:
```
app/<feature>/
├── models.py       # Database models (SQLAlchemy)
├── schemas.py      # API schemas (Pydantic)
├── router.py       # Endpoints (FastAPI)
└── dependencies.py # Optional: Custom dependencies
```

**Benefits**:
- **Separation of concerns**: Each file has one job
- **Reusability**: Common patterns across features
- **Testability**: Easy to mock dependencies
- **Maintainability**: Clear where to add new code

---

## Authentication Flow

### Registration

```
Client                  API                    Database
  │                      │                        │
  │─── POST /register ──>│                        │
  │  (email, password)   │                        │
  │                      │                        │
  │                      │──── hash password ────>│
  │                      │                        │
  │                      │──── create user ──────>│
  │                      │                        │
  │<─── 201 Created ─────│                        │
  │    (user data)       │                        │
```

### Login

```
Client                  API                    Database
  │                      │                        │
  │──── POST /login ────>│                        │
  │  (email, password)   │                        │
  │                      │                        │
  │                      │──── get user ─────────>│
  │                      │<──── user data ────────│
  │                      │                        │
  │                      │── verify password ───> │
  │                      │                        │
  │                      │─── create JWT token    │
  │                      │                        │
  │<────── 200 OK ───────│                        │
  │    (access_token)    │                        │
```

### Protected Endpoint

```
Client                  API                    Database
  │                      │                        │
  │──── GET /items ─────>│                        │
  │  Bearer <token>      │                        │
  │                      │                        │
  │                      │─── verify JWT ─────────│
  │                      │                        │
  │                      │─── decode token ───────│
  │                      │    (extract email)     │
  │                      │                        │
  │                      │──── get user ─────────>│
  │                      │<──── user data ────────│
  │                      │                        │
  │                      │──── get items ────────>│
  │                      │    WHERE user_id=X     │
  │                      │<──── items ────────────│
  │                      │                        │
  │<────── 200 OK ───────│                        │
  │      (items)         │                        │
```

---

## Authorization Model

**Role-Based Access Control** (simplified):

- **User**: Can only access their own resources
- **Superuser** (optional): Can access all resources

**Ownership-Based Authorization**:
```python
# Every resource has user_id field
class ExampleItem(Base):
    user_id = Column(Integer, ForeignKey("users.id"))

# Every endpoint checks ownership
if item.user_id != current_user.id:
    raise HTTPException(403, "Not authorized")
```

**Authorization Matrix**:

| Resource | Own | Others' | Superuser |
|----------|-----|---------|-----------|
| View | ✅ | ❌ | ✅ |
| Create | ✅ | N/A | ✅ |
| Update | ✅ | ❌ | ✅ |
| Delete | ✅ | ❌ | ✅ |

---

## Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL
);

-- Example items table
CREATE TABLE example_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_example_items_user_id ON example_items(user_id);
```

**Relationships**:
- **One-to-Many**: User → Items
- **Cascade Delete**: Deleting user deletes all their items

---

## API Design Principles

### RESTful Endpoints

| Method | Endpoint | Description | Body | Response |
|--------|----------|-------------|------|----------|
| POST | `/items` | Create | Item data | 201 + item |
| GET | `/items` | List all | - | 200 + items array |
| GET | `/items/{id}` | Get one | - | 200 + item |
| PUT | `/items/{id}` | Update | Updated data | 200 + item |
| DELETE | `/items/{id}` | Delete | - | 204 No Content |

### Standard Response Format

**Success**:
```json
{
  "id": 1,
  "title": "Item title",
  ...
}
```

**Error**:
```json
{
  "detail": "Error message"
}
```

---

## Scalability Considerations

### Current (Single Instance)

```
Client → FastAPI → Database
```

**Good for**: MVP, development, small apps

### Production (Multiple Instances)

```
           ┌─> FastAPI Instance 1 ─┐
Client → Load Balancer ─> FastAPI Instance 2 ─> Database
           └─> FastAPI Instance 3 ─┘
```

**Add**:
- Load balancer (nginx, Traefik)
- Database connection pooling
- Redis for session storage (if needed)

### High Scale

```
           ┌─> FastAPI Instance 1 ─┐          ┌─> Primary DB
Client → LB ─> FastAPI Instance 2 ─> DB Pool ─> Replica DB 1
           └─> FastAPI Instance 3 ─┘          └─> Replica DB 2
              ↓
            Redis (cache)
```

**Add**:
- Database replicas (read scaling)
- Redis cache (reduce DB load)
- CDN for static files
- Message queue (Celery) for background tasks

---

## Security Architecture

### Authentication: JWT Tokens

**Advantages**:
- Stateless (no session storage needed)
- Self-contained (includes user info)
- Signed (tamper-proof)

**Security measures**:
- Tokens expire (30 minutes default)
- Secret key kept secure (environment variable)
- HTTPS required in production

### Password Security

- **Hashing**: bcrypt (slow + salted)
- **Salt**: Automatic (different for each password)
- **Cost factor**: 12 rounds (adjustable)

### API Security

- **CORS**: Only allowed origins
- **Rate limiting**: TODO (add if needed)
- **Input validation**: Pydantic (automatic)
- **SQL injection**: Protected by ORM
- **XSS**: JSON responses (no HTML)

---

## Testing Architecture

```
Test Suite
├── Unit Tests
│   ├── test_security.py (password hashing, JWT)
│   └── test_models.py (database models)
│
├── Integration Tests
│   ├── test_auth.py (auth endpoints)
│   └── test_items.py (CRUD endpoints)
│
└── E2E Tests (optional)
    └── test_workflows.py (register → login → create → update → delete)
```

**Test database**: In-memory SQLite (fast, isolated)

---

## Error Handling

### Automatic Errors (FastAPI + Pydantic)

- **422 Unprocessable Entity**: Validation error
- **405 Method Not Allowed**: Wrong HTTP method

### Manual Errors (Application Logic)

- **401 Unauthorized**: Invalid/missing token
- **403 Forbidden**: Not authorized (wrong user)
- **404 Not Found**: Resource doesn't exist
- **500 Internal Server Error**: Unexpected error

**All errors return JSON**:
```json
{
  "detail": "Error message"
}
```

---

## Deployment Options

### 1. Traditional Server

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Use with**: nginx, systemd, supervisor

### 2. Docker

```bash
docker build -t myapp .
docker run -p 8000:8000 myapp
```

### 3. Docker Compose

```bash
docker-compose up
```

**Includes**: API + Database + Redis (optional)

### 4. Cloud Platforms

- **Heroku**: `Procfile` + PostgreSQL addon
- **AWS**: ECS/Fargate + RDS
- **Google Cloud**: Cloud Run + Cloud SQL
- **Azure**: App Service + Azure Database

---

## Summary

**Key Design Decisions**:

1. **Three-layer architecture**: Clear separation (models → schemas → routers)
2. **Dependency injection**: Clean, testable code
3. **JWT authentication**: Stateless, scalable
4. **Ownership-based authorization**: Users own their data
5. **RESTful API**: Standard, predictable endpoints
6. **Pydantic validation**: Automatic, type-safe
7. **Comprehensive examples**: Copy-paste ready code

**Result**: Production-ready template that agents can easily extend.

---

**Next**: See `PATTERNS.md` for common patterns, `QUICKSTART.md` for adding entities.
