from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from app.models.brand import Brand, UserBrand
from app.crud.brand import CRUDBrand as brand_crud
from app.crud.brand import CRUDUserBrand as user_brand_crud
from app.schemas.brand import BrandCreate
from app.core.errors import NotFoundError
from app.core.logger import service_logger as logger
from app.core.log_helper import log_business_logic, log_database_query

class BrandService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        logger.debug("BrandService initialized")

    @log_business_logic("get_brand")
    async def get_brand(self, brand_id: int) -> Optional[Brand]:
        """Get a brand by ID"""
        try:
            brand = await self._get_brand_from_db(brand_id)
            if not brand:
                logger.warning("Brand not found", extra={"brand_id": brand_id})
            return brand
        except Exception as e:
            logger.error("Error retrieving brand", extra={
                "brand_id": brand_id,
                "error": str(e)
            })
            raise

    @log_database_query("get_brand")
    async def _get_brand_from_db(self, brand_id: int) -> Optional[Brand]:
        """Get brand from database"""
        return await brand_crud.get_by_brand_id(self.db, brand_id)
        
    @log_business_logic("create_brand")
    async def create_brand(self, brand_data: BrandCreate) -> Brand:
        """Create a new brand"""
        try:
            # Check if brand already exists
            existing_brand = await self._get_brand_from_db(brand_data.brand_id)
            if existing_brand:
                logger.warning("Brand already exists", extra={
                    "brand_id": brand_data.brand_id
                })
                return existing_brand

            # Create new brand
            new_brand = await self._create_brand_in_db(brand_data)
            logger.info("Brand created successfully", extra={
                "brand_id": new_brand.brand_id,
                "name": new_brand.name
            })
            return new_brand
        except Exception as e:
            logger.error("Error creating brand", extra={
                "brand_data": brand_data.model_dump(),
                "error": str(e)
            })
            raise

    @log_database_query("create_brand")
    async def _create_brand_in_db(self, brand_data: BrandCreate) -> Brand:
        """Create brand in database"""
        return await brand_crud.create(self.db, brand_data)