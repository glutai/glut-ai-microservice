from typing import Optional, List
from pydantic import BaseModel
from app.models.document import Document as DocumentModel
from app.schemas.base import ResponseBase, ListResponse

class DocumentCreate(BaseModel):
    title: str
    metadata: Optional[dict] = None

class DocumentResponse(ResponseBase):
    data: DocumentModel

class DocumentListResponse(ListResponse[DocumentModel]):
    pass

class DocumentStatus(BaseModel):
    document_id: str
    status: str
    error: Optional[str] = None