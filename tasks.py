from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.responses import JSONResponse

# MongoDB Connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["mydatabase"]
tasks_collection = db["tasks"]

# Pydantic model for task input and response
class Task(BaseModel):
    title: str
    completed: bool

class TaskResponse(Task):
    id: str

# Task router to manage task operations
router = APIRouter()

# Get all tasks
@router.get("/tasks/", response_model=List[TaskResponse])
async def get_all_tasks():
    try:
        tasks_cursor = tasks_collection.find()  # Fetch tasks
        tasks = await tasks_cursor.to_list(length=100)
        
        # Convert ObjectId to string for response
        for task in tasks:
            task["id"] = str(task["_id"])
            del task["_id"]  # Remove _id field
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {e}")

# Get a single task by ID
@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_by_id(task_id: str):
    try:
        task = tasks_collection.find_one({"_id": ObjectId(task_id)})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task["id"] = str(task["_id"])
        del task["_id"]
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching task by ID: {e}")

# Create a new task
@router.post("/tasks/", response_model=TaskResponse)
async def create_task(task: Task):
    try:
        # Check if task title already exists
        existing_task = await tasks_collection.find_one({"title": task.title})
        if existing_task:
            raise HTTPException(status_code=400, detail="Task title already exists")

        new_task = {
            "title": task.title,
            "completed": task.completed
        }
        result = await tasks_collection.insert_one(new_task)
        created_task = await tasks_collection.find_one({"_id": result.inserted_id})
        created_task["id"] = str(created_task["_id"])
        del created_task["_id"]
        return created_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {e}")

# Update a task by ID
@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task: Task):
    try:
        # Ensure task_id is a valid ObjectId
        if not ObjectId.is_valid(task_id):
            raise HTTPException(status_code=400, detail="Invalid task ID format")
        
        # Find and update the task
        result = await tasks_collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"title": task.title, "completed": task.completed}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Fetch the updated task
        updated_task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
        
        # Convert ObjectId to string for response
        updated_task["id"] = str(updated_task["_id"])
        del updated_task["_id"]  # Remove _id field
        
        return updated_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task: {e}")

# Delete a task by ID
@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    try:
        result = await tasks_collection.delete_one({"_id": ObjectId(task_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        return JSONResponse(content={"message": "Task deleted successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting task: {e}")
