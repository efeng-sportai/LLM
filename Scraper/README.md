# SportAI Backend API

A FastAPI-based backend service for managing sports data, training data, user interactions, and feedback. This system provides a comprehensive API for scraping sports data, managing training datasets, tracking user interactions, and collecting feedback for AI model improvement.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Setup](#setup)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Database Structure](#database-structure)
- [Running the Server](#running-the-server)
- [Testing](#testing)
- [Project Structure](#project-structure)

## Features

- **Sports Data Scraping**: Automated scraping of NFL data from Sleeper API and ESPN
- **Training Data Management**: Create, query, and export training data for AI model fine-tuning
- **User Interaction Tracking**: Record and analyze user queries and AI responses
- **Feedback System**: Collect and analyze user feedback (thumbs up/down) for quality improvement
- **Document Processing**: Process URLs and convert them to structured documents
- **MongoDB Integration**: Async MongoDB operations using Motor
- **RESTful API**: Comprehensive REST API with automatic OpenAPI documentation

## Architecture

### Components

1. **FastAPI Application** (`main.py`)
   - Main application entry point
   - CORS middleware configuration
   - Router registration and lifecycle management

2. **Routers** (`app/routers/`)
   - `health.py` - Health check endpoints
   - `api.py` - General API endpoints
   - `training_data.py` - Training data CRUD operations
   - `sports.py` - Sports data scraping endpoints
   - `populate.py` - Data population endpoints
   - `interactions.py` - User interaction tracking
   - `feedback.py` - User feedback collection
   - `documents.py` - Document management

3. **Services** (`app/services/`)
   - `sports_scraper.py` - Low-level sports data scraping
   - `data_populator.py` - High-level data population orchestration
   - `document_processor.py` - URL processing and document creation

4. **Database** (`app/database.py`)
   - MongoDB connection management
   - Collection accessors

5. **Schemas** (`app/schemas.py`)
   - Pydantic models for request/response validation

## Setup

### Prerequisites

- Python 3.8+
- MongoDB (local or MongoDB Atlas)
- pip

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   cd backend
   ```

2. **Create a virtual environment**:
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
   # MongoDB Configuration
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
   MONGODB_ATLAS_URL=mongodb+srv://username:password@cluster.mongodb.net/
   DATABASE_NAME=sportai_documents
   
   # Server Configuration (optional, defaults provided)
   HOST=0.0.0.0
   PORT=8000
   DEBUG=False
   
   # CORS Origins (comma-separated)
   CORS_ORIGINS=http://localhost:3000,http://localhost:4200,http://localhost:5173
   
   # AI Configuration (optional)
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   DEFAULT_MODEL=gpt-3.5-turbo
   ```
   
   **Note**: The Scraper service loads `.env` from the parent directory (`/SportAI Application/.env`) to share configuration with the LLM service.

5. **Start MongoDB** (if using local MongoDB):
   ```bash
   # macOS (using Homebrew)
   brew services start mongodb-community
   
   # Linux
   sudo systemctl start mongod
   
   # Or use Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```

## Configuration

Configuration is managed through environment variables and the `Settings` class in `app/config.py`. The system supports:

- **Local MongoDB**: Default connection to `mongodb://localhost:27017`
- **MongoDB Atlas**: Cloud MongoDB connection via `MONGODB_ATLAS_URL`
- **CORS**: Configurable allowed origins for cross-origin requests
- **AI Models**: Optional API keys for OpenAI and Anthropic

See `app/config.py` for all available configuration options.

## API Endpoints

### Health Check
- `GET /health` - Health check endpoint
- `GET /health/detailed` - Detailed health information

### Training Data
- `POST /training-data/` - Create training data entry
- `POST /training-data/batch` - Create multiple training data entries
- `GET /training-data/` - List training data with filters
- `GET /training-data/{id}` - Get specific training data entry
- `PUT /training-data/{id}` - Update training data entry
- `DELETE /training-data/{id}` - Delete training data entry
- `GET /training-data/export` - Export training data (JSONL, CSV, JSON)
- `GET /training-data/stats` - Get training data statistics

### Sports Data
- `GET /sports/sleeper/user` - Get Sleeper user information
- `GET /sports/sleeper/leagues` - Get user's leagues
- `GET /sports/sleeper/league/{league_id}` - Get league details
- `GET /sports/sleeper/matchups` - Get league matchups
- `POST /sports/sleeper/batch-scrape` - Batch scrape multiple URLs

### Data Population
- `POST /populate/sleeper/schedule` - Populate NFL schedule
- `POST /populate/sleeper/team-rankings` - Populate team rankings
- `POST /populate/sleeper/players` - Populate player rankings
- `POST /populate/sleeper/standings` - Populate NFL standings
- `POST /populate/sleeper/injured-players` - Populate injured players
- `POST /populate/sleeper/player-news` - Populate player news
- `GET /populate/stats` - Get population statistics

### User Interactions
- `POST /interactions/` - Create interaction record
- `GET /interactions/` - List interactions with filters
- `GET /interactions/{id}` - Get specific interaction
- `POST /interactions/backfeed` - Backfeed interactions as training data

### Feedback
- `POST /feedback/` - Submit user feedback
- `GET /feedback/` - List feedback with filters
- `GET /feedback/stats` - Get feedback statistics
- `GET /feedback/training-data` - Get training data with feedback scores

### API Documentation
- `GET /docs` - Interactive Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Database Structure

The backend uses MongoDB with the following collections:

### Collections

1. **training_data**
   - Stores all training data for AI model fine-tuning
   - Includes prompts, responses, context, categories, and metadata
   - Used by sports scraper to save scraped data

2. **interactions**
   - User interaction records (queries and AI responses)
   - Linked to sessions and documents

3. **feedback**
   - User feedback (positive/negative) on interactions or documents
   - Used for quality assessment and model improvement

4. **documents**
   - Processed documents from URLs or user input
   - Contains content, metadata, and source information

### Data Models

See `app/schemas.py` for complete Pydantic models defining the data structure for each collection.

## Running the Server

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

### Run Tests

```bash
# Run all tests
python run_tests.py

# Run specific test file
python -m pytest tests/test_training_data.py -v
```

### Test Files

- `tests/test_mongodb_connection.py` - MongoDB connection tests
- `tests/test_training_data.py` - Training data CRUD tests
- `tests/test_feedback.py` - Feedback system tests
- `tests/test_complete_system.py` - Integration tests
- `tests/populate_test_data.py` - Test data population

## Project Structure

```
Scraper/
├── app/
│   ├── __init__.py
│   ├── config.py              # Application configuration
│   ├── database.py            # MongoDB connection and collections
│   ├── schemas.py             # Pydantic models
│   ├── routers/               # API route handlers
│   │   ├── api.py
│   │   ├── documents.py
│   │   ├── feedback.py
│   │   ├── health.py
│   │   ├── interactions.py
│   │   ├── populate.py
│   │   ├── sports.py
│   │   └── training_data.py
│   └── services/              # Business logic services
│       ├── data_populator.py
│       ├── document_processor.py
│       ├── sports_scraper.py
│       └── scrapers/           # Scraper implementations
│           ├── base_scraper.py
│           ├── sleeper_api.py
│           ├── nfl_schedule.py
│           ├── nfl_rankings.py
│           ├── nfl_standings.py
│           └── nfl_news.py
├── tests/                     # Test files
├── main.py                    # FastAPI application entry point
├── populate_sports_data.py    # Sports data population script
├── example_usage.py           # Example usage scripts
├── requirements.txt           # Python dependencies
├── run_tests.py              # Test runner
├── README.md                 # This file
└── SPORTS_SCRAPER_README.md  # Detailed sports scraper documentation
```

## Sports Data Scraping

For detailed information about the sports data scraping system, including:
- How to populate NFL data
- Data sources and APIs
- Document structure
- Usage examples

See [SPORTS_SCRAPER_README.md](./SPORTS_SCRAPER_README.md)

## Example Usage

### Populate Sports Data

```bash
# Run the population script
python populate_sports_data.py
```

### Use the API

```python
import requests

# Create training data
response = requests.post("http://localhost:8000/training-data/", json={
    "prompt": "Who is the best quarterback?",
    "response": "Patrick Mahomes is considered one of the best quarterbacks...",
    "category": "sports",
    "source_type": "manual"
})

# Get training data
response = requests.get("http://localhost:8000/training-data/?category=sports")
```

See `example_usage.py` for more comprehensive examples.

## Dependencies

Key dependencies:
- **FastAPI** - Modern web framework
- **Motor** - Async MongoDB driver
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server
- **BeautifulSoup4** - HTML parsing
- **Requests** - HTTP client

See `requirements.txt` for the complete list.

## License

[Add your license information here]

## Contributing

[Add contributing guidelines here]

