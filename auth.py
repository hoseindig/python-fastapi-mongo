from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.collection import Collection
from bson import ObjectId
from dependencies import get_current_user, users_collection

# JWT Configuration
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Bearer Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Create Auth Router
router = APIRouter()

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str
    family: str
    mobile: str  # Added Mobile
    role: str = "user"  # Default role is 'user'

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: EmailStr = None
    name: str = None
    family: str = None
    mobile: str = None  # Added Mobile
    password: str = None
    role: str = None  # Added Role

class Token(BaseModel):
    access_token: str
    token_type: str

# Signup Route
@router.post("/signup")
async def signup(user: UserSignup):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_mobile = await users_collection.find_one({"mobile": user.mobile})
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    hashed_password = pwd_context.hash(user.password)
    user_data = {
        "email": user.email,
        "password": hashed_password,
        "name": user.name,
        "family": user.family,
        "mobile": user.mobile,  # Store Mobile
        "role": user.role  # Store Role
    }
    
    result = await users_collection.insert_one(user_data)
    return {"message": "User created successfully", "user_id": str(result.inserted_id)}

# Login Route
@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    user_record = await users_collection.find_one({"email": user.email})
    if not user_record or not pwd_context.verify(user.password, user_record["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = jwt.encode(
        {"sub": user.email, "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {"access_token": access_token, "token_type": "bearer"}

# Protected Route Example
@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": "You have access!", "user": current_user["email"], "role": current_user["role"]}

# Get User Info
@router.get("/me")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "email": current_user["email"],
        "name": current_user.get("name"),
        "family": current_user.get("family"),
        "mobile": current_user.get("mobile"),  # Include Mobile
        "role": current_user.get("role")  # Include Role
    }

# Update User Info
@router.put("/me/update")
async def update_user_info(
    user_update: UserUpdate, 
    current_user: dict = Depends(get_current_user)
):
    update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items()}
    
    if "password" in update_data:
        update_data["password"] = pwd_context.hash(update_data["password"])

    if "mobile" in update_data:
        existing_mobile = await users_collection.find_one({"mobile": update_data["mobile"]})
        if existing_mobile and str(existing_mobile["_id"]) != str(current_user["_id"]):
            raise HTTPException(status_code=400, detail="Mobile number already in use")

    if "role" in update_data and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied to change role")

    result = await users_collection.update_one(
        {"_id": ObjectId(current_user["_id"])}, {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No changes made")

    return {"message": "User info updated successfully"}

# Clear All Users Endpoint
@router.delete("/clear-all-users")
async def clear_all_users():
    result = await users_collection.delete_many({})
    if result.deleted_count > 0:
        return {"message": f"Successfully deleted {result.deleted_count} users."}
    else:
        return {"message": "No users found to delete."}
