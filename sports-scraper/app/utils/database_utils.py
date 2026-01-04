"""
Database Utilities
Helper functions for database operations
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import asyncio


def get_connection_string(
    atlas_url: Optional[str] = None,
    username: Optional[str] = None, 
    password: Optional[str] = None,
    cluster: Optional[str] = None,
    local_url: Optional[str] = None
) -> str:
    """
    Build MongoDB connection string with priority order
    
    Args:
        atlas_url: Full Atlas connection string
        username: Atlas username
        password: Atlas password  
        cluster: Atlas cluster name
        local_url: Local MongoDB URL
        
    Returns:
        MongoDB connection string
    """
    if atlas_url:
        return atlas_url
    elif username and password and cluster:
        return f"mongodb+srv://{username}:{password}@{cluster}.mongodb.net/?retryWrites=true&w=majority"
    elif local_url:
        return local_url
    else:
        return "mongodb://localhost:27017"


async def test_connection(connection_string: str, database_name: str) -> bool:
    """
    Test MongoDB connection
    
    Args:
        connection_string: MongoDB connection string
        database_name: Database name to test
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        client = AsyncIOMotorClient(connection_string)
        
        # Test connection with ping
        await client.admin.command('ping')
        
        # Test database access
        db = client[database_name]
        collections = await db.list_collection_names()
        
        await client.close()
        return True
    except Exception:
        return False


def format_collection_name(name: str) -> str:
    """
    Format collection name to follow MongoDB conventions
    
    Args:
        name: Raw collection name
        
    Returns:
        Formatted collection name (lowercase, underscores)
    """
    return name.lower().replace(' ', '_').replace('-', '_')