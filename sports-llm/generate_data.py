#!/usr/bin/env python3
"""
Data Generation Runner
Run training data transformation and persona generation scripts
"""

import sys
import asyncio
from pathlib import Path

# Add the sports-llm directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    print("SportAI Data Generation")
    print("=" * 50)
    print("1. Training Data Transformer")
    print("2. Persona Training Generator")
    print("3. Both")
    print("=" * 50)
    
    choice = input("Select option (1-3): ").strip()
    
    if choice in ["1", "3"]:
        print("\nRunning Training Data Transformer...")
        from data_generation.training_transformer import TrainingDataTransformer
        transformer = TrainingDataTransformer()
        await transformer.run_transformation(limit=2)
    
    if choice in ["2", "3"]:
        print("\nRunning Persona Training Generator...")
        from data_generation.persona_training_generator import PersonaTrainingGenerator
        import os
        
        # Load environment variables from root .env file
        try:
            from dotenv import load_dotenv
            # Look for .env in the project root (one level up from this file)
            root_dir = Path(__file__).parent.parent
            env_file = root_dir / '.env'
            if env_file.exists():
                load_dotenv(env_file)
                print(f"Loaded .env from: {env_file}")
            else:
                print(f"Warning: .env file not found at {env_file}")
        except ImportError:
            print("Warning: python-dotenv not installed")
        
        mongodb_url = os.getenv('MONGODB_ATLAS_URL') or os.getenv('MONGODB_URL')
        database_name = os.getenv('DATABASE_NAME', 'sportai_documents')
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        
        if not mongodb_url or not claude_api_key:
            print("Missing environment variables. Check your .env file.")
            return
        
        generator = PersonaTrainingGenerator(mongodb_url, database_name, claude_api_key)
        await generator.run_persona_generation(limit=1)
    
    print("\nData generation complete!")

if __name__ == "__main__":
    asyncio.run(main())