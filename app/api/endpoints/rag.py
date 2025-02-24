# app/api/endpoints/rag.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict
from app.core.errors import ValidationError
from app.core.log_helper import log_api_call
from app.services.rag_service import RAGService
from app.core.deps import get_db
from app.core.logger import api_logger as logger
from app.schemas.base import ResponseBase
from pydantic import BaseModel

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(ResponseBase):
    answer: str
    decision: str

class DocumentUpdate(BaseModel):
    documents: List[Dict]

@router.post("/ask", response_model=QuestionResponse)
@log_api_call("process_question")
async def process_question(
    request: QuestionRequest,
    db=Depends(get_db)
):
    """Process a question through the RAG system"""
    try:
        rag_service = RAGService(db)
        
        # Check if service is ready
        # if not await rag_service.is_ready():
            # raise HTTPException(
            #     status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            #     detail="RAG service not ready. Please ensure documents are loaded."
            # )
        
        result = await rag_service.process_question(request.question)
        
        return QuestionResponse(
            success=True,
            answer=result["answer"],
            decision=result["decision"],
            message="Question processed successfully"
        )
    except ValidationError as e:
        logger.warning("Validation error", extra={
            "question": request.question,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to process question", extra={
            "question": request.question,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process question"
        )

@router.post("/update-knowledge-base")
@log_api_call("update_knowledge_base")
async def update_knowledge_base(
    update: DocumentUpdate,
    db=Depends(get_db)
):
    """Update the RAG knowledge base with new documents"""
    try:
        rag_service = RAGService(db)
        await rag_service.update_knowledge_base(update.documents)
        
        return ResponseBase(
            success=True,
            message="Knowledge base updated successfully"
        )
    except Exception as e:
        logger.error("Failed to update knowledge base", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update knowledge base"
        )