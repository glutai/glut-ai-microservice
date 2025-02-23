from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel
from datetime import datetime

T = TypeVar('T')

class ResponseBase(BaseModel):
    success: bool = True
    message: Optional[str] = None

class ListResponse(ResponseBase, Generic[T]):
    data: List[T]
    total: int
    page: int
    size: int