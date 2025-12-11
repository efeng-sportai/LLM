from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
import os
from datetime import datetime
from app.config import settings

# MongoDB configuration - use cloud if configured, otherwise local
def get_mongodb_url():
    """Get MongoDB URL, prioritizing cloud configuration"""
    if settings.mongodb_atlas_url:
        return settings.mongodb_atlas_url
    elif settings.mongodb_username and settings.mongodb_password and settings.mongodb_cluster:
        # Build Atlas connection string
        return f"mongodb+srv://{settings.mongodb_username}:{settings.mongodb_password}@{settings.mongodb_cluster}.mongodb.net/?retryWrites=true&w=majority"
    else:
        return settings.mongodb_url

MONGODB_URL = get_mongodb_url()
DATABASE_NAME = settings.database_name

# Global MongoDB client
client: Optional[AsyncIOMotorClient] = None
database = None

async def connect_to_mongo():
    """Create database connection"""
    global client, database
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DATABASE_NAME]
    
    # Create indexes for better performance
    await create_indexes()
    
    print(f"Connected to MongoDB: {DATABASE_NAME}")

async def close_mongo_connection():
    """Close database connection"""
    global client
    if client:
        client.close()

async def create_indexes():
    """Create database indexes for better performance"""
    # Only training_data collection - other collections removed
    # Training data collection indexes
    await database.training_data.create_index("category")
    await database.training_data.create_index("source_type")
    await database.training_data.create_index("difficulty_level")
    await database.training_data.create_index("created_at")
    await database.training_data.create_index([("prompt", "text"), ("response", "text")])

def get_database():
    """Get database instance"""
    return database

# Collections - Only training_data collection is used
def get_training_data_collection():
    """Get training data collection"""
    return database.training_data