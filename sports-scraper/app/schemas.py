from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ])

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return ObjectId(v)
            raise ValueError("Invalid ObjectId")
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler):
        return {"type": "string"}

# Document schemas
class DocumentCreate(BaseModel):
    title: str
    content: str
    source_type: str  # 'html', 'json', 'user_created', 'api_response'
    source_url: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    content: str
    source_type: str
    source_url: Optional[str]
    doc_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

# URL processing schemas
class URLProcessRequest(BaseModel):
    url: HttpUrl
    collection_name: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None

class BulkURLProcessRequest(BaseModel):
    urls: List[HttpUrl]
    collection_name: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None

# User interaction schemas
class UserInteractionCreate(BaseModel):
    session_id: str
    user_query: str
    ai_response: str
    document_id: Optional[str] = None
    interaction_metadata: Optional[Dict[str, Any]] = None

class UserInteractionResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    session_id: str
    user_query: str
    ai_response: str
    document_id: Optional[PyObjectId]
    interaction_metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Search schemas
class DocumentSearchRequest(BaseModel):
    query: str
    source_types: Optional[List[str]] = None
    limit: int = 10
    offset: int = 0

class DocumentSearchResponse(BaseModel):
    documents: List[DocumentResponse]
    total_count: int
    query: str

# Collection schemas
class DocumentCollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: str
    collection_metadata: Optional[Dict[str, Any]] = None

class DocumentCollectionResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str]
    source_type: str
    collection_meta: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Back-feed schemas
class BackFeedRequest(BaseModel):
    interactions: List[UserInteractionCreate]
    create_documents: bool = True
    collection_name: Optional[str] = None

class BackFeedResponse(BaseModel):
    processed_interactions: int
    created_documents: int
    collection_id: Optional[int] = None
    message: str

# Training Data schemas
class TrainingDataCreate(BaseModel):
    prompt: str
    response: str
    context: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[str] = None
    source_type: str = "user_interaction"  # 'user_interaction', 'manual', 'synthetic'
    metadata: Optional[Dict[str, Any]] = None

class TrainingDataResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    prompt: str
    response: str
    context: Optional[str]
    category: Optional[str]
    difficulty_level: Optional[str]
    source_type: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class TrainingDataBatchCreate(BaseModel):
    training_data: List[TrainingDataCreate]
    batch_name: Optional[str] = None
    batch_metadata: Optional[Dict[str, Any]] = None

class TrainingDataExport(BaseModel):
    format: str = "jsonl"  # 'jsonl', 'csv', 'json'
    category_filter: Optional[str] = None
    source_type_filter: Optional[str] = None
    date_range: Optional[Dict[str, str]] = None

# User Feedback schemas
class UserFeedbackCreate(BaseModel):
    session_id: str
    interaction_id: Optional[str] = None
    document_id: Optional[str] = None
    quality_label: str = Field(..., pattern="^(positive|negative)$")  # ML-friendly labels
    feedback_metadata: Optional[Dict[str, Any]] = None

class UserFeedbackResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    session_id: str
    interaction_id: Optional[PyObjectId]
    document_id: Optional[PyObjectId]
    quality_label: str
    feedback_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class FeedbackStats(BaseModel):
    total_feedback: int
    positive_count: int
    negative_count: int
    approval_rate: float  # Percentage of positive feedback
    recent_feedback: List[UserFeedbackResponse]

class TrainingDataWithFeedback(BaseModel):
    prompt: str
    response: str
    context: Optional[str]
    category: Optional[str]
    difficulty_level: Optional[str]
    source_type: str
    feedback_score: float  # Calculated from user ratings
    feedback_count: int
    metadata: Optional[Dict[str, Any]]
