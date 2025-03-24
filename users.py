from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from dependencies import get_current_user, users_collection
from bson import ObjectId
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import shutil
import os

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UPLOAD_DIR = "uploads/profile_pictures"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Role-based access check
def check_role(required_roles: list):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# User Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    family: str
    mobile: str
    role: str = "user"
    profile_image: str | None = None  # New profile image field

class UserUpdate(BaseModel):
    name: str | None = None
    family: str | None = None
    mobile: str | None = None
    role: str | None = None
    profile_image: str | None = None  # Allow updating profile image

# Get All Users (Only for Admin & Super Admin)
@router.get("/")
async def get_all_users(current_user: dict = Depends(check_role(["admin", "super_admin"]))):
    users = await users_collection.find().to_list(100)
    for user in users:
        user["id"] = str(user["_id"])
        del user["_id"], user["password"]
    return users

# Upload User Profile Image
@router.post("/upload-profile-image/")
async def upload_profile_image(file: UploadFile = File(...)):
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"profile_image_url": f"/{file_location}"}

# Add a New User
@router.post("/")
async def add_user(
    user: UserCreate, 
    current_user: dict = Depends(check_role(["admin", "super_admin"]))
):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_mobile = await users_collection.find_one({"mobile": user.mobile})
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    if user.role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role. Only 'user' and 'admin' are allowed")

    if user.role == "admin" and current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only Super Admin can assign 'admin' role")

    hashed_password = pwd_context.hash(user.password)
    user_data = {
        "email": user.email,
        "password": hashed_password,
        "name": user.name,
        "family": user.family,
        "mobile": user.mobile,
        "role": user.role,
        "profile_image": user.profile_image
    }

    result = await users_collection.insert_one(user_data)
    return {"message": "User added successfully", "user_id": str(result.inserted_id)}

# Update User Info
@router.put("/{user_id}")
async def update_user(
    user_id: str, 
    user_update: UserUpdate, 
    current_user: dict = Depends(check_role(["admin", "super_admin"]))
):
    update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items()}

    if "role" in update_data and current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only Super Admin can change roles")

    result = await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No changes made")

    return {"message": "User updated successfully"}

# Delete User (Only Super Admin)
@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(check_role(["super_admin"]))):
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# Get User by ID
@router.get("/{user_id}")
async def get_user_by_id(user_id: str, current_user: dict = Depends(check_role(["admin", "super_admin"]))):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["id"] = str(user["_id"])
    del user["_id"], user["password"]

    return user
