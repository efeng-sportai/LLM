#!/usr/bin/env python3
"""
Test script to demonstrate the training data backfeeding functionality
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_training_data_creation():
    """Test creating training data entries"""
    print("Testing Training Data Creation...")
    
    # Test single training data entry
    url = f"{BASE_URL}/training-data/"
    data = {
        "prompt": "What is machine learning?",
        "response": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.",
        "category": "ai_basics",
        "difficulty_level": "beginner",
        "source_type": "manual",
        "context": "Educational content for AI training"
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Created training data: {result['prompt'][:50]}...")
            return result.get('_id') or result.get('id')
        else:
            print(f"ERROR: Failed to create training data: {response.text}")
            return None
    except Exception as e:
        print(f"ERROR: Error: {e}")
        return None

def test_batch_training_data():
    """Test creating multiple training data entries"""
    print("\nTesting Batch Training Data Creation...")
    
    url = f"{BASE_URL}/training-data/batch"
    data = {
        "training_data": [
            {
                "prompt": "How does neural network training work?",
                "response": "Neural network training involves feeding data through the network, comparing outputs to expected results, and adjusting weights using backpropagation.",
                "category": "neural_networks",
                "difficulty_level": "intermediate",
                "source_type": "manual"
            },
            {
                "prompt": "What is backpropagation?",
                "response": "Backpropagation is an algorithm for training neural networks that calculates gradients by propagating errors backward through the network layers.",
                "category": "neural_networks",
                "difficulty_level": "intermediate",
                "source_type": "manual"
            }
        ],
        "batch_name": "neural_network_basics",
        "batch_metadata": {
            "topic": "neural_networks",
            "created_by": "test_script"
        }
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            results = response.json()
            print(f"SUCCESS: Created batch training data: {len(results)} entries")
            return [result.get('_id') or result.get('id') for result in results]
        else:
            print(f"ERROR: Failed to create batch training data: {response.text}")
            return []
    except Exception as e:
        print(f"ERROR: Error: {e}")
        return []

def test_backfeed_from_interactions():
    """Test backfeeding from existing user interactions"""
    print("\nTesting Backfeed from Interactions...")
    
    url = f"{BASE_URL}/training-data/backfeed-from-interactions"
    data = {
        "category": "user_interactions",
        "date_range": {
            "start": "2025-01-01T00:00:00",
            "end": "2025-12-31T23:59:59"
        }
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Backfed interactions: {result.get('training_data_count', 0)} entries")
            return result
        else:
            print(f"ERROR: Failed to backfeed: {response.text}")
            return None
    except Exception as e:
        print(f"ERROR: Error: {e}")
        return None

def test_training_data_stats():
    """Test getting training data statistics"""
    print("\nTesting Training Data Statistics...")
    
    url = f"{BASE_URL}/training-data/stats/overview"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            stats = response.json()
            print(f"SUCCESS: Training Data Stats:")
            print(f"   Total entries: {stats.get('total_training_entries', 0)}")
            print(f"   Categories: {stats.get('entries_by_category', {})}")
            print(f"   Source types: {stats.get('entries_by_source_type', {})}")
            print(f"   Difficulty levels: {stats.get('entries_by_difficulty', {})}")
            return stats
        else:
            print(f"ERROR: Failed to get stats: {response.text}")
            return None
    except Exception as e:
        print(f"ERROR: Error: {e}")
        return None

def test_export_training_data():
    """Test exporting training data"""
    print("\nTesting Training Data Export...")
    
    url = f"{BASE_URL}/training-data/export"
    data = {
        "format": "jsonl",
        "category_filter": "ai_basics"
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"SUCCESS: Exported training data: {len(response.text)} characters")
            print(f"   Sample: {response.text[:200]}...")
            return True
        else:
            print(f"ERROR: Failed to export: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Error: {e}")
        return False

def main():
    """Main test function"""
    print("SportAI Training Data Backfeeding System Test")
    print("=" * 60)
    
    # Test API health
    try:
        response = requests.get(f"{BASE_URL}/health/")
        if response.status_code == 200:
            print("SUCCESS: API is healthy and ready")
        else:
            print("ERROR: API health check failed")
            return
    except Exception as e:
        print(f"ERROR: Cannot connect to API: {e}")
        print("Make sure the FastAPI server is running on http://localhost:8000")
        return
    
    # Run tests
    test_training_data_creation()
    test_batch_training_data()
    test_backfeed_from_interactions()
    test_training_data_stats()
    test_export_training_data()
    
    print("\nTraining Data Backfeeding System Test Complete!")
    print("Check the API documentation at http://localhost:8000/docs")

if __name__ == "__main__":
    main()
