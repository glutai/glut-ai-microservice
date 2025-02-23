from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.core.log_helper import log_api_call
from app.services.message_service import MessageService
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse
from app.core.deps import get_db
from app.core.errors import NotFoundError
from app.core.logger import api_logger as logger

router = APIRouter()

@router.get("/user/{user_id}/brand/{brand_id}", response_model=List[Message])
@log_api_call("get_messages_by_user_and_brand")
async def get_messages_by_user_and_brand(
    user_id: int,
    brand_id: int,
    limit: int = 10,
    before_id: Optional[str] = None,
    db=Depends(get_db)
):
    """Get messages between a user and a brand"""

    message_service = MessageService(db)
    messages = await message_service.get_messages_by_user_and_brand(
        user_id, 
        brand_id, 
        limit=limit, 
        before_id=before_id
    )
    return messages


@router.get("/user-brand/{user_brand_id}", response_model=List[Message])
@log_api_call("get_messages")
async def get_messages(
    user_brand_id: str,
    limit: int = 10,
    before_id: Optional[str] = None,
    db=Depends(get_db)
):
    """Get messages for a specific user-brand association"""

    message_service = MessageService(db)
    return await message_service.get_messages(
        user_brand_id,
        limit=limit,
        before_id=before_id
    )
   
@router.post("/", response_model=MessageResponse)
@log_api_call("create_message")
async def create_message(
    message: MessageCreate, 
    db=Depends(get_db)
):
    """Create a new message"""

    message_service = MessageService(db)
    new_message = await message_service.add_message(message)
    return MessageResponse(
        success=True,
        data=new_message,
        message="Message created successfully"
    )
