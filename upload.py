from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from bson import ObjectId
import shutil
import os
from dependencies import db

router = APIRouter()
files_collection = db["files"]
UPLOAD_DIR = "uploads"  # Store uploaded images here

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_extension = file.filename.split('.')[-1]  # Get file extension
        file_id = str(ObjectId())  # Generate a unique file ID
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{file_extension}")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_data = {
            "_id": file_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "path": file_path,
        }

        await files_collection.insert_one(file_data)
        return {"file_id": file_id, "file_url": f"/files/image/{file_id}.{file_extension}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.get("/image/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
