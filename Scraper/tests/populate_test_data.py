#!/usr/bin/env python3
"""
Populate SportAI database with realistic test data
This will create sample documents, interactions, feedback, and training data
"""

import asyncio
import json
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import random

# Import our modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings
from app.database import get_mongodb_url

async def populate_test_data():
    """Populate the database with realistic test data"""
    print("Populating SportAI Database with Test Data")
    print("=" * 50)
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(get_mongodb_url())
        database = client[settings.database_name]
        
        # Test connection
        await client.admin.command('ping')
        print("SUCCESS: Connected to MongoDB Atlas")
        
        # Get collections
        documents_collection = database.documents
        interactions_collection = database.user_interactions
        feedback_collection = database.user_feedback
        training_collection = database.training_data
        
        print("SUCCESS: All collections accessible")
        
    except Exception as e:
        print(f"ERROR: MongoDB connection failed: {e}")
        return False
    
    # 1. Create Sample Documents
    print("\n1. Creating Sample Documents...")
    try:
        sample_documents = [
            {
                "title": "Introduction to Machine Learning",
                "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data without being explicitly programmed. It enables computers to learn and improve from experience automatically.",
                "source_type": "educational",
                "source_url": "https://example.com/ml-intro",
                "doc_metadata": {
                    "category": "ai_basics",
                    "difficulty": "beginner",
                    "tags": ["machine learning", "AI", "algorithms"],
                    "word_count": 45
                },
                "created_at": datetime.utcnow() - timedelta(days=5),
                "updated_at": datetime.utcnow() - timedelta(days=5),
                "is_active": True
            },
            {
                "title": "Neural Networks Explained",
                "content": "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) that process information using a connectionist approach to computation.",
                "source_type": "technical",
                "source_url": "https://example.com/neural-networks",
                "doc_metadata": {
                    "category": "deep_learning",
                    "difficulty": "intermediate",
                    "tags": ["neural networks", "deep learning", "AI"],
                    "word_count": 38
                },
                "created_at": datetime.utcnow() - timedelta(days=3),
                "updated_at": datetime.utcnow() - timedelta(days=3),
                "is_active": True
            },
            {
                "title": "Python for Data Science",
                "content": "Python is a powerful programming language for data science. It offers libraries like NumPy, Pandas, and Scikit-learn that make data analysis and machine learning accessible to developers.",
                "source_type": "tutorial",
                "source_url": "https://example.com/python-data-science",
                "doc_metadata": {
                    "category": "programming",
                    "difficulty": "beginner",
                    "tags": ["python", "data science", "programming"],
                    "word_count": 42
                },
                "created_at": datetime.utcnow() - timedelta(days=1),
                "updated_at": datetime.utcnow() - timedelta(days=1),
                "is_active": True
            }
        ]
        
        doc_results = await documents_collection.insert_many(sample_documents)
        doc_ids = [str(id) for id in doc_results.inserted_ids]
        print(f"SUCCESS: Created {len(doc_ids)} documents")
        print(f"   Document IDs: {doc_ids}")
        
    except Exception as e:
        print(f"ERROR: Failed to create documents: {e}")
        return False
    
    # 2. Create Sample User Interactions
    print("\n2. Creating Sample User Interactions...")
    try:
        sample_interactions = [
            {
                "session_id": "user_session_001",
                "user_query": "What is machine learning?",
                "ai_response": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data without being explicitly programmed. It enables computers to learn and improve from experience automatically.",
                "document_id": ObjectId(doc_ids[0]),
                "interaction_metadata": {
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "query_type": "definition"
                },
                "created_at": datetime.utcnow() - timedelta(hours=2)
            },
            {
                "session_id": "user_session_001",
                "user_query": "How do neural networks work?",
                "ai_response": "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) that process information using a connectionist approach to computation.",
                "document_id": ObjectId(doc_ids[1]),
                "interaction_metadata": {
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "query_type": "explanation"
                },
                "created_at": datetime.utcnow() - timedelta(hours=1)
            },
            {
                "session_id": "user_session_002",
                "user_query": "What programming language should I learn for data science?",
                "ai_response": "Python is a powerful programming language for data science. It offers libraries like NumPy, Pandas, and Scikit-learn that make data analysis and machine learning accessible to developers.",
                "document_id": ObjectId(doc_ids[2]),
                "interaction_metadata": {
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "query_type": "recommendation"
                },
                "created_at": datetime.utcnow() - timedelta(minutes=30)
            },
            {
                "session_id": "user_session_003",
                "user_query": "Explain deep learning",
                "ai_response": "Deep learning is a subset of machine learning that uses neural networks with multiple layers (deep neural networks) to model and understand complex patterns in data. It's particularly effective for tasks like image recognition and natural language processing.",
                "document_id": ObjectId(doc_ids[1]),
                "interaction_metadata": {
                    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "query_type": "explanation"
                },
                "created_at": datetime.utcnow() - timedelta(minutes=15)
            },
            {
                "session_id": "user_session_004",
                "user_query": "What are the benefits of machine learning?",
                "ai_response": "Machine learning offers numerous benefits including automated decision-making, pattern recognition in large datasets, predictive analytics, personalization, and the ability to improve performance over time without explicit programming.",
                "document_id": ObjectId(doc_ids[0]),
                "interaction_metadata": {
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "query_type": "benefits"
                },
                "created_at": datetime.utcnow() - timedelta(minutes=5)
            }
        ]
        
        interaction_results = await interactions_collection.insert_many(sample_interactions)
        interaction_ids = [str(id) for id in interaction_results.inserted_ids]
        print(f"SUCCESS: Created {len(interaction_ids)} interactions")
        print(f"   Interaction IDs: {interaction_ids}")
        
    except Exception as e:
        print(f"ERROR: Failed to create interactions: {e}")
        return False
    
    # 3. Create Sample Feedback
    print("\n3. Creating Sample Feedback...")
    try:
        # Create feedback for the interactions
        sample_feedback = [
            {
                "session_id": "user_session_001",
                "interaction_id": ObjectId(interaction_ids[0]),
                "quality_label": "positive",
                "feedback_metadata": {
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "feedback_type": "thumbs_up",
                    "user_satisfaction": "high"
                },
                "created_at": datetime.utcnow() - timedelta(hours=1, minutes=45),
                "updated_at": datetime.utcnow() - timedelta(hours=1, minutes=45),
                "is_active": True
            },
            {
                "session_id": "user_session_001",
                "interaction_id": ObjectId(interaction_ids[1]),
                "quality_label": "positive",
                "feedback_metadata": {
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "feedback_type": "thumbs_up",
                    "user_satisfaction": "high"
                },
                "created_at": datetime.utcnow() - timedelta(hours=1, minutes=30),
                "updated_at": datetime.utcnow() - timedelta(hours=1, minutes=30),
                "is_active": True
            },
            {
                "session_id": "user_session_002",
                "interaction_id": ObjectId(interaction_ids[2]),
                "quality_label": "positive",
                "feedback_metadata": {
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "feedback_type": "thumbs_up",
                    "user_satisfaction": "high"
                },
                "created_at": datetime.utcnow() - timedelta(minutes=25),
                "updated_at": datetime.utcnow() - timedelta(minutes=25),
                "is_active": True
            },
            {
                "session_id": "user_session_003",
                "interaction_id": ObjectId(interaction_ids[3]),
                "quality_label": "negative",
                "feedback_metadata": {
                    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "feedback_type": "thumbs_down",
                    "user_satisfaction": "low",
                    "reason": "response_too_technical"
                },
                "created_at": datetime.utcnow() - timedelta(minutes=10),
                "updated_at": datetime.utcnow() - timedelta(minutes=10),
                "is_active": True
            },
            {
                "session_id": "user_session_004",
                "interaction_id": ObjectId(interaction_ids[4]),
                "quality_label": "positive",
                "feedback_metadata": {
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "feedback_type": "thumbs_up",
                    "user_satisfaction": "high"
                },
                "created_at": datetime.utcnow() - timedelta(minutes=2),
                "updated_at": datetime.utcnow() - timedelta(minutes=2),
                "is_active": True
            }
        ]
        
        feedback_results = await feedback_collection.insert_many(sample_feedback)
        feedback_ids = [str(id) for id in feedback_results.inserted_ids]
        print(f"SUCCESS: Created {len(feedback_ids)} feedback entries")
        print(f"   Feedback IDs: {feedback_ids}")
        
    except Exception as e:
        print(f"ERROR: Failed to create feedback: {e}")
        return False
    
    # 4. Convert Positive Feedback to Training Data
    print("\n4. Converting Positive Feedback to Training Data...")
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
                            "user_satisfaction": feedback["feedback_metadata"].get("user_satisfaction", "unknown"),
                            "converted_at": datetime.utcnow().isoformat()
                        },
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "is_active": True
                    }
                    training_entries.append(training_entry)
        
        if training_entries:
            result = await training_collection.insert_many(training_entries)
            training_ids = [str(id) for id in result.inserted_ids]
            print(f"SUCCESS: Converted {len(training_entries)} positive feedback to training data")
            print(f"   Training data IDs: {training_ids}")
        else:
            print("WARNING: No positive feedback found to convert")
            
    except Exception as e:
        print(f"ERROR: Failed to convert feedback to training data: {e}")
        return False
    
    # 5. Display Final Statistics
    print("\n5. Final Database Statistics...")
    try:
        # Document stats
        total_docs = await documents_collection.count_documents({"is_active": True})
        print(f"   Documents: {total_docs}")
        
        # Interaction stats
        total_interactions = await interactions_collection.count_documents({})
        print(f"   Interactions: {total_interactions}")
        
        # Feedback stats
        total_feedback = await feedback_collection.count_documents({"is_active": True})
        positive_count = await feedback_collection.count_documents({"quality_label": "positive", "is_active": True})
        negative_count = await feedback_collection.count_documents({"quality_label": "negative", "is_active": True})
        approval_rate = (positive_count / total_feedback) * 100 if total_feedback > 0 else 0
        
        print(f"   Feedback: {total_feedback} total")
        print(f"   Positive: {positive_count}")
        print(f"   Negative: {negative_count}")
        print(f"   Approval Rate: {approval_rate:.1f}%")
        
        # Training data stats
        total_training = await training_collection.count_documents({"is_active": True})
        user_approved = await training_collection.count_documents({"category": "user_approved", "is_active": True})
        print(f"   Training Data: {total_training}")
        print(f"   User Approved: {user_approved}")
        
    except Exception as e:
        print(f"ERROR: Failed to get final statistics: {e}")
        return False
    
    # Close connection
    client.close()
    
    print("\n" + "=" * 50)
    print("SUCCESS: Database populated with test data!")
    print("\nYou can now view the data in MongoDB Atlas:")
    print("  • Documents: Sample educational content")
    print("  • Interactions: User queries and AI responses")
    print("  • Feedback: Positive/negative user ratings")
    print("  • Training Data: High-quality interactions for ML training")
    print(f"\nDatabase: {settings.database_name}")
    print("Collections: documents, user_interactions, user_feedback, training_data")
    
    return True

def main():
    """Run the data population script"""
    try:
        result = asyncio.run(populate_test_data())
        if result:
            print("\nDatabase is ready with realistic test data!")
        else:
            print("\nData population failed - check the errors above")
    except Exception as e:
        print(f"ERROR: Data population failed with exception: {e}")

if __name__ == "__main__":
    main()
