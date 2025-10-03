from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class Database:
    """Class for database management"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> None:
        """Connect to the database"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.client[settings.DATABASE_NAME]
            await self.create_indexes()
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def get_database(self) -> AsyncIOMotorDatabase:
        """
        Get database instance
        
        Returns:
            AsyncIOMotorDatabase: Database instance
        """
        if self.db is None:
            await self.connect()
        return self.db
    
    async def create_indexes(self) -> None:
        """Create database indexes"""
        # Indexes for users
        await self.db.users.create_index("email", unique=True)
        await self.db.users.create_index("full_name")
        await self.db.users.create_index("roles")
        await self.db.users.create_index("is_active")
        
        # Indexes for travels
        await self.db.travels.create_index("user_id")
        await self.db.travels.create_index("status")
        await self.db.travels.create_index("created_at")
        
        # Indexes for messages
        await self.db.messages.create_index("travel_id")
        await self.db.messages.create_index("user_id")
        await self.db.messages.create_index("created_at")
        
        # Indexes for notifications
        await self.db.notifications.create_index("user_id")
        await self.db.notifications.create_index("read")
        await self.db.notifications.create_index("created_at")
        
        logger.info("Database indexes created")

def format_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format MongoDB document
    
    Args:
        document: MongoDB document
    
    Returns:
        Dict[str, Any]: Formatted document
    """
    if not document:
        return {}
    
    # Convert ObjectId to string
    if "_id" in document:
        document["_id"] = str(document["_id"])
    
    # Convert dates to ISO
    for key, value in document.items():
        if isinstance(value, datetime):
            document[key] = value.isoformat()
    
    return document

def parse_object_id(id_str: str) -> ObjectId:
    """
    Convert string to ObjectId
    
    Args:
        id_str: ID in string format
    
    Returns:
        ObjectId: ID in ObjectId format
    
    Raises:
        ValueError: If the ID is not valid
    """
    try:
        return ObjectId(id_str)
    except Exception as e:
        raise ValueError(f"Invalid ObjectId: {str(e)}")

def build_query(
    filters: Dict[str, Any],
    search_fields: Optional[List[str]] = None,
    search_term: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build MongoDB query
    
    Args:
        filters: Filters to apply
        search_fields: Fields for search
        search_term: Search term
    
    Returns:
        Dict[str, Any]: MongoDB query
    """
    query = {}
    
    # Apply filters
    for key, value in filters.items():
        if value is not None:
            query[key] = value
    
    # Apply search
    if search_term and search_fields:
        search_query = []
        for field in search_fields:
            search_query.append({field: {"$regex": search_term, "$options": "i"}})
        if search_query:
            query["$or"] = search_query
    
    return query

# Global database instance
db = Database()

# Functions to get collections
async def get_users_collection():
    """Get users collection"""
    database = await db.get_database()
    return database.users

async def get_travels_collection():
    """Get travels collection"""
    database = await db.get_database()
    return database.travels

async def get_messages_collection():
    """Get messages collection"""
    database = await db.get_database()
    return database.messages

async def get_notifications_collection():
    """Get notifications collection"""
    database = await db.get_database()
    return database.notifications

# Aliases for compatibility
users_collection = get_users_collection
travels_collection = get_travels_collection
messages_collection = get_messages_collection
notifications_collection = get_notifications_collection 