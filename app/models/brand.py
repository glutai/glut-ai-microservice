from typing import Optional
from pydantic import Field
from datetime import datetime
from .base import MongoBaseModel
from .message import Message

class Brand(MongoBaseModel):
    """Brand model representing a company or AI assistant"""
    brand_id: int = Field(..., description="Brand ID from Postgres")
    name: str = Field(..., description="Brand name")
    description: Optional[str] = None
    logo_url: Optional[str] = None

class UserBrand(MongoBaseModel):
    """Association between a user and a brand, containing their conversation history"""
    user_id: int = Field(..., description="User ID from Postgres")
    brand_id: int = Field(..., description="Brand ID from Postgres")
    last_message_at: Optional[datetime] = None
    last_message: Optional[Message] = None
    brand_details: Optional[Brand] = None