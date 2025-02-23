from typing import Optional, List
from pydantic import Field
from .base import MongoBaseModel

class User(MongoBaseModel):
    user_id: int = Field(..., description="User ID from Postgres")
    
