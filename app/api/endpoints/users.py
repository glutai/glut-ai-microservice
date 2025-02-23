from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.log_helper import log_api_call
from app.services.user_service import UserService
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.deps import get_db
from app.core.errors import DatabaseError, ValidationError
from app.core.logger import api_logger as logger

router = APIRouter()

@router.post("/create-user", response_model=UserResponse)
@log_api_call("create_user")
async def create_user(user_data: UserCreate, db=Depends(get_db)):
    """Create a new user"""
    user_service = UserService(db)
    user = await user_service.get_or_create_user(user_id=user_data.user_id)
    return UserResponse(success=True, data=user, message="User created successfully")