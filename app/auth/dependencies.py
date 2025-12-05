"""
Authentication Dependencies

This module provides FastAPI dependencies for authentication.

WHY: Dependencies inject authenticated user into endpoint functions.
WHY: Centralized authentication logic (DRY principle).
WHY: Automatic 401 error if authentication fails.

USAGE:
    @app.get("/protected")
    def protected_route(current_user: User = Depends(get_current_user)):
        return {"user": current_user.email}
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_access_token
from app.auth.models import User


# HTTP Bearer scheme for JWT tokens
# WHY: Expects "Authorization: Bearer <token>" header
# WHY: auto_error=True means FastAPI returns 401 if header missing
security = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get currently authenticated user from JWT token.

    This is the main authentication dependency used throughout the app.

    Args:
        credentials: JWT token from Authorization header (automatic)
        db: Database session (automatic)

    Returns:
        User: Authenticated user from database

    Raises:
        HTTPException(401): If token is invalid, expired, or user not found

    WHY: Used as dependency in protected endpoints.
    WHY: Validates JWT token and returns User object.
    WHY: Automatic error handling (no need to check None everywhere).

    Example:
        @app.get("/me")
        def get_me(current_user: User = Depends(get_current_user)):
            return {"email": current_user.email}
    """
    # Extract token from credentials
    token = credentials.credentials

    # Verify and decode token
    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract email from token payload (standard JWT "sub" claim)
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are a superuser.

    This dependency is for admin-only endpoints.

    Args:
        current_user: Authenticated user (from get_current_user)

    Returns:
        User: Authenticated superuser

    Raises:
        HTTPException(403): If user is not a superuser

    WHY: Protect admin endpoints without repeating if-checks.

    Example:
        @app.delete("/users/{user_id}")
        def delete_user(
            user_id: int,
            current_user: User = Depends(get_current_active_superuser)
        ):
            # Only superusers can delete users
            ...
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
