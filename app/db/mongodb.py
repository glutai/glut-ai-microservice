from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from app.core.logger import db_logger as logger

class MongoDB:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

db = MongoDB()

async def get_database() -> AsyncIOMotorDatabase:
    if db.client is None:
        logger.info("Initializing MongoDB connection")
        try:
            db.client = AsyncIOMotorClient(settings.MONGODB_URL)
            db.db = db.client[settings.MONGODB_DB]
            
            # Verify connection
            await db.client.admin.command('ping')
            logger.debug("Database connection verified")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    return db.db

async def close_mongo_connection():
    logger.info("Closing MongoDB connection")
    if db.client is not None:
        db.client.close()
        logger.debug("MongoDB connection closed")