from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum
from .base import MongoBaseModel

class MessageType(str, Enum):
    NOTIFICATION = "notification"
    MESSAGE = "message"

class Attachment(BaseModel):
    file_id: str
    file_type: str
    file_name: str

class HumanQuery(BaseModel):
    text: str
    attachments: Optional[List[Attachment]] = None

class LLMResponse(BaseModel):
    text: str
    graph: Optional[dict] = None

class Message(MongoBaseModel):
    user_brand_id: str = Field(..., description="Reference to UserBrand document ID")
    content: Union[HumanQuery, LLMResponse]
    message_type: MessageType
    sender_type: Literal["user", "brand"]
    sender_id: int

