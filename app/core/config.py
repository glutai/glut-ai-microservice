from pydantic_settings import BaseSettings
from typing import Literal, Optional, Dict, Any, List
from functools import lru_cache

class Settings(BaseSettings):
    # API configs
    PROJECT_NAME: str = "Glutt.ai API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # MongoDB configs
    MONGO_PASSWORD: str
    MONGO_USER: str
    MONGODB_URL: str
    MONGODB_DB: str = "ai_services"
    DB_NAME: str = 'ai_services'
    
    # Security configs
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_ALGORITHM: str = "HS256"
    
    # CORS configs
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Default brand config
    GLUTT_AI_BRAND_ID: int 

    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis123"

    # Cache TTLs
    USER_CACHE_TTL: int = 3600  # 1 hour
    MESSAGE_CACHE_TTL: int = 300  # 5 minutes
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["text", "json"] = "text"
    LOG_TO_CONSOLE: bool = True
    LOG_TO_FILE: bool = True
    LOG_DIR: str = "logs"
    LOG_ROTATION_TYPE: Literal["size", "time"] = "size"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10 MB
    LOG_ROTATION_WHEN: str = "midnight"
    LOG_ROTATION_INTERVAL: int = 1
    LOG_BACKUP_COUNT: int = 5
    
    # Request Logging
    LOG_REQUEST_DETAILS: bool = True
    LOG_RESPONSE_DETAILS: bool = True
    LOG_REQUEST_HEADERS: bool = False  # Set to True only in development
    LOG_REQUEST_BODY: bool = False  # Set to True only in development
    
    # Performance Logging
    LOG_SLOW_REQUESTS: bool = True
    LOG_SLOW_THRESHOLD_MS: int = 500  # Log requests taking more than 500ms
    

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
