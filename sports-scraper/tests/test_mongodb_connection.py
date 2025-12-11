#!/usr/bin/env python3
"""
Test script to verify MongoDB cloud connection
Run this to test your cloud MongoDB setup before starting the main application
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings

async def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    print("Testing MongoDB Cloud Connection...")
    print(f"Connection URL: {settings.mongodb_atlas_url or settings.mongodb_url}")
    print(f"Database: {settings.database_name}")
    print("-" * 50)
    
    try:
        # Get connection URL
        if settings.mongodb_atlas_url:
            url = settings.mongodb_atlas_url
        elif settings.mongodb_username and settings.mongodb_password and settings.mongodb_cluster:
            url = f"mongodb+srv://{settings.mongodb_username}:{settings.mongodb_password}@{settings.mongodb_cluster}.mongodb.net/?retryWrites=true&w=majority"
        else:
            url = settings.mongodb_url
            
        # Connect to MongoDB
        client = AsyncIOMotorClient(url)
        database = client[settings.database_name]
        
        # Test connection
        print("Connecting to MongoDB...")
        await client.admin.command('ping')
        print("Connection successful!")
        
        # Test database operations
        print("\nTesting database operations...")
        
        # Test documents collection
        documents = database.documents
        await documents.create_index("title")
        print("Documents collection ready")
        
        # Test interactions collection
        interactions = database.user_interactions
        await interactions.create_index("session_id")
        print("Interactions collection ready")
        
        # Test inserting a sample document
        test_doc = {
            "title": "Connection Test Document",
            "content": "This is a test document to verify MongoDB cloud connection",
            "source_type": "test",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "is_active": True
        }
        
        result = await documents.insert_one(test_doc)
        print(f"Test document inserted with ID: {result.inserted_id}")
        
        # Test reading the document
        retrieved_doc = await documents.find_one({"_id": result.inserted_id})
        if retrieved_doc:
            print(f"Document retrieved: {retrieved_doc['title']}")
        
        # Clean up test document
        await documents.delete_one({"_id": result.inserted_id})
        print("Test document cleaned up")
        
        # Get database stats
        stats = await database.command("dbStats")
        print(f"\nDatabase Stats:")
        print(f"   Collections: {stats.get('collections', 0)}")
        print(f"   Data Size: {stats.get('dataSize', 0)} bytes")
        print(f"   Storage Size: {stats.get('storageSize', 0)} bytes")
        
        print("\nMongoDB Cloud Connection Test PASSED!")
        print("Your FastAPI backend is ready to use cloud MongoDB!")
        
    except Exception as e:
        print(f"\nConnection failed: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check your MongoDB Atlas connection string")
        print("2. Verify network access is configured (0.0.0.0/0 for testing)")
        print("3. Ensure username/password are correct")
        print("4. Check if your IP is whitelisted in Atlas")
        print("5. Verify the database name exists")
        
        return False
    
    finally:
        if 'client' in locals():
            client.close()
    
    return True

async def main():
    """Main test function"""
    print("MongoDB Cloud Connection Tester")
    print("=" * 50)
    
    # Check environment variables
    print("Checking configuration...")
    if settings.mongodb_atlas_url:
        print("Using MongoDB Atlas URL")
    elif settings.mongodb_username and settings.mongodb_password and settings.mongodb_cluster:
        print("Using MongoDB Atlas credentials")
    else:
        print("Using local MongoDB configuration")
    
    print(f"Database name: {settings.database_name}")
    
    # Run the test
    success = await test_mongodb_connection()
    
    if success:
        print("\nNext steps:")
        print("1. Start your FastAPI server: python3 main.py")
        print("2. Test the API: python3 example_usage.py")
        print("3. View API docs: http://localhost:8000/docs")
    else:
        print("\nPlease fix the connection issues before proceeding")
        print("See MONGODB_CLOUD_SETUP.md for detailed instructions")

if __name__ == "__main__":
    asyncio.run(main())
