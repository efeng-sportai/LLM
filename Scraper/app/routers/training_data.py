from fastapi import APIRouter, HTTPException, Query, Response
from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
import json
import csv
import io

from app.database import get_training_data_collection
from app.schemas import (
    TrainingDataCreate, TrainingDataResponse, TrainingDataBatchCreate,
    TrainingDataExport
)

router = APIRouter()

@router.post("/", response_model=TrainingDataResponse)
async def create_training_data(training_data: TrainingDataCreate):
    """Create a new training data entry"""
    collection = get_training_data_collection()
    
    training_dict = {
        "prompt": training_data.prompt,
        "response": training_data.response,
        "context": training_data.context,
        "category": training_data.category,
        "difficulty_level": training_data.difficulty_level,
        "source_type": training_data.source_type,
        "metadata": training_data.metadata,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }
    
    result = await collection.insert_one(training_dict)
    training_dict["_id"] = result.inserted_id
    
    return TrainingDataResponse(**training_dict)

@router.post("/batch", response_model=List[TrainingDataResponse])
async def create_training_data_batch(batch_data: TrainingDataBatchCreate):
    """Create multiple training data entries in a batch"""
    collection = get_training_data_collection()
    
    training_entries = []
    for data in batch_data.training_data:
        entry = {
            "prompt": data.prompt,
            "response": data.response,
            "context": data.context,
            "category": data.category,
            "difficulty_level": data.difficulty_level,
            "source_type": data.source_type,
            "metadata": {
                **(data.metadata or {}),
                "batch_name": batch_data.batch_name,
                "batch_metadata": batch_data.batch_metadata
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        training_entries.append(entry)
    
    result = await collection.insert_many(training_entries)
    
    # Get the inserted documents
    inserted_docs = []
    for i, doc_id in enumerate(result.inserted_ids):
        doc = training_entries[i].copy()
        doc["_id"] = doc_id
        inserted_docs.append(TrainingDataResponse(**doc))
    
    return inserted_docs

@router.get("/", response_model=List[TrainingDataResponse])
async def get_training_data(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True)
):
    """Get training data with optional filtering"""
    collection = get_training_data_collection()
    
    query = {}
    if category:
        query["category"] = category
    if source_type:
        query["source_type"] = source_type
    if difficulty_level:
        query["difficulty_level"] = difficulty_level
    if is_active is not None:
        query["is_active"] = is_active
    
    cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
    training_data = await cursor.to_list(length=limit)
    
    return [TrainingDataResponse(**data) for data in training_data]

@router.get("/{training_data_id}", response_model=TrainingDataResponse)
async def get_training_data_by_id(training_data_id: str):
    """Get a specific training data entry by ID"""
    collection = get_training_data_collection()
    
    try:
        obj_id = ObjectId(training_data_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid training data ID")
    
    training_data = await collection.find_one({"_id": obj_id})
    if not training_data:
        raise HTTPException(status_code=404, detail="Training data not found")
    
    return TrainingDataResponse(**training_data)

@router.post("/export")
async def export_training_data(export_request: TrainingDataExport):
    """Export training data in various formats"""
    collection = get_training_data_collection()
    
    # Build query
    query = {"is_active": True}
    if export_request.category_filter:
        query["category"] = export_request.category_filter
    if export_request.source_type_filter:
        query["source_type"] = export_request.source_type_filter
    if export_request.date_range:
        query["created_at"] = {
            "$gte": datetime.fromisoformat(export_request.date_range["start"]),
            "$lte": datetime.fromisoformat(export_request.date_range["end"])
        }
    
    cursor = collection.find(query).sort("created_at", -1)
    training_data = await cursor.to_list(length=None)
    
    if export_request.format == "jsonl":
        # JSONL format for training
        jsonl_content = ""
        for data in training_data:
            jsonl_content += json.dumps({
                "prompt": data["prompt"],
                "response": data["response"],
                "context": data.get("context"),
                "category": data.get("category"),
                "difficulty_level": data.get("difficulty_level"),
                "metadata": data.get("metadata", {})
            }) + "\n"
        
        return Response(
            content=jsonl_content,
            media_type="application/jsonl",
            headers={"Content-Disposition": "attachment; filename=training_data.jsonl"}
        )
    
    elif export_request.format == "csv":
        # CSV format
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["prompt", "response", "context", "category", "difficulty_level", "source_type", "created_at"])
        
        # Write data
        for data in training_data:
            writer.writerow([
                data["prompt"],
                data["response"],
                data.get("context", ""),
                data.get("category", ""),
                data.get("difficulty_level", ""),
                data["source_type"],
                data["created_at"].isoformat()
            ])
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=training_data.csv"}
        )
    
    else:  # JSON format
        return Response(
            content=json.dumps([{
                "prompt": data["prompt"],
                "response": data["response"],
                "context": data.get("context"),
                "category": data.get("category"),
                "difficulty_level": data.get("difficulty_level"),
                "source_type": data["source_type"],
                "metadata": data.get("metadata", {}),
                "created_at": data["created_at"].isoformat()
            } for data in training_data], indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=training_data.json"}
        )

# Removed: backfeed_from_interactions endpoint - interactions collection removed

@router.get("/stats/overview")
async def get_training_data_stats():
    """Get training data statistics"""
    collection = get_training_data_collection()
    
    total_entries = await collection.count_documents({"is_active": True})
    
    # Count by category
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    categories = await collection.aggregate(pipeline).to_list(length=None)
    categories_dict = {item["_id"] or "uncategorized": item["count"] for item in categories}
    
    # Count by source type
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$source_type", "count": {"$sum": 1}}}
    ]
    source_types = await collection.aggregate(pipeline).to_list(length=None)
    source_types_dict = {item["_id"]: item["count"] for item in source_types}
    
    # Count by difficulty level
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$difficulty_level", "count": {"$sum": 1}}}
    ]
    difficulty_levels = await collection.aggregate(pipeline).to_list(length=None)
    difficulty_dict = {item["_id"] or "unspecified": item["count"] for item in difficulty_levels}
    
    return {
        "total_training_entries": total_entries,
        "entries_by_category": categories_dict,
        "entries_by_source_type": source_types_dict,
        "entries_by_difficulty": difficulty_dict,
        "last_updated": datetime.utcnow().isoformat()
    }
