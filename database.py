import motor.motor_asyncio
from pymongo import ASCENDING
from bson import ObjectId
import asyncio

# Initialize motor client
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")  # Update with your MongoDB URI
db = client["your_database"]  # Replace with your database name

# Initialize collection
products_collection = db["products"]
tasks_collection = db["tasks"]

# Example of creating an index (optional but useful for performance)
async def create_indexes():
    await products_collection.create_index([("name", ASCENDING)], unique=True)

async def get_mongo_version():
    server_info = await client.server_info()  # Get MongoDB version
    print("MongoDB Version:", server_info["version"])

# Check if already in an event loop
try:
    loop = asyncio.get_running_loop()
    loop.create_task(get_mongo_version())  # Schedule without blocking
except RuntimeError:
    asyncio.run(get_mongo_version())  # Only run if no active event loop
