# app/api/endpoints/document_admin.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from app.core.log_helper import log_api_call
from app.utils.document_utils import DocumentCleanup
from app.core.deps import get_db
from app.core.logger import api_logger as logger
from app.schemas.base import ResponseBase
from pydantic import BaseModel

router = APIRouter()

class ProcessingStats(BaseModel):
    status_counts: dict
    processing_times: dict

class CleanupResponse(ResponseBase):
    deleted_count: int

class ReprocessResponse(ResponseBase):
    reprocessed_count: int

@router.post("/cleanup", response_model=CleanupResponse)
@log_api_call("cleanup_documents")
async def cleanup_documents(
    older_than_hours: Optional[int] = 24,
    db=Depends(get_db)
):
    """Clean up failed document processing attempts"""
    try:
        cleanup = DocumentCleanup(db)
        deleted_count = await cleanup.cleanup_failed_documents(older_than_hours)
        
        return CleanupResponse(
            success=True,
            deleted_count=deleted_count,
            message=f"Cleaned up {deleted_count} failed documents"
        )
    except Exception as e:
        logger.error("Failed to cleanup documents", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup documents"
        )

@router.post("/reprocess", response_model=ReprocessResponse)
@log_api_call("reprocess_documents")
async def reprocess_documents(db=Depends(get_db)):
    """Reprocess failed documents"""
    try:
        cleanup = DocumentCleanup(db)
        reprocessed_count = await cleanup.reprocess_failed_documents()
        
        return ReprocessResponse(
            success=True,
            reprocessed_count=reprocessed_count,
            message=f"Marked {reprocessed_count} documents for reprocessing"
        )
    except Exception as e:
        logger.error("Failed to reprocess documents", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reprocess documents"
        )

@router.get("/stats", response_model=ProcessingStats)
@log_api_call("get_processing_stats")
async def get_processing_stats(db=Depends(get_db)):
    """Get document processing statistics"""
    try:
        cleanup = DocumentCleanup(db)
        stats = await cleanup.get_processing_stats()
        return ProcessingStats(**stats)
    except Exception as e:
        logger.error("Failed to get processing stats", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get processing stats"
        )