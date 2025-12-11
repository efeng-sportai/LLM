# Installation Guide

Complete setup instructions for the SportAI LLM project.

## Prerequisites

### System Requirements
- **Python 3.8+** (Python 3.10+ recommended)
- **Node.js 16+** and **npm** (for frontend)
- **MongoDB** (local installation or MongoDB Atlas account)
- **Git** (for cloning the repository)

### Optional but Recommended
- **Kaggle account** (for downloading pre-trained models in LLM service)
- **Expo CLI** (will be installed with npm packages)

---

## 1. Frontend Setup (React Native/Expo)

### Install Node.js Dependencies

```bash
cd frontend
npm install
```

This will install:
- Expo (~54.0.25)
- React (19.1.0)
- React Native (0.81.5)
- TypeScript and type definitions

### Running the Frontend

```bash
# Start Expo development server
npm start

# Or run on specific platform
npm run ios      # iOS Simulator (Mac only)
npm run android  # Android Emulator
npm run web      # Web browser
```

**Note**: Make sure to update the API URL in `App.tsx` if your LLM service runs on a different host/port.

---

## 2. LLM Service Setup (Python)

### Create Virtual Environment

```bash
cd sports-llm
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **Keras** (>=3.0.0) - Deep learning framework
- **Keras NLP** (>=0.3.0) - Natural language processing
- **LangChain Community** (>=0.0.20) - Vector stores
- **PyMongo** (>=4.6.0) - MongoDB driver
- **Motor** (>=3.3.0) - Async MongoDB driver
- **Sentence Transformers** (>=2.2.0) - Text embeddings
- **FastAPI** (>=0.104.0) - Web framework
- **Uvicorn** - ASGI server
- **NumPy** (>=1.24.0) - Numerical operations
- **Kaggle** (>=1.5.0) - Kaggle API client
- **python-dotenv** (>=1.0.0) - Environment variables

### Kaggle API Setup (Optional but Recommended)

If you plan to use pre-trained models:

1. Get your Kaggle API credentials:
   - Go to https://www.kaggle.com/account
   - Scroll to "API" section
   - Click "Create New Token" to download `kaggle.json`

2. Place credentials:
   ```bash
   mkdir -p ~/.kaggle
   cp /path/to/your/kaggle.json ~/.kaggle/kaggle.json
   chmod 600 ~/.kaggle/kaggle.json
   ```

### Running the LLM Service

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the FastAPI server
python driver.py
```

The service will run on `http://localhost:5001` by default.

---

## 3. Scraper Service Setup (Python)

### Create Virtual Environment

```bash
cd sports-scraper
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **FastAPI** (==0.104.1) - Web framework
- **Uvicorn** (==0.24.0) - ASGI server
- **Pydantic** (==2.5.0) - Data validation
- **Motor** (==3.3.2) - Async MongoDB driver
- **PyMongo** (==4.6.0) - MongoDB driver
- **BeautifulSoup4** (==4.12.2) - HTML parsing
- **lxml** (==4.9.3) - XML/HTML parser
- **Requests** (==2.31.0) - HTTP client
- **python-dateutil** (==2.8.2) - Date utilities
- **python-dotenv** (==1.0.0) - Environment variables

### Running the Scraper Service

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the FastAPI server
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The service will run on `http://localhost:8000` by default.

---

## 4. Environment Configuration

### Create `.env` File

Create a `.env` file in the **root directory** (`/SportAI LLM/.env`):

```env
# MongoDB Configuration
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_ATLAS_URL=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=sportai_documents

# LLM Service Configuration (optional)
LLM_HOST=0.0.0.0
LLM_PORT=5001

# Scraper Service Configuration (optional)
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

**Important**: Both the LLM and Scraper services load `.env` from the parent directory.

---

## 5. MongoDB Setup

### Option A: MongoDB Atlas (Cloud - Recommended)

1. Create a free account at https://www.mongodb.com/cloud/atlas
2. Create a new cluster
3. Get your connection string
4. Add it to your `.env` file as `MONGODB_URL` or `MONGODB_ATLAS_URL`
5. Whitelist your IP address in Atlas dashboard

### Option B: Local MongoDB

**macOS (using Homebrew)**:
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Linux**:
```bash
sudo systemctl start mongod
```

**Docker**:
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

For local MongoDB, use: `mongodb://localhost:27017` in your `.env` file.

---

## Quick Start Summary

1. **Install Node.js dependencies**:
   ```bash
   cd frontend && npm install
   ```

2. **Set up LLM service**:
   ```bash
   cd sports-llm
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up Scraper service**:
   ```bash
   cd sports-scraper
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create `.env` file** in root directory with MongoDB connection string

5. **Start services**:
   ```bash
   # Terminal 1: LLM Service
   cd sports-llm
   source venv/bin/activate
   python driver.py

   # Terminal 2: Scraper Service
   cd sports-scraper
   source venv/bin/activate
   python main.py

   # Terminal 3: Frontend
   cd frontend
   npm start
   ```

---

## Verification

### Test LLM Service
```bash
curl http://localhost:5001/
curl http://localhost:5001/check_connection_with_db
```

### Test Scraper Service
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Interactive API documentation
```

### Test Frontend
- Open Expo Go app on your phone and scan QR code
- Or press `i` for iOS simulator / `a` for Android emulator

---

## Troubleshooting

### Python Virtual Environment Issues
- Make sure you're using Python 3.8+
- Check: `python3 --version`
- If `venv` command fails, try: `python3 -m venv venv`

### MongoDB Connection Issues
- Verify connection string format
- Check network access (for Atlas, verify IP whitelist)
- Test connection: `mongosh "your_connection_string"`

### Port Already in Use
- LLM service uses port 5001
- Scraper service uses port 8000
- Change ports in `.env` or kill processes using those ports

### Node.js/Expo Issues
- Clear cache: `npm start -- --clear`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

### Kaggle Authentication Errors
- Verify `~/.kaggle/kaggle.json` exists
- Check permissions: `chmod 600 ~/.kaggle/kaggle.json`
- Verify token is valid

---

## Next Steps

- Read `sports-llm/README.md` for LLM service details
- Read `sports-scraper/README.md` for Scraper service details
- Read `frontend/README.md` for frontend details
- Check API documentation at `http://localhost:8000/docs` (Scraper) and `http://localhost:5001/docs` (LLM)

