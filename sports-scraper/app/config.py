from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
import os

# Load .env from parent directory (main SportAI Application folder)
try:
    from dotenv import load_dotenv
    parent_dir = Path(__file__).parent.parent.parent  # Go up from app/config.py -> Scraper -> SportAI Application
    parent_env_file = parent_dir / '.env'
    if parent_env_file.exists():
        load_dotenv(parent_env_file)
        print(f"Loaded .env from parent directory: {parent_env_file}")
    else:
        print(f"Warning: .env file not found at {parent_env_file}")
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"Error: Could not load .env file: {e}")

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    app_name: str = "SportAI API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # AI Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.7
    
    # CORS Configuration
    cors_origins: list = ["http://localhost:3000", "http://localhost:4200", "http://localhost:5173"]
    
    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"  # Default to local
    database_name: str = "sportai_documents"
    
    # Cloud MongoDB Configuration (for Atlas, etc.)
    mongodb_atlas_url: Optional[str] = None  # Override with cloud connection string
    mongodb_username: Optional[str] = None
    mongodb_password: Optional[str] = None
    mongodb_cluster: Optional[str] = None
    
    class Config:
        # Environment variables are loaded from parent .env file above
        # No local .env file - all config comes from parent directory
        env_file_encoding = "utf-8"

settings = Settings()
