# LLM Module

A Python module for building and managing Large Language Models (LLMs) with vector database integration, pre-trained model support, and MongoDB-based document storage.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Setup](#setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Components](#components)
- [Project Structure](#project-structure)

## Features

- **Pre-trained Model Support**: Load and use pre-trained models from Keras Hub (GPT-2, Gemma)
- **Vector Database Integration**: MongoDB-based vector storage with similarity search
- **Embedding Support**: Automatic document embedding using Sentence Transformers
- **Context Generation**: Retrieve relevant context from vector database for RAG (Retrieval-Augmented Generation)
- **Fine-tuning**: Support for fine-tuning pre-trained models on custom datasets
- **Text Generation**: Generate text responses using loaded models with context
- **FastAPI**: Modern async RESTful API endpoints for LLM queries and document embedding

## Architecture

### Components

1. **LLM Class** (`LLM.py`)
   - Main class for managing LLM operations
   - Model loading from Keras Hub
   - Context generation from vector database
   - Text generation with context
   - Fine-tuning capabilities

2. **MongoVectorClient** (`mongo_vector_collection.py`)
   - MongoDB connection management
   - Document embedding and storage
   - Vector similarity search
   - Collection management

3. **MongoVectorCollection** (`mongo_vector_collection.py`)
   - Low-level vector collection operations
   - Document addition with embeddings
   - Similarity-based querying
   - Metadata support

4. **SportsBot Class** (`sports_bot_class.py`)
   - Specialized bot for sports-related queries
   - Integration with vector database
   - Question-answer management

5. **FastAPI Driver** (`driver.py`)
   - FastAPI REST API for LLM queries
   - RAG (Retrieval-Augmented Generation) implementation
   - Vector search integration
   - Model caching for performance
   - Document embedding endpoints
   - Connection testing

## Setup

### Prerequisites

- Python 3.8+
- MongoDB (local or MongoDB Atlas)
- Kaggle account and API credentials

### Installation

1. **Navigate to the LLM directory**:
   ```bash
   cd LLM
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the parent directory (`/SportAI Application/.env`):
   ```env
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
   MONGODB_ATLAS_URL=mongodb+srv://username:password@cluster.mongodb.net/
   DATABASE_NAME=sportai_documents
   ```
   
   The LLM service automatically loads `.env` from the parent directory.

### Kaggle API Setup

The module uses Kaggle API to download pre-trained models. You need to set up your Kaggle credentials:

1. **Get your Kaggle API credentials**:
   - Go to https://www.kaggle.com/account
   - Scroll to "API" section
   - Click "Create New Token" to download `kaggle.json`

2. **Place credentials in the correct location**:
   ```bash
   # Create .kaggle directory if it doesn't exist
   mkdir -p ~/.kaggle
   
   # Copy your kaggle.json file to ~/.kaggle/
   cp /path/to/your/kaggle.json ~/.kaggle/kaggle.json
   
   # Set proper permissions (required by Kaggle API)
   chmod 600 ~/.kaggle/kaggle.json
   ```

   The file should be located at: `~/.kaggle/kaggle.json`

   Format:
   ```json
   {"username":"your_username","key":"your_api_key"}
   ```

## Configuration

### MongoDB Connection

The module connects to MongoDB for vector storage. You can configure the connection in your code:

```python
from mongo_vector_collection import MongoVectorClient
from sentence_transformers import SentenceTransformer

# Initialize embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# MongoDB connection string
conn_string = "mongodb+srv://username:password@cluster.mongodb.net/?appName=AppName"
database_name = "sportai_documents"
collection_name = "training_data"

# Create client
client = MongoVectorClient(
    connection_string=conn_string,
    database_name=database_name,
    collection_name=collection_name,
    embedding_function=embedding_model
)
```

### Supported Models

Currently supported pre-trained models:
- **GPT-2**: `"gpt2"` - GPT-2 causal language model
- **Gemma**: `"gemma"` - Gemma 3 Instruct 4B model

## Usage

### Basic Example

```python
from LLM import LLM
from sentence_transformers import SentenceTransformer
from mongo_vector_collection import MongoVectorClient

# Setup embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Setup MongoDB client
client = MongoVectorClient(
    connection_string="mongodb+srv://...",
    database_name="sportai_documents",
    collection_name="training_data",
    embedding_function=embedding_model
)

# Create LLM instance
llm = LLM(
    user_query="What are the top NFL TE players?",
    pre_trained_model_path="gemma",
    embeddings_model=embedding_model
)

# Load the model
llm.load_pretrained_model()

# Get context from vector database
embedding_coll = client.get_or_create_collection('training_data_embeddings')
similar_texts = embedding_coll.query(
    query_texts=["What are the top NFL TE players?"],
    n_results=5
)

context = similar_texts['documents'][0][0] if similar_texts['documents'] else ""

# Generate response
output = llm.generate_text(context, max_length=300)
print(output)
```

### Adding Documents to Vector Database

```python
from mongo_vector_collection import MongoVectorClient
from sentence_transformers import SentenceTransformer

# Setup
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
client = MongoVectorClient(
    connection_string="mongodb+srv://...",
    database_name="sportai_documents",
    collection_name="training_data",
    embedding_function=embedding_model
)

# Get or create collection
collection = client.get_or_create_collection('training_data_embeddings')

# Add documents (embeddings are generated automatically)
collection.add(
    documents=[
        "Prompt: Who is the best quarterback? Response: Patrick Mahomes...",
        "Prompt: Top NFL teams? Response: Kansas City Chiefs..."
    ],
    metadatas=[
        {"category": "sports", "source": "sleeper"},
        {"category": "sports", "source": "sleeper"}
    ],
    ids=["doc1", "doc2"]
)
```

### Querying Similar Documents

```python
# Query by text (automatically embedded)
results = collection.query(
    query_texts=["NFL quarterback rankings"],
    n_results=10
)

# Access results
for i, doc_id in enumerate(results['ids'][0]):
    print(f"Document {i+1}: {results['documents'][0][i]}")
    print(f"Distance: {results['distances'][0][i]}")
    print(f"Metadata: {results['metadatas'][0][i]}")
```

### Fine-tuning a Model

```python
llm = LLM(
    user_query="",
    pre_trained_model_path="gemma"
)
llm.load_pretrained_model()

# Fine-tune on your dataset
llm.fine_tuning(
    train_set=train_dataset,
    val_set=val_dataset,
    BATCH_SIZE=32,
    EPOCHS=10,
    LEARNING_RATE=0.0001
)
```

### Using FastAPI Service

```bash
# Run the FastAPI server
cd LLM
python3 driver.py
```

The service runs on `http://localhost:5001` by default.

**Available endpoints**:
- `GET /` - API information
- `GET /check_connection_with_db` - Test MongoDB connection
- `POST /query` - Query the LLM with a question (RAG)
- `POST /embed_all_docs` - Embed all documents in the database
- `GET /docs` - Interactive Swagger UI documentation

**Example Query**:
```bash
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the top NFL TE players?"}'
```

**Response**:
```json
{
  "question": "What are the top NFL TE players?",
  "answer": "Based on the data...",
  "context_found": true,
  "sources_used": 3,
  "model_cached": true,
  "debug": {
    "context": "...",
    "prompt_template": "Context:\\n{context}\\n\\nQuestion: \\n{query}\\n\\n",
    "formatted_prompt": "..."
  }
}
```

## Components

### LLM Class

Main class for LLM operations.

**Methods**:
- `load_pretrained_model()` - Load a pre-trained model from Keras Hub
- `preprocess_input(input_text)` - Embed a query using the embedding model
- `generate_context()` - Retrieve relevant context from vector database
- `generate_text(input_context, max_length=300)` - Generate text response
- `fine_tuning(train_set, val_set, BATCH_SIZE, EPOCHS, LEARNING_RATE)` - Fine-tune the model

### MongoVectorClient

High-level client for MongoDB vector operations.

**Methods**:
- `test_client()` - Test MongoDB connection
- `generate_all_docs_to_embed()` - Extract all documents from training_data collection for embedding
- `get_or_create_collection(name)` - Get or create a vector collection

### MongoVectorCollection

Low-level vector collection operations.

**Methods**:
- `add(documents, embeddings, metadatas, ids)` - Add documents with embeddings
- `query(query_texts, query_embeddings, n_results, where, where_document)` - Query similar documents

## Project Structure

```
LLM/
├── LLM.py                      # Main LLM class
├── mongo_vector_collection.py  # MongoDB vector storage client
├── sports_bot_class.py         # Sports bot implementation
├── driver.py                   # FastAPI application and endpoints
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Dependencies

Key dependencies:
- **fastapi** - Modern async web framework
- **uvicorn** - ASGI server
- **motor** - Async MongoDB driver
- **pymongo** - MongoDB driver (sync operations)
- **keras** - Deep learning framework
- **keras-hub** - Pre-trained model hub
- **sentence-transformers** - Text embeddings
- **python-dotenv** - Environment variable management
- **pydantic** - Data validation
- **numpy** - Numerical operations
- **kaggle** - Kaggle API client

See `requirements.txt` for the complete list.

## Notes

- The module uses MongoDB for vector storage, compatible with MongoDB Atlas
- Embeddings are generated using Sentence Transformers (default: `all-MiniLM-L6-v2`)
- Pre-trained models are downloaded from Kaggle via Keras Hub
- Vector similarity search uses cosine similarity
- All documents are stored with their embeddings for fast similarity search
- **Model Caching**: LLM models are cached globally to avoid reloading on every request
- **First Load**: Model loading takes 30 seconds to 2 minutes (depends on GPU)
- **Subsequent Queries**: Use cached model (< 1 second to start generation)
- **RAG Flow**: Query → Vector Search → Context Retrieval → Prompt Construction → LLM Generation
- **Port**: Service runs on port 5001 by default

## Troubleshooting

### Kaggle Authentication Error

If you get authentication errors:
1. Verify `~/.kaggle/kaggle.json` exists and has correct format
2. Check file permissions: `chmod 600 ~/.kaggle/kaggle.json`
3. Verify your Kaggle API token is valid

### MongoDB Connection Error

If MongoDB connection fails:
1. Check your connection string format
2. Verify network access (for Atlas, check IP whitelist)
3. Verify credentials are correct
4. Test connection using `client.test_client()`

### Model Loading Error

If model loading fails:
1. Ensure Kaggle credentials are set up correctly
2. Check internet connection (models are downloaded from Kaggle)
3. Verify model name is correct (`"gpt2"` or `"gemma"`)

## License

[Add your license information here]

