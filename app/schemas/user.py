from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import User as UserModel
from app.schemas.base import ResponseBase

class UserCreate(BaseModel):
    user_id: int

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class UserResponse(ResponseBase):
    data: UserModel