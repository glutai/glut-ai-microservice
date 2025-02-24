from typing import Optional, List
from pydantic import BaseModel
from app.models.rag import RAGQuery, RAGResponse
from app.schemas.base import ResponseBase

class RAGQueryRequest(BaseModel):
    question: str

class RAGQueryResponse(ResponseBase):
    data: RAGResponse