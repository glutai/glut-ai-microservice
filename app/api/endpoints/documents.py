# app/api/endpoints/documents.py

import json
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional, List
from app.core.log_helper import log_api_call
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.core.deps import get_db
from app.core.logger import api_logger as logger
from app.core.errors import ValidationError, DatabaseError

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse)
@log_api_call("upload_document")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    metadata: Optional[str] = Form(None),
    db=Depends(get_db)
):
    """Upload a PDF document to the knowledge base"""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise ValidationError("Only PDF files are supported")
        
        # Process metadata
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                raise ValidationError("Invalid metadata format")
        
        # Process document
        document_service = DocumentService(db)
        document = await document_service.process_pdf(
            file.file,
            title=title,
            metadata=metadata_dict
        )
        
        # Update RAG knowledge base
        rag_service = RAGService(db)
        await rag_service.update_knowledge_base()
        
        return DocumentResponse(
            success=True,
            data=document,
            message="Document processed successfully"
        )
        
    except ValidationError as e:
        logger.warning("Validation error during document upload", extra={
            "filename": file.filename,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to process document", extra={
            "filename": file.filename,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document"
        )

@router.get("/", response_model=DocumentListResponse)
@log_api_call("get_documents")
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    """Get list of processed documents"""
    try:
        document_service = DocumentService(db)
        documents = await document_service.get_documents(skip=skip, limit=limit)
        
        return DocumentListResponse(
            success=True,
            data=documents,
            total=len(documents),
            page=skip // limit + 1,
            size=limit,
            message="Documents retrieved successfully"
        )
    except Exception as e:
        logger.error("Failed to retrieve documents", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )