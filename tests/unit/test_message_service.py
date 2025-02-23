import pytest
from app.services.message_service import MessageService
from app.schemas.message import MessageCreate, MessageQueryParams
from app.models.message import MessageType

@pytest.mark.asyncio
async def test_add_and_get_message(db):
    service = MessageService(db)
    
    # Create test message
    message_data = MessageCreate(
        user_id=1,
        brand_id=1,
        content={"text": "Test message"},
        message_type=MessageType.MESSAGE,
        sender_type="user",
        sender_id=1
    )
    
    message = await service.add_message(message_data)
    assert message.user_id == 1
    assert message.content["text"] == "Test message"
    
    # Test message retrieval
    params = MessageQueryParams(limit=10)
    messages = await service.get_messages(1, 1, params)
    assert len(messages) > 0
    assert messages[0].id == message.id
