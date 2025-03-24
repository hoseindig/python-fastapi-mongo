from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_current_user, users_collection
from bson import ObjectId
from pydantic import BaseModel,EmailStr
from passlib.context import CryptContext

router = APIRouter()

class UserUpdate(BaseModel):
    name: str = None
    family: str = None
    mobile: str = None
    role: str = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Role-based access check
def check_role(required_roles: list):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    family: str
    mobile: str
    role: str = "user"  # Default role is 'user'

# Role-based access check
def check_role(required_roles: list):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Get All Users (Only for Admin & Super Admin)
@router.get("/")
async def get_all_users(current_user: dict = Depends(check_role(["admin", "super_admin"]))):
    users = await users_collection.find().to_list(100)
    for user in users:
        user["id"] = str(user["_id"])
        del user["_id"], user["password"]  # Remove sensitive data
    return users

# Update User Info (Admin and Super Admin can change roles)
@router.put("/{user_id}")
async def update_user(
    user_id: str, 
    user_update: UserUpdate, 
    current_user: dict = Depends(check_role(["admin", "super_admin"]))
):
    update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items()}
    
    if "role" in update_data and current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can change roles")

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

# Add a New User (Only Admins and Super Admins)
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

    # Ensure only Super Admin can assign the "admin" or "super_admin" role
    if user.role in ["admin", "super_admin"] and current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only Super Admin can assign 'admin' or 'super_admin' role")

    hashed_password = pwd_context.hash(user.password)
    user_data = {
        "email": user.email,
        "password": hashed_password,
        "name": user.name,
        "family": user.family,
        "mobile": user.mobile,
        "role": user.role
    }

    result = await users_collection.insert_one(user_data)
    return {"message": "User added successfully", "user_id": str(result.inserted_id)}
