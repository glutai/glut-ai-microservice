from typing import Generator, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from app.db.mongodb import get_database
from app.core.logger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_db() -> AsyncIOMotorDatabase:
    """Dependency for getting MongoDB database instance"""
    try:
        db = await get_database()
        logger.debug("Database connection retrieved successfully")
        return db
    except Exception as e:
        logger.error("Failed to get database connection", extra={
            "error": str(e)
        })
        raise

