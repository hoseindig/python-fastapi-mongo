from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.collection import Collection
from bson import ObjectId
from dependencies import get_current_user, users_collection
from schemas import UserUpdate  # Use schemas instead of models

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

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Signup Route
@router.post("/signup")
async def signup(user: UserSignup):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user.password)
    user_data = {"email": user.email, "password": hashed_password}
    
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
    return {"message": "You have access!", "user": current_user["email"]}

# Get User Info
@router.get("/me", response_model=UserUpdate)
async def get_user_info(current_user: dict = Depends(get_current_user)):
    return {"email": current_user["email"], "name": current_user.get("name")}

# Update User Info
@router.put("/me/update")
async def update_user_info(
    user_update: UserUpdate, 
    current_user: dict = Depends(get_current_user)
):
    update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items()}
    
    if "password" in update_data:
        update_data["password"] = pwd_context.hash(update_data["password"])

    result = await users_collection.update_one(
        {"_id": ObjectId(current_user["_id"])}, {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No changes made")

    return {"message": "User info updated successfully"}
