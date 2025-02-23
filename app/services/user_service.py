from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from app.models.user import User
from app.crud.user import CRUDUser
from app.core.errors import NotFoundError, DatabaseError
from app.core.redis import RedisClient
from app.core.config import settings
from app.services.user_brand_service import UserBrandService
from app.core.logger import service_logger as logger
from app.core.log_helper import log_business_logic, log_database_query

class UserService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.redis = RedisClient()
        self.GLUTT_AI_BRAND_ID = settings.GLUTT_AI_BRAND_ID
        self.USER_CACHE_TTL = settings.USER_CACHE_TTL
        logger.debug("UserService initialized")

    @log_business_logic("get_or_create_user")
    async def get_or_create_user(self, user_id: int, name: str = "") -> User:
        try:
            # Check cache first
            cached_user = await self._get_from_cache(user_id)
            if cached_user:
                return User(**cached_user)

            # Get or create user
            user = await self._get_or_create_user_in_db(user_id, name)
            
            # Associate with default brand
            try:
                await self._associate_with_default_brand(user_id)
            except Exception as e:
                logger.error("Error associating user with default brand", extra={
                    "user_id": user_id,
                    "error": str(e)
                })

            # Cache the user
            await self._cache_user(user)
            return user
            
        except Exception as e:
            logger.error("Error in get_or_create_user", extra={
                "user_id": user_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error creating user: {str(e)}")

    async def _get_from_cache(self, user_id: int) -> Optional[dict]:
        """Get user from cache"""
        try:
            cache_key = f"user:{user_id}"
            cached_user = await self.redis.get(cache_key)
            if cached_user:
                logger.debug("Cache hit", extra={"user_id": user_id})
            else:
                logger.debug("Cache miss", extra={"user_id": user_id})
            return cached_user
        except Exception as e:
            logger.error("Cache error", extra={
                "user_id": user_id,
                "error": str(e)
            })
            return None

    @log_database_query("get_or_create_user")
    async def _get_or_create_user_in_db(self, user_id: int, name: str) -> User:
        """Get or create user in database"""
        return await CRUDUser.get_or_create(self.db, user_id, name)

    async def _cache_user(self, user: User) -> None:
        """Cache user data"""
        try:
            cache_key = f"user:{user.user_id}"
            await self.redis.set(
                cache_key,
                user.model_dump(),
                expire=self.USER_CACHE_TTL
            )
            logger.debug("User cached", extra={
                "user_id": user.user_id,
                "ttl": self.USER_CACHE_TTL
            })
        except Exception as e:
            logger.error("Failed to cache user", extra={
                "user_id": user.user_id,
                "error": str(e)
            })

    @log_business_logic("associate_with_default_brand")
    async def _associate_with_default_brand(self, user_id: int) -> None:
        """Associate user with default brand"""
        brand_service = UserBrandService(self.db)
        await brand_service.associate_brand(user_id, self.GLUTT_AI_BRAND_ID)