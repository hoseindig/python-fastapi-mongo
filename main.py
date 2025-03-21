from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId  # Import ObjectId from bson

app = FastAPI()

# MongoDB connection
MONGO_URI = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URI)
db = client.taskdb
collection = db.tasks

# Task Model
class Task(BaseModel):
    id: Optional[str]  # 'id' is optional (MongoDB will generate it)
    title: str
    completed: bool = False

    class Config:
        # Convert MongoDB ObjectId to string when serializing
        json_encoders = {
            ObjectId: str
        }

# Create Task
@app.post("/tasks/", response_model=Task)
async def create_task(task: Task):
    # Check if a task with the same title already exists
    existing_task = await collection.find_one({"title": task.title})
    if existing_task:
        raise HTTPException(status_code=400, detail="Task with this title already exists")
    
    task_dict = task.dict()
    result = await collection.insert_one(task_dict)
    task_dict["id"] = str(result.inserted_id)
    del task_dict["_id"]
    return task_dict


# Get All Tasks
@app.get("/tasks/", response_model=List[Task])
async def get_tasks():
    tasks = await collection.find().to_list(100)
    for task in tasks:
        task["id"] = str(task["_id"])  # Convert ObjectId to string
        del task["_id"]  # Remove MongoDB _id if not needed
    return tasks

# Get Task by ID
@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    try:
        # Convert string ID to ObjectId
        task_object_id = ObjectId(task_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    # Query MongoDB using the converted ObjectId
    task = await collection.find_one({"_id": task_object_id})

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Add id field and remove _id field
    task["id"] = str(task["_id"])
    del task["_id"]
    return task

# Update Task
@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task: Task):
  # Check if the title already exists for another task
    existing_task = await collection.find_one({"title": task.title, "_id": {"$ne": ObjectId(task_id)}})
    if existing_task:
        raise HTTPException(status_code=400, detail="Task with this title already exists")

    # Proceed with the update
    result = await collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"title": task.title, "completed": task.completed}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    updated_task = await collection.find_one({"_id": ObjectId(task_id)})
    updated_task["id"] = str(updated_task["_id"])
    del updated_task["_id"]
    
    return updated_task

# Delete Task
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    try:
        # Convert string ID to ObjectId
        task_object_id = ObjectId(task_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    
    # Delete the task using the ObjectId
    result = await collection.delete_one({"_id": task_object_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted successfully"}

# Run with: uvicorn main:app --reload
