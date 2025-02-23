from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.core.logger import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """Create JWT access token"""
    try:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        
        logger.debug("Access token created", extra={
            "user_id": subject,
            "expires_at": expire.isoformat()
        })
        return encoded_jwt
        
    except Exception as e:
        logger.error("Failed to create access token", extra={
            "user_id": subject,
            "error": str(e)
        })
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        if not is_valid:
            logger.warning("Invalid password attempt")
        return is_valid
    except Exception as e:
        logger.error("Password verification error", extra={
            "error": str(e)
        })
        return False

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    try:
        hashed_password = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed_password
    except Exception as e:
        logger.error("Password hashing error", extra={
            "error": str(e)
        })
        raise