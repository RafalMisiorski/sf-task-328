# FastAPI Template - Layer 2 (CRUD with Authentication)

**Production-ready FastAPI template** with complete authentication and CRUD examples.

## Features

✅ **Complete Working Examples**
- User authentication with JWT tokens
- Full CRUD operations with authorization
- Copy-paste ready code for new entities

✅ **Security**
- JWT token authentication
- Password hashing with bcrypt
- Authorization checks (users can only access their own data)

✅ **Developer Experience**
- Comprehensive documentation
- Interactive API docs (Swagger UI)
- Full test coverage examples

✅ **Production Ready**
- CORS configuration
- Error handling
- Database migrations support (Alembic ready)

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
cp .env.example .env
```

Edit `.env` and set your `SECRET_KEY`:
```env
SECRET_KEY=your-secret-key-change-in-production
```

### 3. Initialize Database

```bash
python -m app.database.init_db
```

Select "yes" when asked to seed test data (optional).

### 4. Run the Application

```bash
uvicorn app.main:app --reload
```

### 5. Open API Documentation

Visit: **http://localhost:8000/docs**

---

## Project Structure

```
app/
├── main.py                  # FastAPI application entry point
│
├── core/                    # Core utilities
│   ├── config.py           # Settings (env variables)
│   ├── database.py         # SQLAlchemy setup
│   └── security.py         # JWT and password utilities
│
├── auth/                    # Authentication module
│   ├── models.py           # User model (database)
│   ├── schemas.py          # User schemas (API validation)
│   ├── dependencies.py     # get_current_user dependency
│   └── router.py           # /register, /login, /me endpoints
│
├── examples/                # Example CRUD module ⭐
│   ├── models.py           # ExampleItem model
│   ├── schemas.py          # Item schemas
│   └── router.py           # Full CRUD endpoints
│
└── database/
    └── init_db.py          # Database initialization

tests/
├── conftest.py             # Test fixtures
├── test_auth.py            # Auth tests
└── test_examples.py        # CRUD tests

docs/
├── QUICKSTART.md           # How to add new entities
├── PATTERNS.md             # Architecture patterns
└── ARCHITECTURE.md         # System design
```

---

## Adding a New Entity

**See**: `docs/QUICKSTART.md` for step-by-step guide.

**Summary**:
1. Copy `app/examples/` folder → `app/your_entity/`
2. Rename classes (ExampleItem → YourEntity)
3. Update fields as needed
4. Add router to `app/main.py`
5. Test in Swagger UI

**Time**: 10-15 minutes per entity

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Create new account | No |
| POST | `/api/v1/auth/login` | Login and get JWT token | No |
| GET | `/api/v1/auth/me` | Get current user info | Yes |

### Example Items (CRUD)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/items` | Create new item | Yes |
| GET | `/api/v1/items` | Get all user's items | Yes |
| GET | `/api/v1/items/{id}` | Get specific item | Yes |
| PUT | `/api/v1/items/{id}` | Update item | Yes |
| DELETE | `/api/v1/items/{id}` | Delete item | Yes |

---

## Testing

Run tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

---

## Example Usage

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword123"}'
```

### 2. Login and Get Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword123"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Create an Item (with token)

```bash
curl -X POST http://localhost:8000/api/v1/items \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"title": "My first item", "description": "Test item", "is_completed": false}'
```

### 4. Get All Items

```bash
curl -X GET http://localhost:8000/api/v1/items \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Configuration

Edit `.env` file:

```env
# Application
APP_NAME="My FastAPI App"
DEBUG=True

# Database
DATABASE_URL=sqlite:///./app.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Database Options

**SQLite** (default, for development):
```env
DATABASE_URL=sqlite:///./app.db
```

**PostgreSQL** (recommended for production):
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

**MySQL**:
```env
DATABASE_URL=mysql://user:password@localhost:3306/dbname
```

---

## Security Best Practices

### For Development

✅ Use `.env` file for configuration
✅ Keep `SECRET_KEY` in `.env` (not in code)
✅ Use test credentials in `init_db.py`

### For Production

✅ Generate strong `SECRET_KEY` (32+ characters)
✅ Use environment variables (not `.env` file)
✅ Use PostgreSQL or MySQL (not SQLite)
✅ Set `DEBUG=False`
✅ Configure HTTPS (not HTTP)
✅ Use a reverse proxy (nginx, Traefik)
✅ Set up CORS properly (don't use `allow_origins=["*"]`)

**Generate secure secret key**:
```python
import secrets
print(secrets.token_urlsafe(32))
```

---

## Docker Support

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Run with Docker:
```bash
docker-compose up
```

---

## Database Migrations (Alembic)

### Initialize Alembic

```bash
alembic init alembic
```

### Configure Alembic

Edit `alembic/env.py`:
```python
from app.core.database import Base
from app.auth.models import User
from app.examples.models import ExampleItem

target_metadata = Base.metadata
```

### Create Migration

```bash
alembic revision --autogenerate -m "Initial migration"
```

### Apply Migration

```bash
alembic upgrade head
```

---

## Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)**: Step-by-step guide to add new entities
- **[PATTERNS.md](docs/PATTERNS.md)**: Architecture patterns and best practices
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System design overview

---

## Troubleshooting

### Database locked (SQLite)

**Error**: `database is locked`
**Fix**: Close all other connections, or switch to PostgreSQL

### Import error: cannot import name 'X'

**Error**: `ImportError: cannot import name 'User' from 'app.auth.models'`
**Fix**: Check that all `__init__.py` files exist

### 401 Unauthorized

**Error**: Endpoints return 401
**Fix**:
1. Check token is included: `Authorization: Bearer <token>`
2. Check token is valid (not expired)
3. Check user exists in database

### ModuleNotFoundError

**Error**: `ModuleNotFoundError: No module named 'app'`
**Fix**: Run from project root, not from `app/` directory

---

## Tech Stack

- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation using Python type hints
- **JWT**: JSON Web Tokens for authentication
- **bcrypt**: Password hashing
- **pytest**: Testing framework
- **Uvicorn**: ASGI server

---

## Contributing

When adding new features:

1. **Follow patterns** in `docs/PATTERNS.md`
2. **Write tests** (see `tests/test_examples.py` for pattern)
3. **Update documentation** if adding new patterns
4. **Run tests** before committing

---

## License

MIT License - Feel free to use this template for your projects!

---

## Support

- **Documentation**: See `docs/` folder
- **Examples**: See `app/examples/` and `tests/`
- **API Docs**: http://localhost:8000/docs (when running)
