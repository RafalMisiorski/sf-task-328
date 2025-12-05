"""
Database Configuration and Session Management

This module sets up SQLAlchemy engine, session, and base model.

WHY: Centralized database setup ensures consistent connection pooling and session management.
WHY: Dependency injection (get_db) ensures proper session lifecycle (automatic cleanup).
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from .config import settings


# Create SQLAlchemy engine
# WHY: Engine manages database connection pool for performance
# WHY: check_same_thread=False is needed for SQLite with FastAPI (multiple threads)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug  # Log SQL queries in debug mode
)

# Create session factory
# WHY: SessionLocal creates new sessions for each request
# WHY: autocommit=False means we control when to commit (explicit is better than implicit)
# WHY: autoflush=False means we control when to flush (prevents surprises)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create base class for models
# WHY: All ORM models inherit from Base
# WHY: Base.metadata can create/drop all tables
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.

    Usage in endpoints:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items

    WHY: Dependency injection ensures session is:
    1. Created for each request
    2. Automatically closed after request (even on error)
    3. Properly committed or rolled back

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.

    WHY: Creates tables based on all models that inherit from Base.
    Call this at application startup or in a migration script.

    Note: In production, use Alembic migrations instead of this function.
    """
    # Import all models here to ensure they are registered with Base
    from app.auth import models as auth_models
    # NOTE: Commented out to prevent SQLAlchemy relationship errors in template
    # Uncomment if you need example models: from app.examples import models as example_models

    # Create all tables
    Base.metadata.create_all(bind=engine)
