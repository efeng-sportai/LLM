#!/usr/bin/env python3
"""
SportAI LLM - Main Entry Point
Claude-only Fantasy Football AI with FastAPI server
"""

import sys
import os
from pathlib import Path

# Add the sports-llm directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    from api.driver import app
    import uvicorn
    
    print("Starting SportAI LLM Server")
    print("=" * 50)
    print("Claude-only Fantasy Football AI")
    print("Server: http://localhost:5001")
    print("API Docs: http://localhost:5001/docs")
    print("=" * 50)
    
    uvicorn.run("api.driver:app", host="0.0.0.0", port=5001, reload=True)