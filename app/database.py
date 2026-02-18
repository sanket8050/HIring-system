"""MongoDB database connection using Motor (async)."""
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

client: AsyncIOMotorClient | None = None


def _get_client() -> AsyncIOMotorClient:
    """Get or create MongoDB client."""
    global client
    if client is None:
        client = AsyncIOMotorClient(settings.mongo_uri)
    return client


def get_candidates_collection():
    """Get the candidates collection (Motor collection - use with await for operations)."""
    return _get_client()[settings.database_name][settings.collection_name]


async def close_database():
    """Close MongoDB connection."""
    global client
    if client is not None:
        client.close()
        client = None
