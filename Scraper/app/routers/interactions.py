from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.database import get_interactions_collection, get_documents_collection
from app.schemas import (
    UserInteractionCreate, UserInteractionResponse,
    BackFeedRequest, BackFeedResponse
)
from app.services.document_processor import DocumentProcessor

router = APIRouter()
document_processor = DocumentProcessor()

@router.post("/", response_model=UserInteractionResponse)
async def create_interaction(interaction: UserInteractionCreate):
    """Create a new user interaction record"""
    collection = get_interactions_collection()
    
    interaction_dict = {
        "session_id": interaction.session_id,
        "user_query": interaction.user_query,
        "ai_response": interaction.ai_response,
        "document_id": ObjectId(interaction.document_id) if interaction.document_id else None,
        "interaction_metadata": interaction.interaction_metadata,
        "created_at": datetime.utcnow()
    }
    
    result = await collection.insert_one(interaction_dict)
    interaction_dict["_id"] = result.inserted_id
    
    return UserInteractionResponse(**interaction_dict)

@router.get("/", response_model=List[UserInteractionResponse])
async def get_interactions(
    session_id: Optional[str] = Query(None),
    document_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get user interactions with optional filtering"""
    collection = get_interactions_collection()
    
    query = {}
    if session_id:
        query["session_id"] = session_id
    if document_id:
        try:
            query["document_id"] = ObjectId(document_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid document ID")
    
    cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    interactions = await cursor.to_list(length=limit)
    
    return [UserInteractionResponse(**interaction) for interaction in interactions]

@router.get("/{interaction_id}", response_model=UserInteractionResponse)
async def get_interaction(interaction_id: str):
    """Get a specific interaction by ID"""
    collection = get_interactions_collection()
    
    try:
        obj_id = ObjectId(interaction_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid interaction ID")
    
    interaction = await collection.find_one({"_id": obj_id})
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    
    return UserInteractionResponse(**interaction)

@router.post("/back-feed", response_model=BackFeedResponse)
async def back_feed_interactions(back_feed_request: BackFeedRequest):
    """Back-feed user interactions and optionally create documents"""
    interactions_collection = get_interactions_collection()
    documents_collection = get_documents_collection()
    
    processed_interactions = 0
    created_documents = 0
    
    for interaction_data in back_feed_request.interactions:
        # Create the interaction record
        interaction_dict = {
            "session_id": interaction_data.session_id,
            "user_query": interaction_data.user_query,
            "ai_response": interaction_data.ai_response,
            "document_id": ObjectId(interaction_data.document_id) if interaction_data.document_id else None,
            "interaction_metadata": interaction_data.interaction_metadata,
            "created_at": datetime.utcnow()
        }
        
        result = await interactions_collection.insert_one(interaction_dict)
        interaction_dict["_id"] = result.inserted_id
        processed_interactions += 1
        
        # Optionally create documents from interactions
        if back_feed_request.create_documents:
            # Create document from the AI response
            doc_data = document_processor.create_document_from_text(
                title=f"Response to: {interaction_data.user_query[:50]}...",
                content=interaction_data.ai_response,
                metadata={
                    "source": "user_interaction_backfeed",
                    "session_id": interaction_data.session_id,
                    "original_query": interaction_data.user_query,
                    "interaction_metadata": interaction_data.interaction_metadata
                }
            )
            
            document_dict = {
                "title": doc_data["title"],
                "content": doc_data["content"],
                "source_type": "api_response",
                "doc_metadata": doc_data["doc_metadata"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True
            }
            
            doc_result = await documents_collection.insert_one(document_dict)
            document_dict["_id"] = doc_result.inserted_id
            created_documents += 1
            
            # Update the interaction with the document ID
            await interactions_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"document_id": doc_result.inserted_id}}
            )
    
    return BackFeedResponse(
        processed_interactions=processed_interactions,
        created_documents=created_documents,
        message=f"Successfully processed {processed_interactions} interactions and created {created_documents} documents"
    )

@router.get("/sessions/{session_id}/summary")
async def get_session_summary(session_id: str):
    """Get a summary of interactions for a specific session"""
    collection = get_interactions_collection()
    
    interactions = await collection.find({"session_id": session_id}).sort("created_at", 1).to_list(length=None)
    
    if not interactions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    total_interactions = len(interactions)
    total_queries_length = sum(len(i["user_query"].split()) for i in interactions)
    total_responses_length = sum(len(i["ai_response"].split()) for i in interactions)
    
    # Get unique document IDs referenced
    document_ids = list(set(str(i["document_id"]) for i in interactions if i.get("document_id")))
    
    # Get time span
    first_interaction = interactions[0]["created_at"]
    last_interaction = interactions[-1]["created_at"]
    duration_minutes = (last_interaction - first_interaction).total_seconds() / 60
    
    return {
        "session_id": session_id,
        "total_interactions": total_interactions,
        "duration_minutes": round(duration_minutes, 2),
        "first_interaction": first_interaction.isoformat(),
        "last_interaction": last_interaction.isoformat(),
        "total_queries_words": total_queries_length,
        "total_responses_words": total_responses_length,
        "referenced_documents": len(document_ids),
        "document_ids": document_ids
    }

@router.get("/stats/overview")
async def get_interaction_stats():
    """Get interaction statistics"""
    collection = get_interactions_collection()
    
    total_interactions = await collection.count_documents({})
    
    # Count by session
    pipeline = [{"$group": {"_id": "$session_id"}}, {"$count": "unique_sessions"}]
    unique_sessions_result = await collection.aggregate(pipeline).to_list(length=1)
    unique_sessions = unique_sessions_result[0]["unique_sessions"] if unique_sessions_result else 0
    
    # Recent interactions (last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_interactions = await collection.count_documents({"created_at": {"$gte": week_ago}})
    
    # Average interaction length
    pipeline = [
        {"$group": {
            "_id": None,
            "avg_query_length": {"$avg": {"$strLenCP": "$user_query"}},
            "avg_response_length": {"$avg": {"$strLenCP": "$ai_response"}}
        }}
    ]
    avg_result = await collection.aggregate(pipeline).to_list(length=1)
    
    if avg_result:
        avg_query_length = avg_result[0].get("avg_query_length", 0) / 5  # Rough word count
        avg_response_length = avg_result[0].get("avg_response_length", 0) / 5
    else:
        avg_query_length = 0
        avg_response_length = 0
    
    return {
        "total_interactions": total_interactions,
        "unique_sessions": unique_sessions,
        "recent_interactions": recent_interactions,
        "average_query_length": round(avg_query_length, 2),
        "average_response_length": round(avg_response_length, 2),
        "last_updated": datetime.utcnow().isoformat()
    }