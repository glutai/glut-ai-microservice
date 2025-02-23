from typing import List, Optional
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageQueryParams
from .base import CRUDBase
from bson import ObjectId
from app.core.logger import db_logger as logger
from app.core.log_helper import log_database_query
from app.core.errors import DatabaseError

class CRUDMessage(CRUDBase[Message, MessageCreate, MessageQueryParams]):
    collection_name = "messages"
    model = Message
    
    @classmethod
    @log_database_query("get_conversation")
    async def get_conversation(
        self,
        db,
        user_brand_id: str,
        params: MessageQueryParams
    ) -> List[Message]:
        try:
            collection = self.get_collection(db)
            query = {"user_brand_id": user_brand_id}
            
            if params.before_id:
                query["_id"] = {"$lt": ObjectId(params.before_id)}
                
            cursor = collection.find(query)\
                .sort("created_at", -1)\
                .limit(params.limit)
                
            messages = await cursor.to_list(length=params.limit)
            
            logger.debug("Retrieved conversation messages", extra={
                "user_brand_id": user_brand_id,
                "message_count": len(messages),
                "limit": params.limit,
                "before_id": params.before_id
            })
            
            return [Message(**msg) for msg in messages]
            
        except Exception as e:
            logger.error("Error retrieving conversation", extra={
                "user_brand_id": user_brand_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error retrieving conversation: {str(e)}")

    @classmethod
    @log_database_query("add_message")
    async def add_message(self, db, message: MessageCreate) -> Message:
        try:
            collection = self.get_collection(db)
            message_dict = message.model_dump()
            
            result = await collection.insert_one(message_dict)
            message_dict["_id"] = result.inserted_id
            
            logger.debug("Message created", extra={
                "message_id": str(result.inserted_id),
                "user_brand_id": message.user_brand_id,
                "message_type": message.message_type
            })
            
            return Message(**message_dict)
            
        except Exception as e:
            logger.error("Error creating message", extra={
                "user_brand_id": message.user_brand_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error creating message: {str(e)}")

    @classmethod
    @log_database_query("delete_messages")
    async def delete_conversation_messages(
        self,
        db,
        user_brand_id: str
    ) -> int:
        try:
            collection = self.get_collection(db)
            result = await collection.delete_many({"user_brand_id": user_brand_id})
            
            logger.info("Deleted conversation messages", extra={
                "user_brand_id": user_brand_id,
                "deleted_count": result.deleted_count
            })
            
            return result.deleted_count
            
        except Exception as e:
            logger.error("Error deleting conversation messages", extra={
                "user_brand_id": user_brand_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error deleting conversation messages: {str(e)}")

    @classmethod
    @log_database_query("get_message_count")
    async def get_message_count(self, db, user_brand_id: str) -> int:
        try:
            collection = self.get_collection(db)
            count = await collection.count_documents({"user_brand_id": user_brand_id})
            
            logger.debug("Retrieved message count", extra={
                "user_brand_id": user_brand_id,
                "count": count
            })
            
            return count
            
        except Exception as e:
            logger.error("Error getting message count", extra={
                "user_brand_id": user_brand_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error getting message count: {str(e)}")

    @classmethod
    @log_database_query("get_messages_by_type")
    async def get_messages_by_type(
        self,
        db,
        user_brand_id: str,
        message_type: str,
        limit: int = 50
    ) -> List[Message]:
        try:
            collection = self.get_collection(db)
            query = {
                "user_brand_id": user_brand_id,
                "message_type": message_type
            }
            
            cursor = collection.find(query)\
                .sort("created_at", -1)\
                .limit(limit)
                
            messages = await cursor.to_list(length=limit)
            
            logger.debug("Retrieved messages by type", extra={
                "user_brand_id": user_brand_id,
                "message_type": message_type,
                "count": len(messages),
                "limit": limit
            })
            
            return [Message(**msg) for msg in messages]
            
        except Exception as e:
            logger.error("Error retrieving messages by type", extra={
                "user_brand_id": user_brand_id,
                "message_type": message_type,
                "error": str(e)
            })
            raise DatabaseError(f"Error retrieving messages by type: {str(e)}")

    @classmethod
    @log_database_query("mark_messages_as_read")
    async def mark_messages_as_read(
        self,
        db,
        user_brand_id: str,
        before_timestamp
    ) -> int:
        try:
            collection = self.get_collection(db)
            result = await collection.update_many(
                {
                    "user_brand_id": user_brand_id,
                    "created_at": {"$lte": before_timestamp},
                    "is_read": {"$ne": True}
                },
                {"$set": {"is_read": True}}
            )
            
            logger.debug("Marked messages as read", extra={
                "user_brand_id": user_brand_id,
                "modified_count": result.modified_count,
                "before_timestamp": before_timestamp
            })
            
            return result.modified_count
            
        except Exception as e:
            logger.error("Error marking messages as read", extra={
                "user_brand_id": user_brand_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error marking messages as read: {str(e)}")

    @classmethod
    @log_database_query("get_unread_count")
    async def get_unread_count(self, db, user_brand_id: str) -> int:
        try:
            collection = self.get_collection(db)
            count = await collection.count_documents({
                "user_brand_id": user_brand_id,
                "is_read": {"$ne": True}
            })
            
            logger.debug("Retrieved unread message count", extra={
                "user_brand_id": user_brand_id,
                "unread_count": count
            })
            
            return count
            
        except Exception as e:
            logger.error("Error getting unread message count", extra={
                "user_brand_id": user_brand_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error getting unread message count: {str(e)}")