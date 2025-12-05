"""
Example Item Model (SQLAlchemy ORM)

This is a COMPLETE CRUD example that agents can copy and adapt.

WHY: Shows how to create a model with foreign key relationship (user_id → users.id).
WHY: Demonstrates all common column types and patterns.
WHY: This is the template to copy when creating new entities!

COPY THIS PATTERN:
1. Copy this file for your new entity (e.g., Todo, Product, Post)
2. Rename ExampleItem to your entity name
3. Change columns to match your needs
4. Keep the user_id foreign key for authorization
5. Update __tablename__
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


class ExampleItem(Base):
    """
    Example entity with full CRUD operations.

    This demonstrates:
    - Primary key (id)
    - Foreign key relationship (user_id → users.id)
    - Various column types (String, Text, Boolean, DateTime)
    - Timestamps (created_at, updated_at)
    - Relationship to User model

    WHY: This is a complete working example to copy for new entities.
    """

    __tablename__ = "example_items"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign key to User (owner)
    # WHY: Links each item to its owner (user)
    # WHY: ForeignKey constraint ensures user_id exists in users table
    # WHY: ondelete="CASCADE" means deleting user deletes their items
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Index for fast queries: "get all items by user X"
    )

    # Item fields
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)  # Text for long content
    is_completed = Column(Boolean, default=False, nullable=False)

    # Timestamps
    # WHY: Track when items are created and updated
    # WHY: timezone=True ensures timestamps include timezone info
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),  # Auto-update on modification
        nullable=False
    )

    # Relationship to User
    # WHY: Allows accessing item.owner to get User object
    # WHY: back_populates creates items attribute on User (user.items)
    owner = relationship("User", back_populates="items")

    def __repr__(self):
        """String representation for debugging."""
        return f"<ExampleItem(id={self.id}, title={self.title}, user_id={self.user_id})>"


# Add back_populates to User model
# NOTE: In real implementation, you would add this to app/auth/models.py:
#
# from sqlalchemy.orm import relationship
#
# class User(Base):
#     ...
#     items = relationship("ExampleItem", back_populates="owner", cascade="all, delete-orphan")
#
# WHY: cascade="all, delete-orphan" means deleting user deletes their items
