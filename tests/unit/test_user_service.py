import pytest
from app.services.user_service import UserService
from app.core.errors import NotFoundError

@pytest.mark.asyncio
async def test_get_or_create_user(db):
    service = UserService(db)
    user = await service.get_or_create_user(1, "Test User")
    
    assert user.user_id == 1
    assert user.name == "Test User"
    
    # Test retrieval of existing user
    same_user = await service.get_or_create_user(1, "Test User")
    assert same_user.id == user.id

@pytest.mark.asyncio
async def test_get_user_not_found(db):
    service = UserService(db)
    with pytest.raises(NotFoundError):
        await service.get_user(999)