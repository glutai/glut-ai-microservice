from typing import Optional, List, Literal, Union
from pydantic import BaseModel
from .base import MongoBaseModel

class RAGQuery(BaseModel):
    """Model for RAG query input"""
    question: str
    context: Optional[List[str]] = None
    
class RAGResponse(BaseModel):
    """Model for RAG response"""
    answer: str
    source_documents: Optional[List[str]] = None
    
class RAGDocument(MongoBaseModel):
    """Model for storing RAG documents"""
    content: str
    metadata: dict
    embedding: Optional[List[float]] = None
    source: str