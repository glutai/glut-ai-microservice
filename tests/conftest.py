import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.db.mongodb import get_database

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def client():
    async with TestClient(app) as client:
        yield client

@pytest.fixture(scope="session")
async def db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB + "_test"]
    yield db
    await client.drop_database(settings.MONGODB_DB + "_test")
    client.close()
