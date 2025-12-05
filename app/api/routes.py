'import pytest' 
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@router.post("/items/", response_model=Item)
def create_item(item: Item):
    try:
        # Simulate potential errors during item creation
        if item.price < 0:
            raise ValueError("Price cannot be negative")
        if item.tax is not None and item.tax < 0:
            raise ValueError("Tax cannot be negative")
        
        # In a real application, you would save the item to a database here
        # For demonstration, we'll just return it
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/items/{item_id}")
def read_item(item_id: int):
    try:
        # Simulate fetching an item, potentially not found
        if item_id == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"item_id": item_id, "name": "Sample Item", "price": 10.0}
    except HTTPException as e:
        # Re-raise HTTPException to be handled by FastAPI
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching item {item_id}: {str(e)}")

@router.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    try:
        # Simulate updating an item, potentially with invalid data
        if item.price < 0:
            raise ValueError("Price cannot be negative")
        
        # In a real application, you would update the item in a database
        return {"item_id": item_id, **item.dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while updating item {item_id}: {str(e)}")

@router.delete("/items/{item_id}")
def delete_item(item_id: int):
    try:
        # Simulate deleting an item, potentially not found
        if item_id == 999:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": f"Item {item_id} deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while deleting item {item_id}: {str(e)}")
