from typing import Optional, List, Union
from pydantic import BaseModel
from app.models.message import Message as MessageModel, HumanQuery, LLMResponse
from app.schemas.base import ListResponse, ResponseBase

class MessageCreate(BaseModel):
    user_brand_id: str
    content: Union[HumanQuery, LLMResponse]
    message_type: str
    sender_type: str
    sender_id : int

class MessageQueryParams(BaseModel):
    limit: Optional[int] = 10
    before_id: Optional[str] = None

class MessageResponse(ResponseBase):
    data: MessageModel

class MessageListResponse(ListResponse[MessageModel]):
    pass