from fastapi import APIRouter
from app.api.endpoints import users, messages, brands

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(brands.router, prefix="/brands", tags=["brands"])

