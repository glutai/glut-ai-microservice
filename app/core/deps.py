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

async def get_current_user(
    db: AsyncIOMotorDatabase = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> dict:
    """Dependency for getting authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: int = payload.get("sub")
        
        if user_id is None:
            logger.warning("Invalid token payload - missing user_id")
            raise credentials_exception
            
        logger.debug("Token decoded successfully", extra={"user_id": user_id})
        
    except JWTError as e:
        logger.warning("JWT token validation failed", extra={
            "error": str(e)
        })
        raise credentials_exception
        
    try:
        # Get user from database
        user = await db.users.find_one({"user_id": user_id})
        if user is None:
            logger.warning("User not found in database", extra={
                "user_id": user_id
            })
            raise credentials_exception
            
        logger.debug("User authenticated successfully", extra={
            "user_id": user_id
        })
        return user
        
    except Exception as e:
        logger.error("Database error during user authentication", extra={
            "user_id": user_id,
            "error": str(e)
        })
        raise credentials_exception