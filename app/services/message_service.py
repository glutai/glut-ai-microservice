from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageQueryParams
from app.crud.message import CRUDMessage as message_crud
from app.crud.brand import CRUDUserBrand as user_brand_crud
from app.core.redis import RedisClient
from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.logger import service_logger as logger
from app.core.log_helper import log_business_logic, log_database_query

class MessageService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.redis = RedisClient()
        self.MESSAGE_CACHE_TTL = settings.MESSAGE_CACHE_TTL
        logger.debug("MessageService initialized")

    @log_business_logic("get_messages")
    async def get_messages(
        self,
        user_brand_id: str,
        **params: dict
    ) -> List[Message]:
        """Get messages for a specific user-brand association"""
        params = MessageQueryParams(**params)
        cache_key = f"messages:{user_brand_id}:{params.limit}:{params.before_id}"
        
        # Try cache first
        cached_messages = await self._get_from_cache(cache_key)
        if cached_messages:
            return [Message(**msg) for msg in cached_messages]
        
        # Cache miss, get from database
        messages = await self._get_messages_from_db(user_brand_id, params)
        messages.reverse()
        
        # Cache the results
        await self._cache_messages(cache_key, messages)
        
        return messages

    @log_database_query("get_messages")
    async def _get_messages_from_db(
        self,
        user_brand_id: str,
        params: MessageQueryParams
    ) -> List[Message]:
        """Get messages from database"""
        try:
            return await message_crud.get_conversation(
                self.db,
                user_brand_id,
                params
            )
        except Exception as e:
            logger.error("Failed to get messages from database", extra={
                "user_brand_id": user_brand_id,
                "error": str(e)
            })
            raise

    async def _get_from_cache(self, cache_key: str) -> Optional[List[dict]]:
        """Get messages from cache"""
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                logger.debug("Cache hit", extra={"cache_key": cache_key})
                return cached_data
            logger.debug("Cache miss", extra={"cache_key": cache_key})
            return None
        except Exception as e:
            logger.error("Cache read error", extra={
                "cache_key": cache_key,
                "error": str(e)
            })
            return None

    async def _cache_messages(self, cache_key: str, messages: List[Message]) -> None:
        """Cache messages with TTL"""
        try:
            await self.redis.set(
                cache_key,
                [msg.model_dump() for msg in messages],
                expire=self.MESSAGE_CACHE_TTL
            )
            logger.debug("Messages cached", extra={
                "cache_key": cache_key,
                "ttl": self.MESSAGE_CACHE_TTL
            })
        except Exception as e:
            logger.error("Failed to cache messages", extra={
                "cache_key": cache_key,
                "error": str(e)
            })

    @log_business_logic("add_message")
    async def add_message(self, message: MessageCreate) -> Message:
        """Create a new message and update related data"""
        # Validate user_brand exists
        user_brand = await self._get_user_brand(message.user_brand_id)
        if not user_brand:
            logger.warning("UserBrand not found", extra={
                "user_brand_id": message.user_brand_id
            })
            raise NotFoundError(f"UserBrand with ID {message.user_brand_id} not found")
        
        # Create message
        new_message = await self._create_message(message)
        
        # Update related data
        await self._handle_message_creation(message.user_brand_id, new_message)
        
        return new_message

    @log_database_query("get_user_brand")
    async def _get_user_brand(self, user_brand_id: str) -> Optional[dict]:
        """Get user-brand association"""
        return await user_brand_crud.get_by_id(self.db, user_brand_id)

    @log_database_query("create_message")
    async def _create_message(self, message: MessageCreate) -> Message:
        """Create new message in database"""
        return await message_crud.add_message(self.db, message)

    async def _handle_message_creation(self, user_brand_id: str, message: Message) -> None:
        """Handle post-message creation tasks"""
        try:
            # Invalidate cache
            await self._invalidate_message_cache(user_brand_id)
            
            # Update last message
            await self._update_last_message(user_brand_id, message)
            
            logger.debug("Post-message creation tasks completed", extra={
                "user_brand_id": user_brand_id,
                "message_id": str(message.id)
            })
        except Exception as e:
            logger.error("Failed to handle message creation tasks", extra={
                "user_brand_id": user_brand_id,
                "message_id": str(message.id),
                "error": str(e)
            })
            raise

    async def _invalidate_message_cache(self, user_brand_id: str) -> None:
        """Invalidate message cache for user-brand"""
        cache_key = f"messages:{user_brand_id}:*"
        try:
            await self.redis.delete(cache_key)
            logger.debug("Cache invalidated", extra={"pattern": cache_key})
        except Exception as e:
            logger.error("Failed to invalidate cache", extra={
                "pattern": cache_key,
                "error": str(e)
            })

    @log_database_query("update_last_message")
    async def _update_last_message(self, user_brand_id: str, message: Message) -> None:
        """Update last message in user-brand"""
        await user_brand_crud.update_last_message(
            self.db,
            user_brand_id,
            message.model_dump()
        )

    @log_business_logic("get_messages_by_user_and_brand")
    async def get_messages_by_user_and_brand(
        self,
        user_id: int,
        brand_id: int,
        **params: dict
    ) -> List[Message]:
        """Get messages between a user and brand"""
        try:
            # Get user-brand association
            user_brand = await user_brand_crud.get_user_brand(self.db, user_id, brand_id)
            if not user_brand:
                logger.warning("No user-brand association found", extra={
                    "user_id": user_id,
                    "brand_id": brand_id
                })
                return []
            
            logger.debug("Found user-brand association", extra={
                "user_brand_id": str(user_brand.id),
                "user_id": user_id,
                "brand_id": brand_id
            })
            
            # Get messages using the association
            return await self.get_messages(str(user_brand.id), **params)
        except Exception as e:
            logger.error("Failed to get messages by user and brand", extra={
                "user_id": user_id,
                "brand_id": brand_id,
                "error": str(e)
            })
            raise