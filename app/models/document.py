from typing import Optional, Dict
from datetime import datetime
from pydantic import Field
from .base import MongoBaseModel

class Document(MongoBaseModel):
    """Document model for storing knowledge base documents"""
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")
    source_type: str = Field(..., description="Type of document (e.g., 'pdf')")
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    embedding_model: Optional[str] = Field(None, description="Model used for embeddings")
    chunk_size: Optional[int] = Field(None, description="Size of chunks used for processing")
    status: str = Field(default="pending", description="Processing status")
