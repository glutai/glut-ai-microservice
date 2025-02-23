from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.log_helper import log_api_call
from app.services.user_brand_service import UserBrandService
from app.services.brand_service import BrandService
from app.models.brand import UserBrand, Brand
from app.schemas.brand import (
    UserBrandListResponse, UserBrandResponse,
    BrandCreate, BrandResponse
)
from app.core.deps import get_db
from app.core.errors import DatabaseError, NotFoundError
from app.core.logger import api_logger as logger

router = APIRouter()

@router.get("/user/{user_id}", response_model=UserBrandListResponse)
@log_api_call("get_user_brands")
async def get_user_brands(user_id: int, db=Depends(get_db)):
    """Get all brands associated with a user with detailed brand information"""

    user_brand_service = UserBrandService(db)
    user_brands = await user_brand_service.get_user_brands(user_id)
    
    return UserBrandListResponse(
        success=True,
        data=user_brands,
        total=len(user_brands),
        page=1,
        size=len(user_brands),
        message="Brands retrieved successfully"
    )
   
@router.post("/", response_model=BrandResponse)
@log_api_call("create_brand")
async def create_brand(brand: BrandCreate, db=Depends(get_db)):
    """Create a new brand"""
    brand_service = BrandService(db)
    new_brand = await brand_service.create_brand(brand)
    return BrandResponse(
        success=True,
        data=new_brand,
        message="Brand created successfully"
    )
   

@router.get("/{brand_id}", response_model=BrandResponse)
@log_api_call("get_brand")
async def get_brand(brand_id: int, db=Depends(get_db)):
    """Get a brand by ID"""

    brand_service = BrandService(db)
    brand = await brand_service.get_brand(brand_id)
    if not brand:
        raise NotFoundError(f"Brand with ID {brand_id} not found")
    return BrandResponse(
        success=True,
        data=brand,
        message="Brand retrieved successfully"
    )
    