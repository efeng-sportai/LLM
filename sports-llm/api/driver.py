from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from utils.mongo_vector_collection import MongoVectorClient, MongoVectorCollection
from pydantic import BaseModel
import os
import logging
from pathlib import Path

# Configure logging for debug mode
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load .env file from project root
try:
    from dotenv import load_dotenv
    # Look for .env in the project root (two levels up from this file)
    root_dir = Path(__file__).parent.parent.parent
    env_file = root_dir / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded .env file from: {env_file}")
    else:
        print(f"Warning: .env file not found at {env_file}")
except ImportError:
    print("Note: python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"Note: Could not load .env file: {e}")

# Get MongoDB connection string
def get_mongodb_connection_string():
    """Get MongoDB connection string from environment or command line"""
    import sys
    if len(sys.argv) > 1:
        return sys.argv[1]
    elif os.getenv('MONGODB_URL'):
        return os.getenv('MONGODB_URL')
    elif os.getenv('MONGODB_ATLAS_URL'):
        return os.getenv('MONGODB_ATLAS_URL')
    else:
        raise ValueError(
            "MongoDB connection string required. "
            "Set MONGODB_URL or MONGODB_ATLAS_URL environment variable, "
            "or create a .env file in the main SportAI Application folder"
        )

MONGODB_URL = get_mongodb_connection_string()
DATABASE_NAME = "sportai_documents"

# Global MongoDB client
client: AsyncIOMotorClient = None
database = None

async def connect_to_mongo():
    """Create database connection"""
    global client, database
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DATABASE_NAME]
    print(f"Connected to MongoDB: {DATABASE_NAME}")

async def close_mongo_connection():
    """Close database connection"""
    global client
    if client:
        client.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="SportAI LLM API",
    description="FastAPI service for LLM operations, document embedding, and vector database management",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "Welcome to SportAI LLM API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "check_connection": "GET /check_connection_with_db",
            "embed_documents": "POST /embed_all_docs",
            "query_llm": "POST /query",
            "api_docs": "GET /docs"
        }
    }

@app.get("/check_connection_with_db")
async def check_connection():
    """Test MongoDB connection"""
    try:
        await database.command("ping")
        return {"status": "Connected to MongoDB", "database": DATABASE_NAME}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to MongoDB: {e}")

# Global embedding model cache (lightweight)
_embedding_model_cache = None

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
async def query_llm(request: QueryRequest):
    """Query the LLM with a question - uses RAG to find relevant context and generate answer"""
    try:
        from sentence_transformers import SentenceTransformer
        from core.claude_llm import ClaudeLLM
        
        question = request.question
        logger.info(f"DEBUG: Received question: {question}")
        
        # Cache embedding model (lightweight, can stay in memory)
        global _embedding_model_cache
        if _embedding_model_cache is None:
            logger.debug("Loading embedding model (first time)")
            _embedding_model_cache = SentenceTransformer('all-MiniLM-L6-v2')
        embedding_model = _embedding_model_cache
        
        # Create vector client
        mongo_vector_client = MongoVectorClient(
            MONGODB_URL,
            DATABASE_NAME,
            "training_data",
            embedding_function=embedding_model
        )
        
        # Query vector database for relevant context
        logger.debug("Querying vector database for relevant context...")
        embedding_collection = mongo_vector_client.get_or_create_collection("training_data_embeddings")
        results = embedding_collection.query(
            query_texts=[question],
            n_results=3  # Get top 3 most relevant documents
        )
        
        # Log retrieved context
        logger.debug(f"Retrieved {len(results['documents'][0]) if results['documents'] else 0} documents from vector search")
        if results['documents'] and len(results['documents'][0]) > 0:
            for i, doc in enumerate(results['documents'][0][:3], 1):
                logger.debug(f"   Document {i} (first 200 chars): {doc[:200]}...")
        
        # Combine context from retrieved documents
        context = ""
        if results['documents'] and len(results['documents'][0]) > 0:
            context = "\n\n".join(results['documents'][0][:3])  # Use top 3 documents
            logger.info(f"DEBUG: Context retrieved ({len(context)} characters)")
            logger.debug(f"Full context:\n{context[:500]}...")  # Log first 500 chars
        else:
            logger.warning("No relevant context found in database")
            return {
                "question": question,
                "answer": "I couldn't find relevant information in the database to answer this question.",
                "context_found": False,
                "debug": {
                    "context": None,
                    "sources_used": 0
                }
            }
        
        # Use Claude LLM (fast, lightweight API)
        logger.info("Generating answer with Claude LLM...")
        
        claude_llm = ClaudeLLM()
        claude_llm.user_query = question  # Set the query
        
        # Generate answer using context
        answer = await claude_llm.generate_text(context, max_length=500)
        
        logger.info(f"DEBUG: Generated answer ({len(answer)} characters)")
        logger.debug(f"Full answer:\n{answer}")
        
        return {
            "question": question,
            "answer": answer,
            "context_found": True,
            "sources_used": len(results['documents'][0]) if results['documents'] else 0,
            "model_used": "claude-3-sonnet",
            "debug": {
                "context": context[:1000] if len(context) > 1000 else context,  # Include first 1000 chars of context
                "context_length": len(context),
                "sources_used": len(results['documents'][0]) if results['documents'] else 0,
                "persona_detected": claude_llm.detect_user_persona(question) if hasattr(claude_llm, 'detect_user_persona') else "unknown"
            }
        }
    except Exception as e:
        import traceback
        error_msg = f"Failed to query LLM: {e}\n{traceback.format_exc()}"
        logger.error(f"ERROR: {error_msg}")
        raise HTTPException(
            status_code=500, 
            detail=error_msg
        )

@app.post("/embed_all_docs")
async def embed_all_docs():
    """Embed all documents from training_data collection into vector database"""
    try:
        from sentence_transformers import SentenceTransformer
        
        # Initialize embedding model
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get documents from training_data collection (using sync client for pymongo compatibility)
        sync_client = MongoClient(MONGODB_URL)
        sync_db = sync_client[DATABASE_NAME]
        docs_cursor = sync_db.training_data.find({})
        docs_list = list(docs_cursor)
        sync_client.close()
        
        if not docs_list:
            return {"message": "No documents found in training_data collection", "count": 0}
        
        # Prepare documents for embedding (combine prompt and response)
        documents_to_embed = []
        metadatas = []
        ids = []
        
        for doc in docs_list:
            doc_id = str(doc.get('_id', ''))
            prompt = doc.get('prompt', '')
            response = doc.get('response', '')
            # Combine prompt and response for embedding
            combined_text = f"Prompt: {prompt}\nResponse: {response}"
            documents_to_embed.append(combined_text)
            metadatas.append({
                'category': doc.get('category', ''),
                'source_type': doc.get('source_type', ''),
                'original_id': doc_id
            })
            ids.append(doc_id)
        
        # Create vector client with embedding function
        mongo_vector_client = MongoVectorClient(
            MONGODB_URL, 
            DATABASE_NAME,
            "training_data",      # collection_name (base collection)
            embedding_function=embedding_model
        )
        
        # Get or create the embeddings collection
        embedding_collection = mongo_vector_client.get_or_create_collection("training_data_embeddings")
        
        # Add documents with embeddings
        embedding_collection.add(
            documents=documents_to_embed,
            metadatas=metadatas,
            ids=ids
        )
        
        return {
            "message": "Successfully embedded documents",
            "count": len(documents_to_embed),
            "collection": "training_data_embeddings"
        }
    except Exception as e:
        import traceback
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to embed documents: {e}\n{traceback.format_exc()}"
        )

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server on http://localhost:5001")
    print("Available endpoints:")
    print("  - GET /check_connection_with_db - Test MongoDB connection")
    print("  - POST /embed_all_docs - Embed all documents")
    print("  - GET /docs - Interactive API documentation")
    uvicorn.run("driver:app", host="0.0.0.0", port=5001, reload=True)
