from typing import List, Optional
from datetime import datetime
from app.models.brand import UserBrand, Brand
from app.schemas.brand import UserBrandCreate, UserBrandUpdate, BrandCreate
from .base import CRUDBase
from bson import ObjectId
from app.core.logger import db_logger as logger
from app.core.log_helper import log_database_query
from app.core.errors import DatabaseError

class CRUDBrand(CRUDBase[Brand, BrandCreate, None]):
    collection_name = "brands"
    model = Brand
    
    @classmethod
    @log_database_query("get_brand_by_id")
    async def get_by_brand_id(cls, db, brand_id: int) -> Optional[Brand]:
        """Get brand by Postgres ID"""
        try:
            collection = cls.get_collection(db)
            result = await collection.find_one({"brand_id": brand_id})
            
            if result:
                logger.debug("Brand found", extra={"brand_id": brand_id})
                return Brand(**result)
                
            logger.debug("Brand not found", extra={"brand_id": brand_id})
            return None
            
        except Exception as e:
            logger.error("Error retrieving brand", extra={
                "brand_id": brand_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error retrieving brand: {str(e)}")

class CRUDUserBrand(CRUDBase[UserBrand, UserBrandCreate, UserBrandUpdate]):
    collection_name = "user_brands"
    model = UserBrand

    @classmethod
    @log_database_query("get_user_brands")
    async def get_user_brands(cls, db, user_id: int) -> List[UserBrand]:
        try:
            brands = await cls.get_by_query(
                db,
                query={"user_id": user_id},
                limit=100
            )
            
            logger.debug("Retrieved user brands", extra={
                "user_id": user_id,
                "count": len(brands)
            })
            
            return brands
            
        except Exception as e:
            logger.error("Error retrieving user brands", extra={
                "user_id": user_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error retrieving user brands: {str(e)}")

    @classmethod
    @log_database_query("get_user_brands_with_details")
    async def get_user_brands_with_details(cls, db, user_id: int) -> List[dict]:
        """Get user brands with full brand details using aggregation pipeline"""
        try:
            user_brands_collection = cls.get_collection(db)
            
            pipeline = [
                {"$match": {"user_id": user_id}},
                {
                    "$lookup": {
                        "from": "brands",
                        "localField": "brand_id",
                        "foreignField": "brand_id",
                        "as": "brand_details"
                    }
                },
                {"$unwind": {"path": "$brand_details", "preserveNullAndEmptyArrays": True}},
                {"$sort": {"last_message_at": -1}}
            ]
            
            cursor = user_brands_collection.aggregate(pipeline)
            results = await cursor.to_list(length=100)
            
            logger.debug("Retrieved user brands with details", extra={
                "user_id": user_id,
                "count": len(results)
            })
            
            return results
            
        except Exception as e:
            logger.error("Error retrieving user brands with details", extra={
                "user_id": user_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error retrieving user brands with details: {str(e)}")

    @classmethod
    @log_database_query("get_user_brand")
    async def get_user_brand(
        cls,
        db,
        user_id: int,
        brand_id: int
    ) -> Optional[UserBrand]:
        try:
            collection = cls.get_collection(db)
            result = await collection.find_one({
                "user_id": user_id,
                "brand_id": brand_id
            })
            
            if result:
                logger.debug("User brand found", extra={
                    "user_id": user_id,
                    "brand_id": brand_id
                })
                return UserBrand(**result)
                
            logger.debug("User brand not found", extra={
                "user_id": user_id,
                "brand_id": brand_id
            })
            return None
            
        except Exception as e:
            logger.error("Error retrieving user brand", extra={
                "user_id": user_id,
                "brand_id": brand_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error retrieving user brand: {str(e)}")
    
    @classmethod
    @log_database_query("get_by_id")
    async def get_by_id(cls, db, id: str) -> Optional[UserBrand]:
        try:
            collection = cls.get_collection(db)
            result = await collection.find_one({"_id": ObjectId(id)})
            
            if result:
                logger.debug("User brand found by ID", extra={"id": id})
                return UserBrand(**result)
                
            logger.debug("User brand not found by ID", extra={"id": id})
            return None
            
        except Exception as e:
            logger.error("Error retrieving user brand by ID", extra={
                "id": id,
                "error": str(e)
            })
            raise DatabaseError(f"Error retrieving user brand by ID: {str(e)}")
    
    @classmethod
    @log_database_query("associate_brand")
    async def associate_brand(
        cls,
        db,
        user_id: int,
        brand_id: int
    ) -> UserBrand:
        try:
            collection = cls.get_collection(db)
            user_brand = UserBrandCreate(user_id=user_id, brand_id=brand_id)
            
            result = await collection.update_one(
                {"user_id": user_id, "brand_id": brand_id},
                {
                    "$setOnInsert": {
                        **user_brand.model_dump(),
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.debug("Brand association created/updated", extra={
                "user_id": user_id,
                "brand_id": brand_id,
                "upserted": result.upserted_id is not None
            })
            
            return await cls.get_user_brand(db, user_id, brand_id)
            
        except Exception as e:
            logger.error("Error associating brand", extra={
                "user_id": user_id,
                "brand_id": brand_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error associating brand: {str(e)}")

    @classmethod
    @log_database_query("update_last_message")
    async def update_last_message(
        cls,
        db,
        user_brand_id: str,
        message: dict
    ) -> UserBrand:
        try:
            collection = cls.get_collection(db)
            update_data = {
                "last_message_at": datetime.utcnow(),
                "last_message": message,
                "updated_at": datetime.utcnow()
            }
            
            result = await collection.update_one(
                {"_id": ObjectId(user_brand_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.debug("Last message updated", extra={
                    "user_brand_id": user_brand_id
                })
            else:
                logger.warning("No document updated", extra={
                    "user_brand_id": user_brand_id
                })
            
            return await cls.get_by_id(db, user_brand_id)
            
        except Exception as e:
            logger.error("Error updating last message", extra={
                "user_brand_id": user_brand_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error updating last message: {str(e)}")

    @classmethod
    @log_database_query("delete_user_brand")
    async def delete_user_brand(
        cls,
        db,
        user_id: int,
        brand_id: int
    ) -> bool:
        try:
            collection = cls.get_collection(db)
            result = await collection.delete_one({
                "user_id": user_id,
                "brand_id": brand_id
            })
            
            success = result.deleted_count > 0
            log_level = logger.info if success else logger.warning
            
            log_level(
                "Brand association deletion attempt",
                extra={
                    "user_id": user_id,
                    "brand_id": brand_id,
                    "success": success
                }
            )
            
            return success
            
        except Exception as e:
            logger.error("Error deleting brand association", extra={
                "user_id": user_id,
                "brand_id": brand_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error deleting brand association: {str(e)}")

    @classmethod
    @log_database_query("get_brand_user_count")
    async def get_brand_user_count(cls, db, brand_id: int) -> int:
        try:
            collection = cls.get_collection(db)
            count = await collection.count_documents({"brand_id": brand_id})
            
            logger.debug("Retrieved brand user count", extra={
                "brand_id": brand_id,
                "count": count
            })
            
            return count
            
        except Exception as e:
            logger.error("Error getting brand user count", extra={
                "brand_id": brand_id,
                "error": str(e)
            })
            raise DatabaseError(f"Error getting brand user count: {str(e)}")