from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from app.models.brand import UserBrand as UserBrandModel, Brand as BrandModel
from app.schemas.base import ListResponse, ResponseBase

class BrandCreate(BaseModel):
    brand_id: int
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None

class BrandResponse(ResponseBase):
    data: BrandModel

class UserBrandCreate(BaseModel):
    user_id: int
    brand_id: int

class UserBrandUpdate(BaseModel):
    last_message_at: Optional[datetime] = None
    last_message: Optional[dict] = None

class UserBrandResponse(ResponseBase):
    data: UserBrandModel

class UserBrandListResponse(ListResponse[UserBrandModel]):
    pass