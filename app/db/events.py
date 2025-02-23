from typing import Callable
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.db.mongodb import db, close_mongo_connection
from app.core.logger import db_logger as logger

def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        logger.info("Starting database connection")
        
        # Initialize MongoDB connection
        try:
            db.client = AsyncIOMotorClient(settings.MONGODB_URL)
            db.db = db.client[settings.MONGODB_DB]
            logger.info(f"Successfully connected to MongoDB database: {settings.MONGODB_DB}")
            
            # Verify connection
            await db.client.admin.command('ping')
            logger.info("Database connection verified")
            
            # Optional: Create indexes if needed
            try:
                await create_indexes(db.db)
                logger.info("Database indexes created successfully")
            except Exception as e:
                logger.error(f"Error creating database indexes: {str(e)}")
                # Don't re-raise, as the app can still function without indexes
        except Exception as e:
            logger.critical(f"Failed to connect to MongoDB: {str(e)}")
            raise  # Re-raise as the app cannot function without database
    
    return start_app

def create_stop_app_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        logger.info("Closing database connection")
        try:
            await close_mongo_connection()
            logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")
    
    return stop_app

async def create_indexes(database):
    """Create MongoDB indexes"""
    logger.info("Creating database indexes")
    
    # Users collection indexes
    await database.users.create_index("user_id", unique=True)
    logger.debug("Created index: users.user_id (unique)")
    
    await database.users.create_index("email", sparse=True)
    logger.debug("Created index: users.email (sparse)")

    # Messages collection indexes
    await database.messages.create_index([
        ("user_id", 1),
        ("brand_id", 1),
        ("created_at", -1)
    ])
    logger.debug("Created compound index: messages.user_id, brand_id, created_at")
    
    await database.messages.create_index("thread_id", sparse=True)
    logger.debug("Created index: messages.thread_id (sparse)")

    # User brands collection indexes
    await database.user_brands.create_index([
        ("user_id", 1),
        ("brand_id", 1)
    ], unique=True)
    logger.debug("Created compound index: user_brands.user_id, brand_id (unique)")
    
    await database.user_brands.create_index("last_message_at")
    logger.debug("Created index: user_brands.last_message_at")
    
    logger.info("All database indexes created successfully")