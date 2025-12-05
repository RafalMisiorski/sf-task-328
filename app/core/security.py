"""
Security Utilities: JWT and Password Hashing

This module provides utilities for:
1. Password hashing and verification (using bcrypt)
2. JWT token creation and verification

WHY: Security utilities are centralized for consistency and easy updates.
WHY: bcrypt is industry-standard for password hashing (slow + salted = secure).
WHY: JWT tokens are stateless and include user claims (no database lookup per request).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings


# Password hashing context
# WHY: bcrypt is secure, auto-salts passwords, and is computationally expensive (prevents brute force)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        password: Plain-text password from user

    Returns:
        Hashed password (safe to store in database)

    WHY: Never store plain-text passwords.
    WHY: Bcrypt automatically generates unique salt for each password.

    Example:
        hashed = hash_password("mysecretpassword")
        # hashed looks like: "$2b$12$KIX..."
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hashed password.

    Args:
        plain_password: Password provided by user during login
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise

    WHY: Constant-time comparison prevents timing attacks.

    Example:
        is_valid = verify_password("mysecretpassword", user.hashed_password)
        if is_valid:
            # Login successful
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Claims to include in token (typically {"sub": user_email})
        expires_delta: Custom expiration time (optional, defaults to settings)

    Returns:
        Encoded JWT token string

    WHY: JWT tokens are stateless (no database lookup needed).
    WHY: Tokens include expiration time for automatic invalidation.
    WHY: Token signature prevents tampering (verified with SECRET_KEY).

    Example:
        token = create_access_token({"sub": "user@example.com"})
        # Client includes token in Authorization: Bearer <token>
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})

    # Encode JWT with secret key
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload (claims) if valid, None if invalid

    WHY: Verifies token signature and expiration.
    WHY: Returns None instead of raising exception for easier error handling.

    Example:
        payload = verify_access_token(token)
        if payload:
            user_email = payload.get("sub")
            # Token is valid, proceed with request
        else:
            # Token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None
