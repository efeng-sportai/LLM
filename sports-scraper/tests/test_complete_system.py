#!/usr/bin/env python3
"""
Complete system test - MongoDB connection, data creation, feedback, and training data conversion
"""

import asyncio
import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Import our modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings
from app.database import get_mongodb_url, get_database

async def test_complete_system():
    """Test the complete SportAI system end-to-end"""
    print("SportAI Complete System Test")
    print("=" * 50)
    
    # 1. Test MongoDB Connection
    print("\n1. Testing MongoDB Connection...")
    try:
        client = AsyncIOMotorClient(get_mongodb_url())
        database = client[settings.database_name]
        
        # Test connection
        await client.admin.command('ping')
        print("SUCCESS: MongoDB connection established")
        
        # Get collections
        documents_collection = database.documents
        interactions_collection = database.user_interactions
        feedback_collection = database.user_feedback
        training_collection = database.training_data
        
        print("SUCCESS: All collections accessible")
        
    except Exception as e:
        print(f"ERROR: MongoDB connection failed: {e}")
        return False
    
    # 2. Create Sample Document
    print("\n2. Creating Sample Document...")
    try:
        sample_document = {
            "title": "Machine Learning Basics",
            "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.",
            "source_type": "manual",
            "source_url": "https://example.com/ml-basics",
            "doc_metadata": {
                "category": "ai_basics",
                "difficulty": "beginner",
                "created_by": "test_system"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        doc_result = await documents_collection.insert_one(sample_document)
        doc_id = str(doc_result.inserted_id)
        print(f"SUCCESS: Document created with ID: {doc_id}")
        
    except Exception as e:
        print(f"ERROR: Failed to create document: {e}")
        return False
    
    # 3. Create Sample User Interaction
    print("\n3. Creating Sample User Interaction...")
    try:
        sample_interaction = {
            "session_id": "test_session_123",
            "user_query": "What is machine learning?",
            "ai_response": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.",
            "document_id": ObjectId(doc_id),
            "interaction_metadata": {
                "user_agent": "test_agent",
                "timestamp": datetime.utcnow().isoformat()
            },
            "created_at": datetime.utcnow()
        }
        
        interaction_result = await interactions_collection.insert_one(sample_interaction)
        interaction_id = str(interaction_result.inserted_id)
        print(f"SUCCESS: Interaction created with ID: {interaction_id}")
        
    except Exception as e:
        print(f"ERROR: Failed to create interaction: {e}")
        return False
    
    # 4. Create Sample Feedback
    print("\n4. Creating Sample Feedback...")
    try:
        # Positive feedback
        positive_feedback = {
            "session_id": "test_session_123",
            "interaction_id": ObjectId(interaction_id),
            "quality_label": "positive",
            "feedback_metadata": {
                "user_agent": "test_agent",
                "timestamp": datetime.utcnow().isoformat(),
                "feedback_type": "thumbs_up"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        feedback_result = await feedback_collection.insert_one(positive_feedback)
        feedback_id = str(feedback_result.inserted_id)
        print(f"SUCCESS: Positive feedback created with ID: {feedback_id}")
        
        # Negative feedback
        negative_feedback = {
            "session_id": "test_session_456",
            "interaction_id": ObjectId(interaction_id),
            "quality_label": "negative",
            "feedback_metadata": {
                "user_agent": "test_agent",
                "timestamp": datetime.utcnow().isoformat(),
                "feedback_type": "thumbs_down"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        await feedback_collection.insert_one(negative_feedback)
        print("SUCCESS: Negative feedback created")
        
    except Exception as e:
        print(f"ERROR: Failed to create feedback: {e}")
        return False
    
    # 5. Test Feedback Statistics
    print("\n5. Testing Feedback Statistics...")
    try:
        total_feedback = await feedback_collection.count_documents({"is_active": True})
        positive_count = await feedback_collection.count_documents({"quality_label": "positive", "is_active": True})
        negative_count = await feedback_collection.count_documents({"quality_label": "negative", "is_active": True})
        
        approval_rate = (positive_count / total_feedback) * 100 if total_feedback > 0 else 0
        
        print(f"SUCCESS: Feedback Statistics:")
        print(f"   Total feedback: {total_feedback}")
        print(f"   Positive: {positive_count}")
        print(f"   Negative: {negative_count}")
        print(f"   Approval rate: {approval_rate:.1f}%")
        
    except Exception as e:
        print(f"ERROR: Failed to get feedback stats: {e}")
        return False
    
    # 6. Convert Positive Feedback to Training Data
    print("\n6. Converting Positive Feedback to Training Data...")
    try:
        # Get positive feedback
        positive_feedback_cursor = feedback_collection.find({
            "quality_label": "positive",
            "is_active": True
        })
        positive_feedback_list = await positive_feedback_cursor.to_list(length=None)
        
        training_entries = []
        
        for feedback in positive_feedback_list:
            if feedback.get("interaction_id"):
                # Get the interaction
                interaction = await interactions_collection.find_one({
                    "_id": feedback["interaction_id"]
                })
                
                if interaction:
                    # Create training data entry
                    training_entry = {
                        "prompt": interaction["user_query"],
                        "response": interaction["ai_response"],
                        "context": f"Session: {interaction['session_id']} | User approved with positive feedback",
                        "category": "user_approved",
                        "difficulty_level": "medium",
                        "source_type": "user_feedback",
                        "metadata": {
                            "feedback_id": str(feedback["_id"]),
                            "interaction_id": str(interaction["_id"]),
                            "session_id": interaction["session_id"],
                            "quality_label": feedback["quality_label"],
                            "converted_at": datetime.utcnow().isoformat()
                        },
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "is_active": True
                    }
                    training_entries.append(training_entry)
        
        if training_entries:
            result = await training_collection.insert_many(training_entries)
            print(f"SUCCESS: Converted {len(training_entries)} positive feedback to training data")
            print(f"   Training data IDs: {[str(id) for id in result.inserted_ids]}")
        else:
            print("WARNING: No positive feedback found to convert")
            
    except Exception as e:
        print(f"ERROR: Failed to convert feedback to training data: {e}")
        return False
    
    # 7. Test Training Data Statistics
    print("\n7. Testing Training Data Statistics...")
    try:
        total_training = await training_collection.count_documents({"is_active": True})
        user_approved = await training_collection.count_documents({"category": "user_approved", "is_active": True})
        
        print(f"SUCCESS: Training Data Statistics:")
        print(f"   Total training entries: {total_training}")
        print(f"   User approved entries: {user_approved}")
        
    except Exception as e:
        print(f"ERROR: Failed to get training data stats: {e}")
        return False
    
    # 8. Cleanup Test Data
    print("\n8. Cleaning up test data...")
    try:
        await documents_collection.delete_many({"title": "Machine Learning Basics"})
        await interactions_collection.delete_many({"session_id": "test_session_123"})
        await feedback_collection.delete_many({"session_id": {"$in": ["test_session_123", "test_session_456"]}})
        await training_collection.delete_many({"category": "user_approved"})
        print("SUCCESS: Test data cleaned up")
        
    except Exception as e:
        print(f"WARNING: Failed to clean up test data: {e}")
    
    # Close connection
    client.close()
    
    print("\n" + "=" * 50)
    print("SUCCESS: Complete system test passed!")
    print("All components working correctly:")
    print("  • MongoDB connection")
    print("  • Document creation")
    print("  • User interaction tracking")
    print("  • Feedback system (positive/negative)")
    print("  • Training data conversion")
    print("  • Statistics and analytics")
    
    return True

def main():
    """Run the complete system test"""
    try:
        result = asyncio.run(test_complete_system())
        if result:
            print("\nSportAI system is ready for production!")
        else:
            print("\nSystem test failed - check the errors above")
    except Exception as e:
        print(f"ERROR: System test failed with exception: {e}")

if __name__ == "__main__":
    main()
