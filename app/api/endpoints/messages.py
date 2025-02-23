from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.services.message_service import MessageService
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse
from app.core.deps import get_db
from app.core.errors import NotFoundError
from app.core.logger import api_logger as logger

router = APIRouter()

@router.get("/user/{user_id}/brand/{brand_id}", response_model=List[Message])
async def get_messages_by_user_and_brand(
    user_id: int,
    brand_id: int,
    limit: int = 10,
    before_id: Optional[str] = None,
    db=Depends(get_db)
):
    """Get messages between a user and a brand"""
    try:
        message_service = MessageService(db)
        messages = await message_service.get_messages_by_user_and_brand(
            user_id, 
            brand_id, 
            limit=limit, 
            before_id=before_id
        )
        return messages
    except Exception as e:
        logger.error("Error retrieving user-brand messages", extra={
            "user_id": user_id,
            "brand_id": brand_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/user-brand/{user_brand_id}", response_model=List[Message])
async def get_messages(
    user_brand_id: str,
    limit: int = 10,
    before_id: Optional[str] = None,
    db=Depends(get_db)
):
    """Get messages for a specific user-brand association"""
    try:
        message_service = MessageService(db)
        return await message_service.get_messages(
            user_brand_id,
            limit=limit,
            before_id=before_id
        )
    except Exception as e:
        logger.error("Error retrieving messages", extra={
            "user_brand_id": user_brand_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.post("/", response_model=MessageResponse)
async def create_message(
    message: MessageCreate, 
    db=Depends(get_db)
):
    """Create a new message"""
    try:
        message_service = MessageService(db)
        new_message = await message_service.add_message(message)
        return MessageResponse(
            success=True,
            data=new_message,
            message="Message created successfully"
        )
    except NotFoundError as e:
        logger.warning("Resource not found in create message", extra={
            "user_brand_id": message.user_brand_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error creating message", extra={
            "user_brand_id": message.user_brand_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )