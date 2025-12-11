#!/usr/bin/env python3
"""
Example usage script for the SportAI Application Document Database System
This script demonstrates how to use the document processing and back-feed features
"""

import requests
import json
from datetime import datetime
import uuid

# API base URL
BASE_URL = "http://localhost:8000"

def create_sample_document():
    """Create a sample document"""
    url = f"{BASE_URL}/documents/"
    data = {
        "title": "Sample Document",
        "content": "This is a sample document created for testing the document database system.",
        "source_type": "user_created",
        "metadata": {
            "category": "example",
            "tags": ["sample", "test"],
            "created_by": "example_script"
        }
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        doc = response.json()
        doc_id = doc.get('id') or doc.get('_id')
        print(f"Created document: {doc['title']} (ID: {doc_id})")
        return doc_id
    else:
        print(f"Failed to create document: {response.text}")
        return None

def process_url_example():
    """Process a URL and convert HTML to JSON"""
    url = f"{BASE_URL}/documents/process-url"
    data = {
        "url": "https://example.com",
        "metadata": {
            "source": "example_script",
            "processed_at": datetime.utcnow().isoformat()
        }
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        doc = response.json()
        doc_id = doc.get('id') or doc.get('_id')
        print(f"Processed URL: {doc['title']} (ID: {doc_id})")
        return doc_id
    else:
        print(f"Failed to process URL: {response.text}")
        return None

def create_user_interaction():
    """Create a sample user interaction"""
    session_id = str(uuid.uuid4())
    
    url = f"{BASE_URL}/interactions/"
    data = {
        "session_id": session_id,
        "user_query": "What is machine learning?",
        "ai_response": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn and make decisions from data without being explicitly programmed.",
        "interaction_metadata": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "tokens_used": 45
        }
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        interaction = response.json()
        interaction_id = interaction.get('id') or interaction.get('_id')
        print(f"Created interaction: Session {session_id[:8]}... (ID: {interaction_id})")
        return session_id, interaction_id
    else:
        print(f"Failed to create interaction: {response.text}")
        return None, None

def back_feed_example():
    """Demonstrate back-feeding user interactions"""
    session_id = str(uuid.uuid4())
    
    # Create multiple sample interactions
    interactions = [
        {
            "session_id": session_id,
            "user_query": "How does neural network training work?",
            "ai_response": "Neural network training involves feeding data through the network, comparing outputs to expected results, and adjusting weights using backpropagation to minimize error.",
            "interaction_metadata": {"model": "gpt-4", "topic": "neural_networks"}
        },
        {
            "session_id": session_id,
            "user_query": "What is backpropagation?",
            "ai_response": "Backpropagation is an algorithm for training neural networks that calculates gradients by propagating errors backward through the network layers.",
            "interaction_metadata": {"model": "gpt-4", "topic": "algorithms"}
        }
    ]
    
    url = f"{BASE_URL}/interactions/back-feed"
    data = {
        "interactions": interactions,
        "create_documents": True,
        "collection_name": "neural_network_qa"
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
        print(f"Back-fed {result['processed_interactions']} interactions")
        print(f"Created {result['created_documents']} documents")
        return session_id
    else:
        print(f"Failed to back-feed: {response.text}")
        return None

def search_documents_example():
    """Search for documents"""
    url = f"{BASE_URL}/documents/search"
    data = {
        "query": "machine learning",
        "limit": 5
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        results = response.json()
        print(f"Found {results['total_count']} documents matching 'machine learning'")
        for doc in results['documents']:
            print(f"  - {doc['title']} (Type: {doc['source_type']})")
    else:
        print(f"Search failed: {response.text}")

def get_stats():
    """Get system statistics"""
    print("\nSystem Statistics:")
    
    # Document stats
    response = requests.get(f"{BASE_URL}/documents/stats/overview")
    if response.status_code == 200:
        stats = response.json()
        print(f"Documents: {stats['total_documents']} total")
        print(f"By source type: {stats['documents_by_source_type']}")
        print(f"Recent: {stats['recent_documents']} in last 7 days")
    
    # Interaction stats
    response = requests.get(f"{BASE_URL}/interactions/stats/overview")
    if response.status_code == 200:
        stats = response.json()
        print(f"Interactions: {stats['total_interactions']} total")
        print(f"Sessions: {stats['unique_sessions']} unique")
        print(f"Avg query length: {stats['average_query_length']} words")
        print(f"Avg response length: {stats['average_response_length']} words")

def main():
    """Main example function"""
    print("SportAI Document Database - Example Usage")
    print("=" * 60)
    
    # Test API health
    try:
        response = requests.get(f"{BASE_URL}/health/")
        if response.status_code == 200:
            print("API is healthy and ready")
        else:
            print("API health check failed")
            return
    except Exception as e:
        print(f"Cannot connect to API: {e}")
        print("Make sure the FastAPI server is running on http://localhost:8000")
        return
    
    print("\n1. Creating sample documents...")
    doc_id = create_sample_document()
    
    print("\n2. Processing URL (HTML to JSON)...")
    url_doc_id = process_url_example()
    
    print("\n3. Creating user interactions...")
    session_id, interaction_id = create_user_interaction()
    
    print("\n4. Back-feeding interactions...")
    back_feed_session = back_feed_example()
    
    print("\n5. Searching documents...")
    search_documents_example()
    
    print("\n6. Getting system statistics...")
    get_stats()
    
    print("\nExample completed! Check the API documentation at http://localhost:8000/docs")

if __name__ == "__main__":
    main()
