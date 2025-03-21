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

class Category(BaseModel):
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True  # Updated from orm_mode to from_attributes for Pydantic V2
        populate_by_name = True

class Product(BaseModel):
    name: str
    price: float
    description: str
    category_id: str
    
    class Config:
        from_attributes = True  # Updated from orm_mode to from_attributes for Pydantic V2
        populate_by_name = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None

# models.py
from pydantic import BaseModel

 