from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.services.user_service import UserService
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.deps import get_db
from app.core.errors import DatabaseError, ValidationError
from app.core.logger import api_logger as logger

router = APIRouter()

@router.post("/create-user", response_model=UserResponse)
async def create_user(user_data: UserCreate, db=Depends(get_db)):
    """Create a new user"""
    try:
        user_service = UserService(db)
        user = await user_service.get_or_create_user(
            user_id=user_data.user_id,
        )
        return UserResponse(
            success=True,
            data=user,
            message="User created successfully"
        )
    except ValidationError as e:
        # Validation errors are expected, log as warning
        logger.warning("User creation validation error", extra={
            "user_id": user_data.user_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except DatabaseError as e:
        # Database errors should be logged as errors
        logger.error("Database error during user creation", extra={
            "user_id": user_data.user_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected errors should be logged with full context
        logger.error("Unexpected error during user creation", extra={
            "user_id": user_data.user_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )