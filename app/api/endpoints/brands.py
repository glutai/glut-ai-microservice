from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
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
async def get_user_brands(user_id: int, db=Depends(get_db)):
    """Get all brands associated with a user with detailed brand information"""
    try:
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
    except DatabaseError as e:
        logger.error("Database error retrieving user brands", extra={
            "user_id": user_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Unexpected error retrieving user brands", extra={
            "user_id": user_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.post("/user/{user_id}/brand/{brand_id}", response_model=UserBrandResponse)
async def associate_brand(user_id: int, brand_id: int, db=Depends(get_db)):
    """Associate a brand with a user"""
    try:
        user_brand_service = UserBrandService(db)
        user_brand = await user_brand_service.associate_brand(user_id, brand_id)
        return UserBrandResponse(
            success=True,
            data=user_brand,
            message="Brand associated with user successfully"
        )
    except NotFoundError as e:
        logger.warning("Brand association not found", extra={
            "user_id": user_id,
            "brand_id": brand_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error associating brand with user", extra={
            "user_id": user_id,
            "brand_id": brand_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.post("/", response_model=BrandResponse)
async def create_brand(brand: BrandCreate, db=Depends(get_db)):
    """Create a new brand"""
    try:
        brand_service = BrandService(db)
        new_brand = await brand_service.create_brand(brand)
        return BrandResponse(
            success=True,
            data=new_brand,
            message="Brand created successfully"
        )
    except Exception as e:
        logger.error("Error creating brand", extra={
            "brand_id": brand.brand_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(brand_id: int, db=Depends(get_db)):
    """Get a brand by ID"""
    try:
        brand_service = BrandService(db)
        brand = await brand_service.get_brand(brand_id)
        if not brand:
            raise NotFoundError(f"Brand with ID {brand_id} not found")
        return BrandResponse(
            success=True,
            data=brand,
            message="Brand retrieved successfully"
        )
    except NotFoundError as e:
        logger.warning("Brand not found", extra={
            "brand_id": brand_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error retrieving brand", extra={
            "brand_id": brand_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )