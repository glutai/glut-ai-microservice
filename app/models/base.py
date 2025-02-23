from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, BeforeValidator, Field
from bson import ObjectId
from typing_extensions import Annotated


def convert_object_id(id: Any) -> str:
    if isinstance(id, ObjectId):
        return str(id)
    return id

PyObjectId = Annotated[str, BeforeValidator(convert_object_id)]

class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    model_config = {
        "json_encoders": {ObjectId: str},
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }