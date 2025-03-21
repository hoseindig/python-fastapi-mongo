from pydantic import BaseModel, Field ,EmailStr
from bson import ObjectId
from typing import Optional

# Common model for ObjectId handling
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, ObjectId):
            raise ValueError("Invalid ObjectId")
        return str(v)

# Task model
class Task(BaseModel):
    title: str
    completed: bool

    class Config:
        json_encoders = {ObjectId: str}

# Product model
class Product(BaseModel):
    id: Optional[str] = Field(None, exclude=True)  # Exclude 'id' from OpenAPI schema
    title: str
    description: str
    price: float
    completed: bool = False

    class Config:
        json_encoders = {ObjectId: str}


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None

# models.py
from pydantic import BaseModel

class Category(BaseModel):
    name: str
    description: str