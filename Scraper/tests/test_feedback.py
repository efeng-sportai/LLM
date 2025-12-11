#!/usr/bin/env python3
"""
Test script to demonstrate the user feedback system with quality labels
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_positive_feedback():
    """Test submitting positive feedback"""
    print("Testing Positive Feedback Submission...")
    
    url = f"{BASE_URL}/feedback/"
    positive_feedback_data = {
        "session_id": "user_session_123",
        "interaction_id": "507f1f77bcf86cd799439011",
        "quality_label": "positive",
        "feedback_metadata": {
            "user_agent": "Mozilla/5.0...",
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    try:
        response = requests.post(url, json=positive_feedback_data)
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Positive feedback submitted: {result['quality_label']}")
            return result.get('_id') or result.get('id')
        else:
            print(f"ERROR: Failed to submit positive feedback: {response.text}")
            return None
    except Exception as e:
        print(f"ERROR: Error: {e}")
        return None

def test_negative_feedback():
    """Test submitting negative feedback"""
    print("\nTesting Negative Feedback Submission...")
    
    url = f"{BASE_URL}/feedback/"
    negative_feedback_data = {
        "session_id": "user_session_123",
        "interaction_id": "507f1f77bcf86cd799439012",
        "quality_label": "negative",
        "feedback_metadata": {
            "user_agent": "Mozilla/5.0...",
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    try:
        response = requests.post(url, json=negative_feedback_data)
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Negative feedback submitted: {result['quality_label']}")
            return result.get('_id') or result.get('id')
        else:
            print(f"ERROR: Failed to submit negative feedback: {response.text}")
            return None
    except Exception as e:
        print(f"ERROR: Error: {e}")
        return None

def test_feedback_stats():
    """Test getting feedback statistics"""
    print("\nTesting Feedback Statistics...")
    
    url = f"{BASE_URL}/feedback/stats"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            stats = response.json()
            print(f"SUCCESS: Feedback Stats:")
            print(f"   Total feedback: {stats.get('total_feedback', 0)}")
            print(f"   Positive: {stats.get('positive_count', 0)}")
            print(f"   Negative: {stats.get('negative_count', 0)}")
            print(f"   Approval rate: {stats.get('approval_rate', 0):.1f}%")
            return stats
        else:
            print(f"ERROR: Failed to get feedback stats: {response.text}")
            return None
    except Exception as e:
        print(f"ERROR: Error: {e}")
        return None

def test_convert_positive_to_training():
    """Test converting positive feedback to training data"""
    print("\nTesting Positive Feedback to Training Data Conversion...")
    
    url = f"{BASE_URL}/feedback/convert-to-training"
    data = {
        "session_id": "user_session_123",
        "only_positive": True
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Converted positive feedback to training data: {result.get('training_data_count', 0)} entries")
            return result
        else:
            print(f"ERROR: Failed to convert feedback: {response.text}")
            return None
    except Exception as e:
        print(f"ERROR: Error: {e}")
        return None

def demonstrate_frontend_integration():
    """Show how the frontend would integrate with thumbs up/down"""
    print("\nFrontend Thumbs Up/Down Integration:")
    print("=" * 50)
    
    print("""
    // Angular/React Frontend Integration Example:
    
    // 1. User clicks thumbs up button
    async thumbsUp(interactionId: string, sessionId: string) {
        const feedbackData = {
            session_id: sessionId,
            interaction_id: interactionId,
            quality_label: "positive",
            feedback_metadata: {
                user_agent: navigator.userAgent,
                timestamp: new Date().toISOString()
            }
        };
        
        try {
            const response = await fetch('/feedback/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(feedbackData)
            });
            
            if (response.ok) {
                console.log('Thumbs up submitted');
                // Update UI to show thumbs up state
                this.updateThumbsUI(interactionId, 'up');
            }
        } catch (error) {
            console.error('Failed to submit thumbs up:', error);
        }
    }
    
    // 2. User clicks thumbs down button
    async thumbsDown(interactionId: string, sessionId: string) {
        const feedbackData = {
            session_id: sessionId,
            interaction_id: interactionId,
            quality_label: "negative",
            feedback_metadata: {
                user_agent: navigator.userAgent,
                timestamp: new Date().toISOString()
            }
        };
        
        try {
            const response = await fetch('/feedback/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(feedbackData)
            });
            
            if (response.ok) {
                console.log('Thumbs down submitted');
                // Update UI to show thumbs down state
                this.updateThumbsUI(interactionId, 'down');
            }
        } catch (error) {
            console.error('Failed to submit thumbs down:', error);
        }
    }
    
    // 3. Update UI to show thumbs state
    updateThumbsUI(interactionId: string, state: 'up' | 'down' | 'none') {
        const thumbsUpBtn = document.querySelector(`[data-interaction="${interactionId}"] .thumbs-up`);
        const thumbsDownBtn = document.querySelector(`[data-interaction="${interactionId}"] .thumbs-down`);
        
        // Reset all states
        thumbsUpBtn?.classList.remove('active');
        thumbsDownBtn?.classList.remove('active');
        
        // Set active state
        if (state === 'up') {
            thumbsUpBtn?.classList.add('active');
        } else if (state === 'down') {
            thumbsDownBtn?.classList.add('active');
        }
    }
    
    // 4. Get feedback statistics for dashboard
    async getFeedbackStats() {
        try {
            const response = await fetch('/feedback/stats');
            const stats = await response.json();
            
            // Update dashboard with stats
            document.getElementById('positive-count').textContent = stats.positive_count;
            document.getElementById('negative-count').textContent = stats.negative_count;
            document.getElementById('approval-rate').textContent = `${stats.approval_rate.toFixed(1)}%`;
            
            return stats;
        } catch (error) {
            console.error('Failed to get feedback stats:', error);
        }
    }
    """)

def main():
    """Main test function"""
    print("SportAI User Feedback System Test")
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
    test_positive_feedback()
    test_negative_feedback()
    test_feedback_stats()
    test_convert_positive_to_training()
    demonstrate_frontend_integration()
    
    print("\nUser Feedback System Test Complete!")
    print("Key Features Demonstrated:")
    print("   • Positive/negative feedback submission")
    print("   • Quality label system (positive/negative)")
    print("   • Approval rate statistics")
    print("   • Automatic training data conversion")
    print("   • Frontend integration examples")
    print("\nCheck the API documentation at http://localhost:8000/docs")

if __name__ == "__main__":
    main()
