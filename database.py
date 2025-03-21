import motor.motor_asyncio
from pymongo import ASCENDING
from bson import ObjectId

# Initialize motor client
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")  # Update with your MongoDB URI
db = client["your_database"]  # Replace with your database name

# Initialize collection
products_collection = db["products"]
tasks_collection = db["tasks"]

# Example of creating an index (optional but useful for performance)
async def create_indexes():
    await products_collection.create_index([("name", ASCENDING)], unique=True)
