from fastapi import APIRouter, HTTPException
from models import Product
from pymongo import MongoClient
from bson import ObjectId

# MongoDB setup
client = MongoClient("mongodb://localhost:27017")
db = client["mydatabase"]
products_collection = db["products"]

router = APIRouter()

# Create a product
@router.post("/", response_model=Product)
async def create_product(product: Product):
    existing_product = await products_collection.find_one({"title": product.title})
    if existing_product:
        raise HTTPException(status_code=400, detail="Product with this title already exists")

    product_dict = product.dict()
    result = await products_collection.insert_one(product_dict)
    product_dict["id"] = str(result.inserted_id)
    del product_dict["_id"]
    return product_dict

# Get a product by ID
@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await products_collection.find_one({"_id": ObjectId(product_id)})
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product["id"] = str(product["_id"])
    del product["_id"]
    return product

# Update a product by ID
@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: str, product: Product):
    result = await products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"title": product.title, "description": product.description, "price": product.price, "completed": product.completed}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    updated_product = await products_collection.find_one({"_id": ObjectId(product_id)})
    updated_product["id"] = str(updated_product["_id"])
    del updated_product["_id"]
    
    return updated_product

# Delete a product by ID
@router.delete("/{product_id}")
async def delete_product(product_id: str):
    result = await products_collection.delete_one({"_id": ObjectId(product_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"detail": "Product deleted successfully"}
