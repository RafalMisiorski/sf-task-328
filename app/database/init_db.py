"""
Database Initialization and Seeding

This module provides utilities for initializing the database and optionally seeding with test data.

WHY: Separate initialization logic from main application.
WHY: Allows running database setup independently.
WHY: Useful for testing and development.
"""

from sqlalchemy.orm import Session

from app.core.database import engine, SessionLocal, Base
from app.core.security import hash_password
from app.auth.models import User
from app.examples.models import ExampleItem


def create_tables():
    """
    Create all database tables.

    WHY: Creates tables for all models that inherit from Base.
    WHY: Idempotent - safe to run multiple times (won't recreate existing tables).

    NOTE: In production, use Alembic migrations instead of this function.
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def seed_test_data(db: Session):
    """
    Seed database with test data for development.

    WHY: Useful for testing and development.
    WHY: Creates sample users and items to work with.

    Args:
        db: Database session

    WARNING: Only use this in development! Never run in production!
    """
    print("Seeding test data...")

    # Check if data already exists
    existing_users = db.query(User).count()
    if existing_users > 0:
        print("⚠️  Database already has data, skipping seeding")
        return

    # Create test user
    test_user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
        is_superuser=False
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    print(f"✅ Created test user: {test_user.email}")

    # Create test admin user
    admin_user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        is_active=True,
        is_superuser=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    print(f"✅ Created admin user: {admin_user.email}")

    # Create sample items for test user
    sample_items = [
        ExampleItem(
            user_id=test_user.id,
            title="My first item",
            description="This is a sample item",
            is_completed=False
        ),
        ExampleItem(
            user_id=test_user.id,
            title="Another item",
            description="This one is completed",
            is_completed=True
        ),
        ExampleItem(
            user_id=test_user.id,
            title="Important task",
            description=None,
            is_completed=False
        ),
    ]

    for item in sample_items:
        db.add(item)

    db.commit()
    print(f"✅ Created {len(sample_items)} sample items")

    print("\n📝 Test credentials:")
    print("   Email: test@example.com")
    print("   Password: testpassword123")
    print("\n📝 Admin credentials:")
    print("   Email: admin@example.com")
    print("   Password: adminpassword123")


def reset_database():
    """
    Drop all tables and recreate them.

    WHY: Useful for testing and development.
    WARNING: This deletes ALL DATA! Only use in development!
    """
    print("⚠️  Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped")

    create_tables()


if __name__ == "__main__":
    """
    Run this script directly to initialize database with test data.

    Usage:
        python -m app.database.init_db

    WHY: Convenient way to set up database for development.
    """
    import sys

    print("🚀 Database Initialization Script")
    print("=" * 50)

    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        confirm = input("⚠️  This will DELETE ALL DATA. Are you sure? (yes/no): ")
        if confirm.lower() == "yes":
            reset_database()
        else:
            print("❌ Reset cancelled")
            sys.exit(0)
    else:
        create_tables()

    # Ask if user wants to seed test data
    seed = input("\n❓ Do you want to seed test data? (yes/no): ")
    if seed.lower() == "yes":
        db = SessionLocal()
        try:
            seed_test_data(db)
        finally:
            db.close()

    print("\n✅ Database initialization complete!")
    print("   Run: uvicorn app.main:app --reload")
    print("   Docs: http://localhost:8000/docs")
