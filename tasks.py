from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from database import tasks_collection  # Ensure your database is set up correctly
import re
import pdb
import logging

# MongoDB Connection
# client = AsyncIOMotorClient("mongodb://localhost:27017")
# db = client["mydatabase"]
# tasks_collection = db["tasks"]

# Pydantic model for task input and response
class Task(BaseModel):
    title: str
    completed: bool

class TaskResponse(Task):
    id: str


# Helper function to check if an ObjectId is valid
def is_valid_objectid(value: str) -> bool:
    # Check if the value is a 24-character hex string
    return bool(re.match(r'^[0-9a-fA-F]{24}$', value))


# Task router to manage task operations
router = APIRouter()
###############################################
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


###############################################
# Get a single task by ID
@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_by_id(task_id: str):
    if not is_valid_objectid(task_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    try:
        # Await the asynchronous operation
        task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Convert ObjectId to string and remove _id
        task["id"] = str(task["_id"])
        del task["_id"]
        
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching task by ID: {e}")

###############################################
# Create a new task
@router.post("/tasks/", response_model=TaskResponse)
async def create_task(task: Task):
    # Check if the task title already exists
    existing_task = await tasks_collection.find_one({"title": task.title})
    
    if existing_task:
        raise HTTPException(status_code=400, detail="Task title already exists")
    
    # Create the new task
    try:
        result = await tasks_collection.insert_one(task.dict())
        
        # Fetch the created task to include the generated ObjectId
        new_task = await tasks_collection.find_one({"_id": result.inserted_id})
        
        # Convert ObjectId to string for response
        new_task["id"] = str(new_task["_id"])
        del new_task["_id"]  # Remove _id field
        
        return new_task
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")
    
###############################################
# Update a task by ID
@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task: Task):
    if not is_valid_objectid(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    
    try:
        # Ensure task_id is a valid ObjectId
        if not ObjectId.is_valid(task_id):
            raise HTTPException(status_code=400, detail="Invalid task ID format")
        
        logging.warning(f"Task title '{task.title}' {task_id} ")
        
        # Check if task title already exists, excluding the current task
        # existing_task = await tasks_collection.find_one({"title": task.title})
        existing_task = await tasks_collection.find_one({"title": task.title})
        if existing_task:
            raise HTTPException(status_code=409, detail="Product name already exists")

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
    except HTTPException as http_exc:
        # If the exception is a known HTTPException, pass it through
        raise http_exc
    except Exception as e:
        logging.error(f"Unexpected error updating task: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating task: {e}")

###############################################
# Delete a task by ID
@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    # Convert the task_id from string to ObjectId
    try:
        task_object_id = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    # Check if the task exists in the database
    task = await tasks_collection.find_one({"_id": task_object_id})

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Delete the task
    await tasks_collection.delete_one({"_id": task_object_id})

    return {"message": "Task deleted successfully"}

