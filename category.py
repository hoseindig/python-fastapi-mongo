# category.py
from fastapi import APIRouter, HTTPException
from pymongo.collection import Collection
from bson import ObjectId
from models import Category
from dependencies import db


category_router = APIRouter()

# MongoDB Collection for Categories
categories_collection = db["categories"]

# Helper function to convert ObjectId to string
def objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj


# 1. Create a Category
@category_router.post("/", response_model=Category)
async def create_category(category: Category):
    existing_category = await categories_collection.find_one({"name": category.name})
    if existing_category:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    category_data = category.dict()
    result = await categories_collection.insert_one(category_data)
    category_data["_id"] = str(result.inserted_id)
    return category_data

# 2. Get All Categories
@category_router.get("/")
async def get_all_categories():
    try:
        # Fetch all categories from the database
        categories = await categories_collection.find().to_list(length=100)
        
        # Convert _id to id and ObjectId to string for each category
        products = [
            {**{key: objectid_to_str(value) if isinstance(value, ObjectId) else value for key, value in categorie.items()},
            'id': str(categorie['_id']),  # Add id field with the string representation of _id
            }
            for categorie in categories
        ]
        
        # Remove _id from the response
        for product in products:
            product.pop('_id', None)

        return products

    except Exception as e:
        # Catch any exceptions and return a 500 error
        print(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching categories")


# 3. Get Category by ID
@category_router.get("/category/{category_id}", response_model=Category)
async def get_category_by_id(category_id: str):
    category = await categories_collection.find_one({"_id": ObjectId(category_id)})
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    category["_id"] = str(category["_id"])
    return category

# 4. Update Category
@category_router.put("/category/{category_id}", response_model=Category)
async def update_category(category_id: str, category: Category):
    existing_category = await categories_collection.find_one({"_id": ObjectId(category_id)})
    if not existing_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = category.dict(exclude_unset=True)
    result = await categories_collection.update_one({"_id": ObjectId(category_id)}, {"$set": update_data})
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No changes made")
    
    updated_category = await categories_collection.find_one({"_id": ObjectId(category_id)})
    updated_category["_id"] = str(updated_category["_id"])
    return updated_category

# 5. Delete Category
@category_router.delete("/category/{category_id}")
async def delete_category(category_id: str):
    category = await categories_collection.find_one({"_id": ObjectId(category_id)})
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    result = await categories_collection.delete_one({"_id": ObjectId(category_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Failed to delete category")
    
    return {"message": "Category deleted successfully"}
