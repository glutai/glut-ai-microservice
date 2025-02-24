# app/services/document_service.py

import tempfile
import os
from typing import Optional, List, BinaryIO
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import VertexAIEmbeddings
from app.models.document import Document
from app.core.logger import service_logger as logger
from app.core.log_helper import log_business_logic
from app.core.config import settings
from app.core.errors import ValidationError, DatabaseError

class DocumentService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["documents"]
        self.embeddings = VertexAIEmbeddings(model=settings.EMBEDDINGS_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP
        )
        self.vectorstore_path = "vectorstores"  # Base directory for vector stores
        os.makedirs(self.vectorstore_path, exist_ok=True)
        logger.debug("DocumentService initialized")

    def _get_vectorstore_path(self, document_id: str) -> str:
        """Get path for storing vectorstore files"""
        return os.path.join(self.vectorstore_path, f"vectorstore_{document_id}")

    @log_business_logic("process_pdf")
    async def process_pdf(
        self,
        file: BinaryIO,
        title: str,
        metadata: Optional[dict] = None
    ) -> Document:
        """Process PDF file and create vector store"""
        if metadata is None:
            metadata = {}

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            try:
                # Write uploaded file to temp file
                temp_file.write(file.read())
                temp_file.flush()

                # Load and process document
                loader = PDFPlumberLoader(temp_file.name)
                docs = loader.load()
                
                # Split documents
                splits = self.text_splitter.split_documents(docs)
                
                # Create vector store
                vectorstore = FAISS.from_documents(splits, self.embeddings)
                
                # Store document metadata
                document = await self._store_document(
                    title=title,
                    content="\n".join(d.page_content for d in docs),
                    metadata={
                        **metadata,
                        "num_pages": len(docs),
                        "num_chunks": len(splits),
                        "chunk_size": settings.RAG_CHUNK_SIZE,
                        "chunk_overlap": settings.RAG_CHUNK_OVERLAP
                    }
                )

                # Save vectorstore
                await self.save_vectorstore(document.id, vectorstore)

                logger.info("PDF processed successfully", extra={
                    "title": title,
                    "num_pages": len(docs),
                    "num_chunks": len(splits),
                    "document_id": str(document.id)
                })

                return document

            except Exception as e:
                logger.error("Failed to process PDF", extra={
                    "title": title,
                    "error": str(e)
                })
                raise ValidationError(f"Failed to process PDF: {str(e)}")
            finally:
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning("Failed to delete temporary file", extra={
                        "error": str(e)
                    })

    @log_business_logic("save_vectorstore")
    async def save_vectorstore(self, document_id: str, vectorstore: FAISS) -> None:
        """Save vectorstore to disk"""
        try:
            # Convert string ID to ObjectId if needed
            doc_id = str(document_id)
            save_path = self._get_vectorstore_path(doc_id)
            vectorstore.save_local(save_path)
            
            logger.info("Vectorstore saved successfully", extra={
                "document_id": doc_id,
                "save_path": save_path
            })
        except Exception as e:
            logger.error("Failed to save vectorstore", extra={
                "document_id": str(document_id),
                "error": str(e)
            })
            raise DatabaseError("Failed to save vectorstore")

    @log_business_logic("load_vectorstore")
    async def load_vectorstore(self, document_id: str) -> FAISS:
        """Load vectorstore from disk"""
        try:
            load_path = self._get_vectorstore_path(document_id)
            
            if not os.path.exists(load_path):
                raise ValidationError(f"Vectorstore not found for document {document_id}")
            
            vectorstore = FAISS.load_local(load_path, self.embeddings, allow_dangerous_deserialization = True)
            
            logger.info("Vectorstore loaded successfully", extra={
                "document_id": str(document_id),
                "load_path": load_path
            })
            
            return vectorstore
        except Exception as e:
            logger.error("Failed to load vectorstore", extra={
                "document_id": str(document_id),
                "error": str(e)
            })
            raise

    @log_business_logic("delete_vectorstore")
    async def delete_vectorstore(self, document_id: str) -> None:
        """Delete vectorstore from disk"""
        try:
            path = self._get_vectorstore_path(document_id)
            if os.path.exists(path):
                os.rmdir(path)
                logger.info("Vectorstore deleted successfully", extra={
                    "document_id": str(document_id)
                })
        except Exception as e:
            logger.error("Failed to delete vectorstore", extra={
                "document_id": str(document_id),
                "error": str(e)
            })
            raise

    async def _store_document(
        self,
        title: str,
        content: str,
        metadata: dict
    ) -> Document:
        """Store document in database"""
        try:
            doc = Document(
                title=title,
                content=content,
                metadata=metadata,
                source_type="pdf",
                embedding_model=settings.EMBEDDINGS_MODEL,
                status="processed"
            )
            
            result = await self.collection.insert_one(doc.model_dump())
            doc.id = str(result.inserted_id)
            
            logger.info("Document stored in database", extra={
                "document_id": str(doc.id),
                "title": title
            })
            
            return doc
        except Exception as e:
            logger.error("Failed to store document", extra={"error": str(e)})
            raise DatabaseError("Failed to store document")

    @log_business_logic("get_documents")
    async def get_documents(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Get list of processed documents"""
        try:
            cursor = self.collection.find()\
                .sort("processed_at", -1)\
                .skip(skip)\
                .limit(limit)
            
            documents = await cursor.to_list(length=limit)
            return [Document(**doc) for doc in documents]
        except Exception as e:
            logger.error("Failed to retrieve documents", extra={"error": str(e)})
            raise DatabaseError("Failed to retrieve documents")