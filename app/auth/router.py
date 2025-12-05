"""
Authentication Router (API Endpoints)

This module defines API endpoints for authentication:
- POST /auth/register - Create new user account
- POST /auth/login - Login and get JWT token
- GET /auth/me - Get current user info

WHY: Routers group related endpoints together.
WHY: Separate file for each feature (auth, users, todos, etc).
WHY: APIRouter allows including routes in main app.

This is a COMPLETE working example - copy this pattern for new features!
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.auth.models import User
from app.auth.schemas import UserCreate, UserResponse, UserLogin, Token
from app.auth.dependencies import get_current_user


# Create router
# WHY: prefix="/auth" means all endpoints start with /auth
# WHY: tags=["auth"] groups endpoints in API docs
router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    Endpoint: POST /auth/register

    Request Body:
        {
            "email": "user@example.com",
            "password": "securepassword123"
        }

    Response (201 Created):
        {
            "id": 1,
            "email": "user@example.com",
            "is_active": true,
            "is_superuser": false,
            "created_at": "2024-01-15T10:30:00Z"
        }

    Errors:
        - 400: Email already registered

    WHY: Hash password before storing (never store plain text).
    WHY: Return UserResponse (no password in response).
    WHY: IntegrityError catches duplicate email (unique constraint).
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    return new_user


@router.post("/login", response_model=Token)
def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password, get JWT token.

    Endpoint: POST /auth/login

    Request Body:
        {
            "email": "user@example.com",
            "password": "securepassword123"
        }

    Response (200 OK):
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }

    Errors:
        - 401: Invalid credentials (wrong email or password)
        - 403: Account is inactive

    WHY: Return 401 for both "user not found" and "wrong password" (don't reveal which).
    WHY: Check is_active to prevent deactivated users from logging in.
    WHY: Token contains email in "sub" claim (used by get_current_user).

    Usage:
        1. Client calls /auth/login with email + password
        2. Server returns JWT token
        3. Client stores token (localStorage, cookie, etc)
        4. Client includes token in subsequent requests: "Authorization: Bearer <token>"
    """
    # Get user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()

    # Check if user exists and password is correct
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Create JWT token
    # WHY: "sub" (subject) is standard JWT claim for user identifier
    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.

    Endpoint: GET /auth/me

    Headers:
        Authorization: Bearer <jwt_token>

    Response (200 OK):
        {
            "id": 1,
            "email": "user@example.com",
            "is_active": true,
            "is_superuser": false,
            "created_at": "2024-01-15T10:30:00Z"
        }

    Errors:
        - 401: Invalid or expired token

    WHY: Protected endpoint (requires Depends(get_current_user)).
    WHY: Returns current user based on JWT token.
    WHY: Useful for client to verify token and get user info.

    Usage:
        1. Client includes token in header: "Authorization: Bearer <token>"
        2. get_current_user dependency validates token and gets user
        3. Endpoint returns user info
    """
    return current_user
