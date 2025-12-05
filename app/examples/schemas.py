"""
Example Item Schemas (Pydantic Models)

This is a COMPLETE CRUD schema example that agents can copy and adapt.

WHY: Shows the standard pattern for CRUD schemas.
WHY: Demonstrates Base, Create, Update, and Response schemas.

COPY THIS PATTERN for new entities:
1. Base: Common fields
2. Create: Fields required when creating
3. Update: Fields that can be updated (all optional)
4. Response: What API returns (includes id, timestamps, computed fields)
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class ExampleItemBase(BaseModel):
    """
    Base schema with common fields.

    WHY: Inherit from this to avoid duplication.
    WHY: Contains fields used in both Create and Update.
    """
    title: str = Field(..., min_length=1, max_length=200, description="Item title", examples=["My first item"])
    description: Optional[str] = Field(None, description="Item description", examples=["This is a detailed description"])
    is_completed: bool = Field(default=False, description="Whether item is completed", examples=[False])


class ExampleItemCreate(BaseModel):
    """
    Schema for creating a new item.

    Used for: POST /items

    WHY: Requires title (mandatory).
    WHY: description and is_completed are optional (have defaults).
    WHY: user_id comes from authentication (not in request body).
    """
    title: str = Field(..., min_length=1, max_length=200, description="Item title", examples=["My first item"])
    description: Optional[str] = Field(None, description="Item description", examples=["This is a detailed description"])
    is_completed: bool = Field(default=False, description="Whether item is completed", examples=[False])


class ExampleItemUpdate(BaseModel):
    """
    Schema for updating an existing item.

    Used for: PUT /items/{item_id}, PATCH /items/{item_id}

    WHY: All fields optional (user can update just title, or just description, etc).
    WHY: Only provided fields are updated (partial updates).
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Item title", examples=["Updated title"])
    description: Optional[str] = Field(None, description="Item description", examples=["Updated description"])
    is_completed: Optional[bool] = Field(None, description="Whether item is completed", examples=[True])


class ExampleItemResponse(BaseModel):
    """
    Schema for returning item data.

    Used for: Response from all item endpoints

    WHY: Includes all fields from database (id, timestamps, user_id).
    WHY: model_config with from_attributes=True allows creating from ORM models.
    WHY: This is what API returns to client.
    """
    id: int = Field(..., description="Item ID", examples=[1])
    user_id: int = Field(..., description="Owner user ID", examples=[1])
    title: str = Field(..., description="Item title", examples=["My first item"])
    description: Optional[str] = Field(None, description="Item description", examples=["This is a detailed description"])
    is_completed: bool = Field(..., description="Whether item is completed", examples=[False])
    created_at: datetime = Field(..., description="When item was created")
    updated_at: datetime = Field(..., description="When item was last updated")

    model_config = ConfigDict(
        from_attributes=True,  # Allow creating from SQLAlchemy models
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "title": "My first item",
                "description": "This is a detailed description",
                "is_completed": False,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class ExampleItemListResponse(BaseModel):
    """
    Schema for returning paginated list of items.

    Used for: GET /items (with pagination)

    WHY: Wraps items list with pagination metadata.
    WHY: Clients can paginate through large result sets.

    Optional: Use this if you implement pagination.
    """
    items: list[ExampleItemResponse] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items", examples=[42])
    page: int = Field(..., description="Current page number", examples=[1])
    page_size: int = Field(..., description="Items per page", examples=[20])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "user_id": 1,
                        "title": "First item",
                        "description": "Description",
                        "is_completed": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total": 42,
                "page": 1,
                "page_size": 20
            }
        }
    )
