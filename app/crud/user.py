from typing import List, Optional
from datetime import datetime
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from .base import CRUDBase
from app.core.errors import DatabaseError
from app.core.logger import db_logger as logger
from app.core.log_helper import log_database_query

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    collection_name = "users"
    model = User

    def __init__(self):
        super().__init__(model=User, collection_name="users")

    @classmethod
    @log_database_query("get_user_by_id")
    async def get_by_user_id(cls, db, user_id: int) -> Optional[User]:
        try:
            collection = cls.get_collection(db)
            obj = await collection.find_one({"user_id": user_id})
            
            if obj:
                logger.debug("User found", extra={"user_id": user_id})
                return User(**obj)
                
            logger.debug("User not found", extra={"user_id": user_id})
            return None
            
        except Exception as e:
            logger.error("Error retrieving user", extra={
                "user_id": user_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error retrieving user: {str(e)}")
            
    @classmethod
    @log_database_query("get_or_create_user")
    async def get_or_create(cls, db, user_id: int, name: str = "") -> User:
        try:
            # Try to get existing user
            user = await cls.get_by_user_id(db, user_id)
            
            if user:
                logger.debug("Retrieved existing user", extra={"user_id": user_id})
                return user
                
            # Create new user if not found
            collection = cls.get_collection(db)
            user_data = {
                "user_id": user_id,
                "name": name,
                "created_at": datetime.utcnow()
            }
            
            result = await collection.insert_one(user_data)
            user_data["_id"] = result.inserted_id
            
            logger.info("Created new user", extra={
                "user_id": user_id,
                "id": str(result.inserted_id)
            })
            
            return User(**user_data)
            
        except Exception as e:
            logger.error("Error in get_or_create user", extra={
                "user_id": user_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error in get_or_create user: {str(e)}")

    @classmethod
    @log_database_query("update_user")
    async def update_user(cls, db, user_id: int, update_data: dict) -> Optional[User]:
        try:
            collection = cls.get_collection(db)
            result = await collection.update_one(
                {"user_id": user_id},
                {"$set": {**update_data, "updated_at": datetime.utcnow()}}
            )
            
            if result.modified_count > 0:
                updated_user = await cls.get_by_user_id(db, user_id)
                logger.debug("User updated successfully", extra={
                    "user_id": user_id,
                    "fields_updated": list(update_data.keys())
                })
                return updated_user
                
            logger.warning("User not found for update", extra={"user_id": user_id})
            return None
            
        except Exception as e:
            logger.error("Error updating user", extra={
                "user_id": user_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error updating user: {str(e)}")

    @classmethod
    @log_database_query("delete_user")
    async def delete_user(cls, db, user_id: int) -> bool:
        try:
            collection = cls.get_collection(db)
            result = await collection.delete_one({"user_id": user_id})
            
            success = result.deleted_count > 0
            log_level = logger.info if success else logger.warning
            
            log_level(
                "User deletion attempt",
                extra={
                    "user_id": user_id,
                    "success": success
                }
            )
            
            return success
            
        except Exception as e:
            logger.error("Error deleting user", extra={
                "user_id": user_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error deleting user: {str(e)}")