from fastapi import APIRouter
from app.api.endpoints import users, messages, brands, rag, document_admin, documents

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(brands.router, prefix="/brands", tags=["brands"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(document_admin.router, prefix="/document_admin", tags=["document_admin"])

