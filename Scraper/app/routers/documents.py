from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import uuid
from datetime import datetime
from bson import ObjectId

from app.database import get_documents_collection
from app.schemas import (
    DocumentCreate, DocumentResponse, DocumentUpdate,
    URLProcessRequest, BulkURLProcessRequest,
    DocumentSearchRequest, DocumentSearchResponse
)
from app.services.document_processor import DocumentProcessor

router = APIRouter()
document_processor = DocumentProcessor()

@router.post("/", response_model=DocumentResponse)
async def create_document(document: DocumentCreate):
    """Create a new document"""
    collection = get_documents_collection()
    
    document_dict = {
        "title": document.title,
        "content": document.content,
        "source_type": document.source_type,
        "source_url": document.source_url,
        "doc_metadata": document.doc_metadata,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }
    
    result = await collection.insert_one(document_dict)
    document_dict["_id"] = result.inserted_id
    
    return DocumentResponse(**document_dict)

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True)
):
    """Get all documents with optional filtering"""
    collection = get_documents_collection()
    
    query = {}
    if source_type:
        query["source_type"] = source_type
    if is_active is not None:
        query["is_active"] = is_active
    
    cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
    documents = await cursor.to_list(length=limit)
    
    return [DocumentResponse(**doc) for doc in documents]

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get a specific document by ID"""
    collection = get_documents_collection()
    
    try:
        obj_id = ObjectId(document_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    document = await collection.find_one({"_id": obj_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(**document)

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: str, document_update: DocumentUpdate):
    """Update a document"""
    collection = get_documents_collection()
    
    try:
        obj_id = ObjectId(document_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    update_data = document_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    result = await collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Return updated document
    updated_document = await collection.find_one({"_id": obj_id})
    return DocumentResponse(**updated_document)

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document (soft delete)"""
    collection = get_documents_collection()
    
    try:
        obj_id = ObjectId(document_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    result = await collection.update_one(
        {"_id": obj_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}

@router.post("/process-url", response_model=DocumentResponse)
async def process_url(url_request: URLProcessRequest):
    """Process a URL and create a document from its content"""
    try:
        # Process the URL
        processed_data = document_processor.process_url(str(url_request.url))
        
        collection = get_documents_collection()
        
        # Create document
        document_dict = {
            "title": processed_data["title"],
            "content": processed_data["content"],
            "source_type": processed_data.get("source_type", "html"),
            "source_url": str(url_request.url),
            "doc_metadata": processed_data.get("metadata", {}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = await collection.insert_one(document_dict)
        document_dict["_id"] = result.inserted_id
        
        return DocumentResponse(**document_dict)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process URL: {str(e)}")

@router.post("/process-urls-bulk", response_model=List[DocumentResponse])
async def process_urls_bulk(bulk_request: BulkURLProcessRequest):
    """Process multiple URLs and create documents"""
    created_documents = []
    errors = []
    
    collection = get_documents_collection()
    
    for url in bulk_request.urls:
        try:
            processed_data = document_processor.process_url(str(url))
            
            document_dict = {
                "title": processed_data["title"],
                "content": processed_data["content"],
                "source_type": processed_data.get("source_type", "html"),
                "source_url": str(url),
                "doc_metadata": processed_data.get("metadata", {}),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True
            }
            
            result = await collection.insert_one(document_dict)
            document_dict["_id"] = result.inserted_id
            created_documents.append(DocumentResponse(**document_dict))
            
        except Exception as e:
            errors.append(f"Failed to process {url}: {str(e)}")
    
    if errors:
        raise HTTPException(status_code=207, detail={
            "message": "Some URLs failed to process",
            "errors": errors,
            "created_documents": len(created_documents)
        })
    
    return created_documents

@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(search_request: DocumentSearchRequest):
    """Search documents by content using MongoDB text search"""
    collection = get_documents_collection()
    
    # Build query
    query = {"is_active": True}
    
    # Add source type filtering
    if search_request.source_types:
        query["source_type"] = {"$in": search_request.source_types}
    
    # Use MongoDB text search
    text_query = {"$text": {"$search": search_request.query}}
    query.update(text_query)
    
    # Get total count
    total_count = await collection.count_documents(query)
    
    # Get documents with pagination
    cursor = collection.find(query).skip(search_request.offset).limit(search_request.limit)
    documents = await cursor.to_list(length=search_request.limit)
    
    return DocumentSearchResponse(
        documents=[DocumentResponse(**doc) for doc in documents],
        total_count=total_count,
        query=search_request.query
    )

@router.get("/stats/overview")
async def get_document_stats():
    """Get document statistics"""
    collection = get_documents_collection()
    
    total_docs = await collection.count_documents({"is_active": True})
    
    # Count by source type
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$source_type", "count": {"$sum": 1}}}
    ]
    source_types = await collection.aggregate(pipeline).to_list(length=None)
    source_types_dict = {item["_id"]: item["count"] for item in source_types}
    
    # Recent documents (last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_docs = await collection.count_documents({
        "created_at": {"$gte": week_ago},
        "is_active": True
    })
    
    return {
        "total_documents": total_docs,
        "documents_by_source_type": source_types_dict,
        "recent_documents": recent_docs,
        "last_updated": datetime.utcnow().isoformat()
    }