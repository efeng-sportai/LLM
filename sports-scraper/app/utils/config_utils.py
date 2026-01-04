"""
Configuration Utilities
Helper functions for configuration management
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


def load_env_config(env_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load environment configuration from .env file
    
    Args:
        env_file: Path to .env file (optional, searches parent directories)
        
    Returns:
        Dictionary of environment variables
    """
    if env_file:
        load_dotenv(env_file)
    else:
        # Search for .env in current and parent directories
        current_dir = Path.cwd()
        for parent in [current_dir] + list(current_dir.parents):
            env_path = parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)
                print(f"Loaded .env from: {env_path}")
                break
    
    # Return relevant environment variables
    return {
        'mongodb_atlas_url': os.getenv('MONGODB_ATLAS_URL'),
        'mongodb_username': os.getenv('MONGODB_USERNAME'),
        'mongodb_password': os.getenv('MONGODB_PASSWORD'),
        'mongodb_cluster': os.getenv('MONGODB_CLUSTER'),
        'database_name': os.getenv('DATABASE_NAME', 'sportai_documents'),
        'host': os.getenv('HOST', '0.0.0.0'),
        'port': int(os.getenv('PORT', 8000)),
        'debug': os.getenv('DEBUG', 'False').lower() == 'true',
        'cors_origins': os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []
    }


def get_env_var(key: str, default: Any = None, required: bool = False) -> Any:
    """
    Get environment variable with validation
    
    Args:
        key: Environment variable key
        default: Default value if not found
        required: Whether the variable is required
        
    Returns:
        Environment variable value
        
    Raises:
        ValueError: If required variable is missing
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    
    return value


def validate_config(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Validate configuration and return any errors
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary of validation errors (empty if valid)
    """
    errors = {}
    
    # Check database configuration
    if not any([
        config.get('mongodb_atlas_url'),
        all([config.get('mongodb_username'), config.get('mongodb_password'), config.get('mongodb_cluster')])
    ]):
        errors['database'] = "No valid MongoDB configuration found"
    
    # Check required fields
    if not config.get('database_name'):
        errors['database_name'] = "Database name is required"
    
    # Validate port
    try:
        port = int(config.get('port', 8000))
        if port < 1 or port > 65535:
            errors['port'] = "Port must be between 1 and 65535"
    except (ValueError, TypeError):
        errors['port'] = "Port must be a valid integer"
    
    return errors