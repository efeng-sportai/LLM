from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.database import get_feedback_collection, get_interactions_collection
from app.schemas import (
    UserFeedbackCreate, UserFeedbackResponse, FeedbackStats
)

router = APIRouter()

@router.post("/", response_model=UserFeedbackResponse)
async def submit_feedback(feedback: UserFeedbackCreate):
    """Submit user feedback (thumbs up/down) for an interaction or document"""
    feedback_collection = get_feedback_collection()
    
    # Convert string IDs to ObjectId if provided
    interaction_id = None
    document_id = None
    
    if feedback.interaction_id:
        try:
            interaction_id = ObjectId(feedback.interaction_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid interaction ID")
    
    if feedback.document_id:
        try:
            document_id = ObjectId(feedback.document_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid document ID")
    
    feedback_dict = {
        "session_id": feedback.session_id,
        "interaction_id": interaction_id,
        "document_id": document_id,
        "quality_label": feedback.quality_label,
        "feedback_metadata": feedback.feedback_metadata,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }
    
    result = await feedback_collection.insert_one(feedback_dict)
    feedback_dict["_id"] = result.inserted_id
    
    return UserFeedbackResponse(**feedback_dict)

@router.get("/", response_model=List[UserFeedbackResponse])
async def get_feedback(
    session_id: Optional[str] = Query(None),
    interaction_id: Optional[str] = Query(None),
    quality_label: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get user feedback with optional filtering"""
    feedback_collection = get_feedback_collection()
    
    query = {"is_active": True}
    
    if session_id:
        query["session_id"] = session_id
    if interaction_id:
        try:
            query["interaction_id"] = ObjectId(interaction_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid interaction ID")
    if quality_label:
        query["quality_label"] = quality_label
    
    cursor = feedback_collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
    feedback_list = await cursor.to_list(length=limit)
    
    return [UserFeedbackResponse(**feedback) for feedback in feedback_list]

@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    session_id: Optional[str] = Query(None),
    date_range: Optional[str] = Query(None)
):
    """Get feedback statistics"""
    feedback_collection = get_feedback_collection()
    
    # Build query
    query = {"is_active": True}
    if session_id:
        query["session_id"] = session_id
    if date_range:
        # Parse date range (format: "2025-01-01,2025-12-31")
        start_date, end_date = date_range.split(",")
        query["created_at"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    # Get total feedback count
    total_feedback = await feedback_collection.count_documents(query)
    
    # Get positive/negative breakdown
    positive_count = await feedback_collection.count_documents({**query, "quality_label": "positive"})
    negative_count = await feedback_collection.count_documents({**query, "quality_label": "negative"})
    
    # Calculate approval rate
    if total_feedback > 0:
        approval_rate = (positive_count / total_feedback) * 100
    else:
        approval_rate = 0.0
    
    # Get recent feedback
    recent_cursor = feedback_collection.find(query).sort("created_at", -1).limit(10)
    recent_feedback = await recent_cursor.to_list(length=10)
    
    return FeedbackStats(
        total_feedback=total_feedback,
        positive_count=positive_count,
        negative_count=negative_count,
        approval_rate=approval_rate,
        recent_feedback=[UserFeedbackResponse(**feedback) for feedback in recent_feedback]
    )

@router.post("/convert-to-training")
async def convert_feedback_to_training_data(
    session_id: Optional[str] = None,
    only_positive: bool = True
):
    """Convert positive feedback interactions into training data"""
    from app.database import get_interactions_collection, get_training_data_collection
    
    feedback_collection = get_feedback_collection()
    interactions_collection = get_interactions_collection()
    training_collection = get_training_data_collection()
    
    # Build query for positive feedback
    feedback_query = {
        "is_active": True,
        "quality_label": "positive"
    }
    if session_id:
        feedback_query["session_id"] = session_id
    
    # Get positive feedback
    feedback_cursor = feedback_collection.find(feedback_query)
    feedback_list = await feedback_cursor.to_list(length=None)
    
    training_entries = []
    
    for feedback in feedback_list:
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
        return {
            "message": f"Successfully converted {len(training_entries)} positive feedback to training data",
            "training_data_count": len(training_entries),
            "inserted_ids": [str(id) for id in result.inserted_ids]
        }
    else:
        return {"message": "No positive feedback found matching the criteria"}

@router.get("/interaction/{interaction_id}", response_model=List[UserFeedbackResponse])
async def get_feedback_for_interaction(interaction_id: str):
    """Get all feedback for a specific interaction"""
    feedback_collection = get_feedback_collection()
    
    try:
        obj_id = ObjectId(interaction_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid interaction ID")
    
    cursor = feedback_collection.find({
        "interaction_id": obj_id,
        "is_active": True
    }).sort("created_at", -1)
    
    feedback_list = await cursor.to_list(length=None)
    return [UserFeedbackResponse(**feedback) for feedback in feedback_list]

@router.put("/{feedback_id}")
async def update_feedback(feedback_id: str, quality_label: Optional[str] = None, comment: Optional[str] = None):
    """Update existing feedback"""
    feedback_collection = get_feedback_collection()
    
    try:
        obj_id = ObjectId(feedback_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid feedback ID")
    
    update_data = {"updated_at": datetime.utcnow()}
    if quality_label is not None:
        update_data["quality_label"] = quality_label
    if comment is not None:
        update_data["user_comment"] = comment
    
    result = await feedback_collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return {"message": "Feedback updated successfully"}

@router.delete("/{feedback_id}")
async def delete_feedback(feedback_id: str):
    """Soft delete feedback (mark as inactive)"""
    feedback_collection = get_feedback_collection()
    
    try:
        obj_id = ObjectId(feedback_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid feedback ID")
    
    result = await feedback_collection.update_one(
        {"_id": obj_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return {"message": "Feedback deleted successfully"}
