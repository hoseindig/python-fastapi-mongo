from fastapi import Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId

# JWT Configuration
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# MongoDB Connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["mydatabase"]
users_collection = db["users"]

# OAuth2 Bearer Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await users_collection.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
