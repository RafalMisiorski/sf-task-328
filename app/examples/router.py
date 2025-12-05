"""
Example Item Router - COMPLETE CRUD Implementation

This is the MOST IMPORTANT example file - copy this for new entities!

WHY: Shows complete CRUD (Create, Read, Update, Delete) with authorization.
WHY: Demonstrates how to protect endpoints with authentication.
WHY: Shows proper error handling and status codes.

COPY THIS PATTERN for new entities:
1. Copy this entire file
2. Replace "ExampleItem" with your entity name (e.g., "Todo", "Product")
3. Replace "items" with your resource name (e.g., "todos", "products")
4. Adjust logic as needed for your entity
5. Keep the authorization pattern (current_user checks ownership)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.auth.models import User
from app.auth.dependencies import get_current_user
from app.examples.models import ExampleItem
from app.examples.schemas import (
    ExampleItemCreate,
    ExampleItemUpdate,
    ExampleItemResponse
)


# Create router
# WHY: prefix="/items" means all endpoints start with /items
# WHY: tags=["items"] groups endpoints in API docs
router = APIRouter(
    prefix="/items",
    tags=["items"]
)


@router.post("", response_model=ExampleItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: ExampleItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new item.

    Endpoint: POST /items

    Headers:
        Authorization: Bearer <jwt_token>

    Request Body:
        {
            "title": "My first item",
            "description": "Optional description",
            "is_completed": false
        }

    Response (201 Created):
        {
            "id": 1,
            "user_id": 1,
            "title": "My first item",
            "description": "Optional description",
            "is_completed": false,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }

    WHY: Requires authentication (Depends(get_current_user)).
    WHY: user_id comes from authenticated user (not request body).
    WHY: Returns 201 Created status code.
    """
    # Create new item owned by current user
    new_item = ExampleItem(
        user_id=current_user.id,  # Owner is authenticated user
        title=item_data.title,
        description=item_data.description,
        is_completed=item_data.is_completed
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


@router.get("", response_model=List[ExampleItemResponse])
def get_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all items for current user.

    Endpoint: GET /items?skip=0&limit=100

    Headers:
        Authorization: Bearer <jwt_token>

    Query Parameters:
        - skip: Number of items to skip (pagination)
        - limit: Maximum number of items to return

    Response (200 OK):
        [
            {
                "id": 1,
                "user_id": 1,
                "title": "Item 1",
                ...
            },
            {
                "id": 2,
                "user_id": 1,
                "title": "Item 2",
                ...
            }
        ]

    WHY: Returns only items owned by current user (user_id filter).
    WHY: Supports pagination with skip and limit.
    WHY: Returns empty list [] if user has no items.
    """
    items = db.query(ExampleItem).filter(
        ExampleItem.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    return items


@router.get("/{item_id}", response_model=ExampleItemResponse)
def get_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific item by ID.

    Endpoint: GET /items/{item_id}

    Headers:
        Authorization: Bearer <jwt_token>

    Response (200 OK):
        {
            "id": 1,
            "user_id": 1,
            "title": "My item",
            ...
        }

    Errors:
        - 404: Item not found
        - 403: Item belongs to another user (authorization check)

    WHY: Checks that item exists and belongs to current user.
    WHY: Returns 404 if item doesn't exist.
    WHY: Returns 403 if user tries to access someone else's item.
    """
    item = db.query(ExampleItem).filter(ExampleItem.id == item_id).first()

    # Check if item exists
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    # Check if user owns this item (AUTHORIZATION CHECK)
    if item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this item"
        )

    return item


@router.put("/{item_id}", response_model=ExampleItemResponse)
def update_item(
    item_id: int,
    item_data: ExampleItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing item.

    Endpoint: PUT /items/{item_id}

    Headers:
        Authorization: Bearer <jwt_token>

    Request Body (all fields optional):
        {
            "title": "Updated title",
            "description": "Updated description",
            "is_completed": true
        }

    Response (200 OK):
        {
            "id": 1,
            "user_id": 1,
            "title": "Updated title",
            "description": "Updated description",
            "is_completed": true,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T11:00:00Z"  # Updated timestamp!
        }

    Errors:
        - 404: Item not found
        - 403: Item belongs to another user

    WHY: Supports partial updates (only update provided fields).
    WHY: Checks authorization (user must own item).
    WHY: updated_at timestamp is automatically updated.
    """
    item = db.query(ExampleItem).filter(ExampleItem.id == item_id).first()

    # Check if item exists
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    # Check if user owns this item (AUTHORIZATION CHECK)
    if item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this item"
        )

    # Update only provided fields
    # WHY: exclude_unset=True means only update fields that were provided in request
    update_data = item_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an item.

    Endpoint: DELETE /items/{item_id}

    Headers:
        Authorization: Bearer <jwt_token>

    Response (204 No Content):
        (empty response body)

    Errors:
        - 404: Item not found
        - 403: Item belongs to another user

    WHY: Returns 204 No Content (successful deletion, no body).
    WHY: Checks authorization before deletion.
    WHY: Database CASCADE will handle related records (if any).
    """
    item = db.query(ExampleItem).filter(ExampleItem.id == item_id).first()

    # Check if item exists
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    # Check if user owns this item (AUTHORIZATION CHECK)
    if item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this item"
        )

    db.delete(item)
    db.commit()

    return None  # 204 No Content
