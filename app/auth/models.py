"""
Authentication Models (SQLAlchemy ORM)

This module defines the User model for authentication.

WHY: Models represent database tables using SQLAlchemy ORM.
WHY: Separate from schemas (Pydantic) - models are for DB, schemas are for API.
WHY: Password is stored as hashed_password (never store plain text).
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


class User(Base):
    """
    User model for authentication.

    This is a COMPLETE working example that you can copy for new entities.

    Attributes:
        id: Primary key (auto-increment)
        email: Unique user email (used for login)
        hashed_password: Bcrypt-hashed password (never store plain text!)
        is_active: Whether user account is active
        is_superuser: Whether user has admin privileges
        created_at: When user was created

    WHY: __tablename__ tells SQLAlchemy what to name the table in database.
    WHY: unique=True on email ensures no duplicate accounts.
    WHY: index=True on email makes login queries fast.
    """

    __tablename__ = "users"

    # Primary key
    # WHY: autoincrement=True means database assigns IDs automatically
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Email (used for login)
    # WHY: unique=True prevents duplicate accounts
    # WHY: index=True makes queries fast (SELECT * FROM users WHERE email = ?)
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Password (hashed!)
    # WHY: Never store plain-text passwords
    # WHY: Use bcrypt hash (from app.core.security.hash_password)
    hashed_password = Column(String(255), nullable=False)

    # Status flags
    # WHY: is_active allows soft-deleting users (deactivate instead of delete)
    # WHY: is_superuser allows admin features (if needed)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Timestamps
    # WHY: Track when user was created (useful for analytics, debugging)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    # WHY: Allows accessing user.items to get all items owned by this user
    # WHY: cascade="all, delete-orphan" means deleting user deletes their items
    items = relationship("ExampleItem", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation for debugging."""
        return f"<User(id={self.id}, email={self.email})>"
