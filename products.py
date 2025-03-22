from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from bson import ObjectId
from database import products_collection  # Your existing database connection
import re

# Import categories collection from your database module
from dependencies import db
from auth import get_current_user  # Import authentication dependency

categories_collection = db["categories"]

class Product(BaseModel):
    name: str
    price: float
    description: str
    category_id: str

    class Config:
        from_attributes = True  # Updated from orm_mode to from_attributes for Pydantic V2
        populate_by_name = True

# Function to convert ObjectId to string
def objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# Helper function to check if an ObjectId is valid
def is_valid_objectid(value: str) -> bool:
    return bool(re.match(r'^[0-9a-fA-F]{24}$', value))

# Helper function to check if a category exists
async def category_exists(category_id: str) -> bool:
    if not is_valid_objectid(category_id):
        return False
    
    category = await categories_collection.find_one({"_id": ObjectId(category_id)})
    return category is not None

# The API router
router = APIRouter()

##########################################
# Get all products (Protected Route)
@router.get("/")
async def get_all_products(user: dict = Depends(get_current_user)):
    try:
        products = await products_collection.find().to_list(length=100)
        
        # Transform the products to replace _id with id
        formatted_products = []
        for product in products:
            # Create a new dictionary with all the fields
            formatted_product = {key: objectid_to_str(value) for key, value in product.items()}
            
            # Add 'id' field with the string value of '_id'
            formatted_product['id'] = str(product['_id'])
            
            # Remove the '_id' field
            del formatted_product['_id']
            
            formatted_products.append(formatted_product)
            
        return formatted_products
    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching products")
    
##########################################
# Get a specific product by ID (Protected Route)
@router.get("/products/{product_id}")
async def get_product(product_id: str, user: dict = Depends(get_current_user)):
    if not is_valid_objectid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    try:
        product = await products_collection.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        product["id"] = str(product["_id"])
        del product["_id"]
        return product
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")
    
##########################################
# Create a new product (Protected Route)
@router.post("/")
async def create_product(product: Product, user: dict = Depends(get_current_user)):
    try:
        # First, check if the category exists
        if not await category_exists(product.category_id):
            raise HTTPException(status_code=404, detail="Category does not exist")
        
        # Then check if product name already exists
        existing_product = await products_collection.find_one({"name": product.name})
        if existing_product:
            raise HTTPException(status_code=409, detail="Product name already exists")
        
        new_product = await products_collection.insert_one(product.dict())
        created_product = await products_collection.find_one({"_id": new_product.inserted_id})
        
        # Transform the response to use 'id' instead of '_id'
        created_product_formatted = {key: objectid_to_str(value) for key, value in created_product.items()}
        created_product_formatted["id"] = str(created_product["_id"])
        del created_product_formatted["_id"]
        
        return created_product_formatted
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        print(f"Error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")
    
##########################################
# Update an existing product (Protected Route)
@router.put("/products/{product_id}")
async def update_product(product_id: str, product: Product, user: dict = Depends(get_current_user)):
    if not is_valid_objectid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    
    try:
        # First check if the category exists
        if not await category_exists(product.category_id):
            raise HTTPException(status_code=404, detail="Category does not exist")
        
        # Check if another product with the same name already exists (excluding the current product)
        existing_product = await products_collection.find_one({
            "name": product.name,
            "_id": {"$ne": ObjectId(product_id)}
        })
        
        if existing_product:
            raise HTTPException(status_code=409, detail="Product name already exists for another product")
        
        updated_product = await products_collection.find_one_and_update(
            {"_id": ObjectId(product_id)},
            {"$set": product.dict()},
            return_document=True
        )
        
        if updated_product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        
        updated_product["id"] = str(updated_product["_id"])
        del updated_product["_id"]
        return updated_product
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")

##########################################
# Delete a product (Protected Route)
@router.delete("/products/{product_id}")
async def delete_product(product_id: str, user: dict = Depends(get_current_user)):
    try:
        result = await products_collection.delete_one({"_id": ObjectId(product_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"detail": "Product deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")

##########################################
# Clear All Products Endpoint (Protected Route)
@router.delete("/clear-all-product")
async def clear_all_product(user: dict = Depends(get_current_user)):
    result = await products_collection.delete_many({})
    if result.deleted_count > 0:
        return {"message": f"Successfully deleted {result.deleted_count} products."}
    else:
        return {"message": "No products found to delete."}