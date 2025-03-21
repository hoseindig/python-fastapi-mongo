from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from database import products_collection  # Ensure your database is set up correctly
import re

class Product(BaseModel):
    name: str
    price: float
    description: str
    category: str

    class Config:
        orm_mode = True

# Function to convert ObjectId to string
def objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# Helper function to convert ObjectId to string
def objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# Helper function to check if an ObjectId is valid
def is_valid_objectid(value: str) -> bool:
    # Check if the value is a 24-character hex string
    return bool(re.match(r'^[0-9a-fA-F]{24}$', value))

# The API router
router = APIRouter()

##########################################
# Get all products
@router.get("/products/")
async def get_all_products():
    try:
        # Fetch all products from the database
        products = await products_collection.find().to_list(length=100)
        
        # Convert ObjectId to string for each product
        products = [{key: objectid_to_str(value) for key, value in product.items()} for product in products]

        return products

    except Exception as e:
        # Catch any exceptions and return a 500 error
        print(f"Error fetching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching products")
    
##########################################
# Get a specific product by ID
@router.get("/products/{product_id}")
async def get_product(product_id: str):
    # Check if the product_id is valid
    if not is_valid_objectid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    try:
        # Fetch product by ID from the database
        product = await products_collection.find_one({"_id": ObjectId(product_id)})
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Convert _id to string and delete the original _id field
        product["id"] = str(product["_id"])
        del product["_id"]
        return product

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")
    
    
##########################################
# Create a new product
@router.post("/products/")
async def create_product(product: Product):
    try:
        # Check if product name already exists
        existing_product = await products_collection.find_one({"name": product.name})
        if existing_product:
            raise HTTPException(status_code=409, detail="Product name already exists")

        # Insert the new product into the database
        new_product = await products_collection.insert_one(product.dict())

        # Fetch and return the inserted product, converting ObjectId to string
        created_product = await products_collection.find_one({"_id": new_product.inserted_id})
        
        # Convert the _id (ObjectId) to string before returning the product
        created_product = {key: objectid_to_str(value) for key, value in created_product.items()}

        return created_product

    except HTTPException as http_err:
        # Handle HTTPException (409 Conflict)
        raise http_err
    except Exception as e:
        print(f"Error creating product: {str(e)}")
        # Raise a 500 error for any unexpected issue
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")
    

##########################################
# Update an existing product
@router.put("/products/{product_id}")
async def update_product(product_id: str, product: Product):
    # Validate product_id
    if not is_valid_objectid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    
            # Check if product name already exists
    existing_product = await products_collection.find_one({"name": product.name})
    if existing_product:
        raise HTTPException(status_code=409, detail="Product name already exists")

    try:
        # Attempt to update the product in the database
        updated_product = await products_collection.find_one_and_update(
            {"_id": ObjectId(product_id)},
            {"$set": product.dict()},
            return_document=True
        )

        if updated_product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        # Convert _id to string and remove the original _id field
        updated_product["id"] = str(updated_product["_id"])
        del updated_product["_id"]

        return updated_product

    except Exception as e:
        # Log the error (you can configure a logger to write to a file if needed)
        logger.error(f"Error updating product with ID {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")
##########################################
# Delete a product
@router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    try:
        result = await products_collection.delete_one({"_id": ObjectId(product_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"detail": "Product deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")
