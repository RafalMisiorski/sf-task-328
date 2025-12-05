"""
Authentication Schemas (Pydantic Models)

This module defines Pydantic schemas for API request/response validation.

WHY: Schemas validate API data (requests and responses).
WHY: Separate from models (SQLAlchemy) - schemas are for API, models are for DB.
WHY: Pydantic provides automatic validation, serialization, and documentation.

PATTERN: Three types of schemas per entity:
1. Base - Common fields
2. Create - Fields for creating (e.g., password)
3. Response - Fields for responses (e.g., no password, include id)
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """
    Base User schema with common fields.

    WHY: Inherit from this for other User schemas to avoid duplication.
    """
    email: EmailStr = Field(..., description="User email address", examples=["user@example.com"])


class UserCreate(BaseModel):
    """
    Schema for creating a new user (registration).

    Used for: POST /auth/register

    WHY: Requires email and password.
    WHY: EmailStr validates email format automatically.
    WHY: min_length ensures strong password.
    """
    email: EmailStr = Field(..., description="User email address", examples=["user@example.com"])
    password: str = Field(..., min_length=8, description="Password (min 8 characters)", examples=["MySecurePass123"])


class UserResponse(BaseModel):
    """
    Schema for returning user data.

    Used for: Response from /auth/register, /auth/me

    WHY: Includes public fields only (no password!).
    WHY: model_config with from_attributes=True allows creating from ORM models.
    """
    id: int = Field(..., description="User ID", examples=[1])
    email: EmailStr = Field(..., description="User email address", examples=["user@example.com"])
    is_active: bool = Field(..., description="Whether user is active", examples=[True])
    is_superuser: bool = Field(..., description="Whether user is superuser", examples=[False])
    created_at: datetime = Field(..., description="When user was created")

    model_config = ConfigDict(
        from_attributes=True,  # Allow creating from SQLAlchemy models
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class Token(BaseModel):
    """
    Schema for JWT token response.

    Used for: Response from POST /auth/login

    WHY: Standard OAuth2 token format.
    WHY: access_token is the JWT string.
    WHY: token_type is always "bearer" (Bearer Token authentication).
    """
    access_token: str = Field(..., description="JWT access token", examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])
    token_type: str = Field(default="bearer", description="Token type", examples=["bearer"])


class TokenData(BaseModel):
    """
    Schema for data extracted from JWT token.

    Used internally when verifying tokens.

    WHY: "sub" (subject) claim typically contains user email.
    WHY: Optional because token might be invalid.
    """
    email: Optional[str] = None


class UserLogin(BaseModel):
    """
    Schema for user login request.

    Used for: POST /auth/login

    WHY: Simple email + password login.
    WHY: OAuth2PasswordRequestForm could be used instead (for OAuth2 compatibility).
    """
    email: EmailStr = Field(..., description="User email address", examples=["user@example.com"])
    password: str = Field(..., description="User password", examples=["MySecurePass123"])
