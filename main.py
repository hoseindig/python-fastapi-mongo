from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# MongoDB connection
MONGO_URI = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URI)
db = client.taskdb
collection = db.tasks

# Task Model
class Task(BaseModel):
    title: str
    completed: bool = False

# Create Task
@app.post("/tasks/", response_model=Task)
async def create_task(task: Task):
    task_dict = task.dict()
    result = await collection.insert_one(task_dict)
    task_dict["_id"] = str(result.inserted_id)
    return task_dict

# Get All Tasks
@app.get("/tasks/", response_model=List[Task])
async def get_tasks():
    tasks = await collection.find().to_list(100)
    for task in tasks:
        task["_id"] = str(task["_id"])  # Convert ObjectId to string
    return tasks

# Get Task by ID
@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    task = await collection.find_one({"_id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["_id"] = str(task["_id"])
    return task

# Update Task
@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, updated_task: Task):
    result = await collection.update_one({"_id": task_id}, {"$set": updated_task.dict()})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {**updated_task.dict(), "_id": task_id}

# Delete Task
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    result = await collection.delete_one({"_id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}

# Run with: uvicorn main:app --reload
