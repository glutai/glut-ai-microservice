# app/utils/document_utils.py

from typing import List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.logger import logger
from app.core.log_helper import log_business_logic

class DocumentCleanup:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["documents"]

    @log_business_logic("cleanup_failed_documents")
    async def cleanup_failed_documents(self, older_than_hours: int = 24) -> int:
        """Remove failed document processing attempts"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            result = await self.collection.delete_many({
                "status": "failed",
                "processed_at": {"$lt": cutoff_time}
            })
            
            logger.info("Cleaned up failed documents", extra={
                "deleted_count": result.deleted_count,
                "older_than_hours": older_than_hours
            })
            
            return result.deleted_count
        except Exception as e:
            logger.error("Failed to cleanup documents", extra={"error": str(e)})
            raise

    @log_business_logic("reprocess_failed_documents")
    async def reprocess_failed_documents(self) -> List[str]:
        """Mark failed documents for reprocessing"""
        try:
            result = await self.collection.update_many(
                {"status": "failed"},
                {"$set": {
                    "status": "pending",
                    "updated_at": datetime.utcnow(),
                    "retry_count": {"$inc": 1}
                }}
            )
            
            logger.info("Marked documents for reprocessing", extra={
                "modified_count": result.modified_count
            })
            
            return result.modified_count
        except Exception as e:
            logger.error("Failed to mark documents for reprocessing", extra={
                "error": str(e)
            })
            raise

    @log_business_logic("get_processing_stats")
    async def get_processing_stats(self) -> dict:
        """Get document processing statistics"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "avg_processing_time": {
                            "$avg": {
                                "$subtract": [
                                    "$processed_at",
                                    "$created_at"
                                ]
                            }
                        }
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            stats = await cursor.to_list(length=None)
            
            return {
                "status_counts": {
                    stat["_id"]: stat["count"] for stat in stats
                },
                "processing_times": {
                    stat["_id"]: stat["avg_processing_time"] 
                    for stat in stats if stat["avg_processing_time"]
                }
            }
        except Exception as e:
            logger.error("Failed to get processing stats", extra={"error": str(e)})
            raise