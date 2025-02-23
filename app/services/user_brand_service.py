from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Tuple
from datetime import datetime
from app.models.brand import UserBrand, Brand
from app.crud.brand import CRUDUserBrand as user_brand_crud
from app.crud.brand import CRUDBrand as brand_crud
from app.crud.user import CRUDUser as user_crud
from app.core.errors import NotFoundError
from app.core.redis import RedisClient
from app.core.config import settings
from app.core.logger import service_logger as logger
from app.core.log_helper import log_business_logic, log_database_query

class UserBrandService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.redis = RedisClient()
        self.USER_BRAND_CACHE_TTL = settings.USER_CACHE_TTL
        self.GLUTT_AI_BRAND_ID = settings.GLUTT_AI_BRAND_ID
        logger.debug("UserBrandService initialized")

    @log_business_logic("get_user_brands")
    async def get_user_brands(self, user_id: int) -> List[dict]:
        """Get all brands associated with a user with full brand details"""
        try:
            # Check cache first
            cached_brands = await self._get_from_cache(user_id)
            if cached_brands:
                return cached_brands
            
            # Ensure user exists
            user = await self._get_or_create_user(user_id)
            
            # Get user brands with details
            user_brands = await self._get_user_brands_from_db(user_id)
            
            # Cache the results
            await self._cache_user_brands(user_id, user_brands)
            
            return user_brands
            
        except Exception as e:
            logger.error("Error retrieving user brands", extra={
                "user_id": user_id,
                "error": str(e)
            })
            raise

    @log_business_logic("get_or_create_user_brand")
    async def get_or_create_user_brand(
        self, 
        user_id: int, 
        brand_id: int
    ) -> Tuple[UserBrand, bool]:
        """Get user-brand association or create if it doesn't exist"""
        try:
            # Check if association exists
            user_brand = await self._get_user_brand(user_id, brand_id)
            created = False
            
            if not user_brand:
                user_brand = await self.associate_brand(user_id, brand_id)
                created = True
                logger.info("Created new user-brand association", extra={
                    "user_id": user_id,
                    "brand_id": brand_id
                })
            
            return user_brand, created
            
        except Exception as e:
            logger.error("Error in get_or_create_user_brand", extra={
                "user_id": user_id,
                "brand_id": brand_id,
                "error": str(e)
            })
            raise

    async def _get_from_cache(self, user_id: int) -> Optional[List[dict]]:
        """Get user brands from cache"""
        try:
            cache_key = f"user_brands_detailed:{user_id}"
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                logger.debug("Cache hit", extra={"user_id": user_id})
            else:
                logger.debug("Cache miss", extra={"user_id": user_id})
            return cached_data
        except Exception as e:
            logger.error("Cache error", extra={
                "user_id": user_id,
                "error": str(e)
            })
            return None

    @log_database_query("get_user")
    async def _get_or_create_user(self, user_id: int) -> dict:
        """Get or create user"""
        return await user_crud.get_or_create(self.db, user_id)

    @log_database_query("get_user_brands")
    async def _get_user_brands_from_db(self, user_id: int) -> List[dict]:
        """Get user brands from database with full details"""
        return await user_brand_crud.get_user_brands_with_details(self.db, user_id)

    async def _cache_user_brands(self, user_id: int, user_brands: List[dict]) -> None:
        """Cache user brands data"""
        try:
            cache_key = f"user_brands_detailed:{user_id}"
            await self.redis.set(
                cache_key,
                user_brands,
                expire=self.USER_BRAND_CACHE_TTL
            )
            logger.debug("User brands cached", extra={
                "user_id": user_id,
                "count": len(user_brands),
                "ttl": self.USER_BRAND_CACHE_TTL
            })
        except Exception as e:
            logger.error("Failed to cache user brands", extra={
                "user_id": user_id,
                "error": str(e)
            })

    @log_business_logic("associate_brand")
    async def associate_brand(self, user_id: int, brand_id: int) -> UserBrand:
        """Associate a brand with a user"""
        try:
            # Verify brand exists
            brand = await self._get_brand(brand_id)
            if not brand:
                logger.warning("Brand not found", extra={"brand_id": brand_id})
                raise NotFoundError(f"Brand with ID {brand_id} not found")
            
            # Create association
            user_brand = await self._create_association(user_id, brand_id)
            
            # Invalidate cache
            await self._invalidate_cache(user_id)
            
            return user_brand
            
        except Exception as e:
            logger.error("Error associating brand with user", extra={
                "user_id": user_id,
                "brand_id": brand_id,
                "error": str(e)
            })
            raise

    @log_database_query("get_brand")
    async def _get_brand(self, brand_id: int) -> Optional[Brand]:
        """Get brand from database"""
        return await brand_crud.get_by_brand_id(self.db, brand_id)

    @log_database_query("create_association")
    async def _create_association(self, user_id: int, brand_id: int) -> UserBrand:
        """Create user-brand association"""
        return await user_brand_crud.associate_brand(self.db, user_id, brand_id)

    @log_database_query("get_user_brand")
    async def _get_user_brand(self, user_id: int, brand_id: int) -> Optional[UserBrand]:
        """Get specific user-brand association"""
        return await user_brand_crud.get_user_brand(self.db, user_id, brand_id)

    @log_database_query("get_user_brand_by_id")
    async def get_by_id(self, user_brand_id: str) -> Optional[UserBrand]:
        """Get user-brand by ID"""
        return await user_brand_crud.get_by_id(self.db, user_brand_id)

    async def _invalidate_cache(self, user_id: int) -> None:
        """Invalidate user brands cache"""
        try:
            cache_key = f"user_brands:{user_id}"
            await self.redis.delete(cache_key)
            logger.debug("Cache invalidated", extra={"user_id": user_id})
        except Exception as e:
            logger.error("Failed to invalidate cache", extra={
                "user_id": user_id,
                "error": str(e)
            })

    @log_business_logic("update_last_message")
    async def update_last_message(
        self,
        user_brand_id: str,
        message: dict
    ) -> UserBrand:
        """Update the last message for a user-brand association"""
        try:
            # Verify user-brand exists
            user_brand = await self._get_user_brand_by_id(user_brand_id)
            if not user_brand:
                logger.warning("UserBrand not found", extra={"user_brand_id": user_brand_id})
                raise NotFoundError(f"UserBrand with ID {user_brand_id} not found")
            
            # Update last message
            updated_user_brand = await self._update_last_message_in_db(
                user_brand_id,
                message
            )
            
            # Invalidate cache
            await self._invalidate_cache(updated_user_brand.user_id)
            
            return updated_user_brand
            
        except Exception as e:
            logger.error("Error updating last message", extra={
                "user_brand_id": user_brand_id,
                "error": str(e)
            })
            raise

    @log_database_query("get_user_brand")
    async def _get_user_brand_by_id(self, user_brand_id: str) -> Optional[UserBrand]:
        """Get user-brand by ID"""
        return await user_brand_crud.get_by_id(self.db, user_brand_id)

    @log_database_query("update_last_message")
    async def _update_last_message_in_db(
        self,
        user_brand_id: str,
        message: dict
    ) -> UserBrand:
        """Update last message in database"""
        return await user_brand_crud.update_last_message(
            self.db,
            user_brand_id,
            message
        )

    @log_business_logic("remove_brand_association")
    async def remove_brand_association(self, user_id: int, brand_id: int) -> bool:
        """Remove a brand association from a user"""
        try:
            # Verify association exists
            user_brand = await self._get_user_brand(user_id, brand_id)
            if not user_brand:
                logger.warning("UserBrand association not found", extra={
                    "user_id": user_id,
                    "brand_id": brand_id
                })
                return False

            # Remove association
            result = await self._remove_association(user_id, brand_id)
            
            # Invalidate cache
            if result:
                await self._invalidate_cache(user_id)
                logger.info("Brand association removed", extra={
                    "user_id": user_id,
                    "brand_id": brand_id
                })
            
            return result
            
        except Exception as e:
            logger.error("Error removing brand association", extra={
                "user_id": user_id,
                "brand_id": brand_id,
                "error": str(e)
            })
            raise

    @log_database_query("remove_association")
    async def _remove_association(self, user_id: int, brand_id: int) -> bool:
        """Remove user-brand association from database"""
        return await user_brand_crud.delete_user_brand(self.db, user_id, brand_id)