#!/usr/bin/env python3
"""
Persona-Based Training Data Generator
Creates training data tailored to different user personas using Claude AI
"""

import asyncio
import json
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import re
from typing import Dict, List, Any

class PersonaTrainingGenerator:
    """Generate training data based on user personas"""
    
    def __init__(self, mongodb_url: str, database_name: str, claude_api_key: str):
        self.mongodb_url = mongodb_url
        self.database_name = database_name
        self.claude_api_key = claude_api_key
        self.claude_url = "https://api.anthropic.com/v1/messages"
        self.client = None
        self.database = None
        
        # Define user personas
        self.personas = {
            "fred_newbie": {
                "name": "Fred, The Newbie",
                "age": 16,
                "experience": "Never knew what fantasy sports was",
                "sports_knowledge": "Doesn't watch sports. Mostly plays video games",
                "fantasy_frequency": "Just discovered SportAI on Instagram",
                "needs": ["Basic explanations", "Simple terminology", "Step-by-step guidance"],
                "question_style": ["What is...?", "How do I...?", "Why should I...?"]
            },
            "john_rookie": {
                "name": "John, The Rookie", 
                "age": 20,
                "experience": "Amateur fantasy sports player. Only plays because friends do",
                "sports_knowledge": "Watches NBA, knows players but isn't a stats junkie",
                "fantasy_frequency": "Single tournament with friends on weekends",
                "needs": ["Player comparisons", "Basic strategy", "Confidence building"],
                "question_style": ["Should I...?", "Is X better than Y?", "Who should I start?"]
            },
            "alice_dabbler": {
                "name": "Alice, The Dabbler",
                "age": 33,
                "experience": "Passively plays in multiple tournaments",
                "sports_knowledge": "Stats junkie. Can name every hall-of-fame QB in past 20 years",
                "fantasy_frequency": "Checks roster a few times a week",
                "needs": ["Advanced analytics", "Trend analysis", "Optimization tips"],
                "question_style": ["What are the trends for...?", "How do I optimize...?", "What's the data on...?"]
            },
            "max_professional": {
                "name": "Max, The Professional",
                "age": 34,
                "experience": "Consistently watches leagues throughout the day",
                "sports_knowledge": "If it's on TV and involves a ball, he's watching it",
                "fantasy_frequency": "It might as well be his day job",
                "needs": ["Deep analysis", "Edge cases", "Advanced strategies"],
                "question_style": ["What's the advanced strategy for...?", "How do I get an edge with...?", "What are the pros doing with...?"]
            }
        }
    
    async def connect_to_mongo(self):
        """Connect to MongoDB"""
        self.client = AsyncIOMotorClient(self.mongodb_url)
        self.database = self.client[self.database_name]
        await self.client.admin.command('ping')
        print("Connected to MongoDB")
    
    async def call_claude_api(self, prompt: str) -> str:
        """Call Claude API"""
        headers = {
            "x-api-key": self.claude_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.claude_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['content'][0]['text']
                    else:
                        return f"Error: Could not generate response for this persona"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def create_persona_prompt(self, persona_key: str, data: Dict, question_type: str) -> str:
        """Create persona-specific prompts"""
        
        persona = self.personas[persona_key]
        
        base_context = f"""You are a fantasy football expert responding to {persona['name']}.

PERSONA CONTEXT:
- Age: {persona['age']}
- Experience: {persona['experience']}
- Sports Knowledge: {persona['sports_knowledge']}
- Fantasy Frequency: {persona['fantasy_frequency']}
- Needs: {', '.join(persona['needs'])}

RESPONSE GUIDELINES:
- Adjust complexity to their experience level
- Use terminology appropriate for their knowledge
- Address their specific needs and concerns
- Match their typical question style

DATA TO USE:
{json.dumps(data, indent=2)}

"""
        
        if question_type == "start_sit" and persona_key == "fred_newbie":
            return base_context + f"""
TASK: Fred just discovered fantasy sports and needs basic start/sit help.

Question: "I don't really know much about fantasy football. Should I start {data.get('player_name', 'this player')}? What does that even mean?"

Response should:
- Explain what "starting" means in fantasy
- Give simple, clear advice
- Avoid complex stats
- Build confidence
- Use encouraging tone (no emojis)
"""
        
        elif question_type == "start_sit" and persona_key == "john_rookie":
            return base_context + f"""
TASK: John plays casually with friends and needs straightforward advice.

Question: "Should I start {data.get('player_name', 'this player')} this week? My friends will roast me if I make a bad choice."

Response should:
- Give confident recommendation
- Include simple reasoning
- Compare to alternatives
- Help him look smart to friends
"""
        
        elif question_type == "start_sit" and persona_key == "alice_dabbler":
            return base_context + f"""
TASK: Alice knows stats and wants data-driven analysis.

Question: "Looking at the data, should I start {data.get('player_name', 'this player')}? What do the trends show?"

Response should:
- Include specific statistics
- Mention trends and patterns
- Reference historical performance
- Give analytical reasoning
"""
        
        elif question_type == "start_sit" and persona_key == "max_professional":
            return base_context + f"""
TASK: Max is an expert who wants advanced strategy insights.

Question: "What's the advanced play with {data.get('player_name', 'this player')} this week? Any edge angles I should consider?"

Response should:
- Discuss advanced metrics
- Mention game theory aspects
- Consider contrarian plays
- Reference pro strategies
"""
        
        elif question_type == "player_explanation" and persona_key == "fred_newbie":
            return base_context + f"""
TASK: Fred needs basic player explanations.

Question: "I keep hearing about {data.get('player_name', 'this player')}. Can you explain who he is and why people care about him in fantasy?"

Response should:
- Explain the player's role simply
- Why he's fantasy relevant
- Basic stats in plain English
- What to expect from him
"""
        
        return base_context + f"Create appropriate response for {persona['name']} about: {json.dumps(data, indent=2)}"
    
    async def generate_persona_training_data(self, original_doc: Dict) -> List[Dict]:
        """Generate training data for all personas based on original document"""
        
        # Extract player data from original document
        response_text = original_doc.get('response', '')
        metadata = original_doc.get('metadata', {})
        
        # Extract top players
        players = self.extract_players_from_response(response_text)
        
        training_docs = []
        
        if players:
            # Generate different types of questions for each persona
            for persona_key, persona in self.personas.items():
                
                # Start/Sit questions for top 2 players
                for player in players[:2]:
                    prompt_text = self.create_persona_prompt(persona_key, player, "start_sit")
                    response = await self.call_claude_api(prompt_text)
                    
                    # Create question based on persona style
                    if persona_key == "fred_newbie":
                        question = f"I'm new to fantasy football. Should I start {player['player_name']}? What does that mean?"
                    elif persona_key == "john_rookie":
                        question = f"Should I start {player['player_name']} this week? My friends will judge me if I mess up."
                    elif persona_key == "alice_dabbler":
                        question = f"Based on the data, should I start {player['player_name']}? What do the trends show?"
                    else:  # max_professional
                        question = f"What's the advanced strategy with {player['player_name']} this week? Any edge plays?"
                    
                    doc = {
                        "prompt": question,
                        "response": response,
                        "context": f"Fantasy advice for {persona['name']} - {player['player_name']} start/sit analysis",
                        "category": "persona_start_sit_advice",
                        "difficulty_level": self.get_difficulty_for_persona(persona_key),
                        "source_type": "persona_based_expert_advice",
                        "metadata": {
                            "original_doc_id": str(original_doc.get('_id')),
                            "persona": persona_key,
                            "persona_name": persona['name'],
                            "player_name": player['player_name'],
                            "position": player.get('position'),
                            "advice_type": "start_sit",
                            "ai_model": "claude-sonnet-4",
                            "transformed_at": datetime.utcnow().isoformat()
                        },
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "is_active": True
                    }
                    training_docs.append(doc)
                
                # Player explanation for Fred (newbie needs basic info)
                if persona_key == "fred_newbie" and players:
                    top_player = players[0]
                    prompt_text = self.create_persona_prompt(persona_key, top_player, "player_explanation")
                    response = await self.call_claude_api(prompt_text)
                    
                    doc = {
                        "prompt": f"I keep hearing about {top_player['player_name']}. Can you explain who he is and why he matters in fantasy?",
                        "response": response,
                        "context": f"Basic player explanation for {persona['name']} - {top_player['player_name']}",
                        "category": "persona_player_explanation",
                        "difficulty_level": "beginner",
                        "source_type": "persona_based_expert_advice",
                        "metadata": {
                            "original_doc_id": str(original_doc.get('_id')),
                            "persona": persona_key,
                            "persona_name": persona['name'],
                            "player_name": top_player['player_name'],
                            "position": top_player.get('position'),
                            "advice_type": "player_explanation",
                            "ai_model": "claude-sonnet-4",
                            "transformed_at": datetime.utcnow().isoformat()
                        },
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "is_active": True
                    }
                    training_docs.append(doc)
        
        return training_docs
    
    def extract_players_from_response(self, response_text: str) -> List[Dict]:
        """Extract player data from statistical response"""
        players = []
        lines = response_text.split('\n')
        
        for line in lines:
            match = re.match(r'(\d+)\.\s*([^(]+)\s*\(([^)]+)\)\s*-\s*([^-]+)\s*-\s*(.+)', line.strip())
            if match and len(players) < 5:
                rank, name, position, team, stats = match.groups()
                players.append({
                    'rank': int(rank),
                    'player_name': name.strip(),
                    'position': position.strip(),
                    'team': team.strip(),
                    'stats_summary': stats.strip()
                })
        
        return players
    
    def get_difficulty_for_persona(self, persona_key: str) -> str:
        """Get difficulty level based on persona"""
        difficulty_map = {
            "fred_newbie": "beginner",
            "john_rookie": "beginner", 
            "alice_dabbler": "intermediate",
            "max_professional": "advanced"
        }
        return difficulty_map.get(persona_key, "intermediate")
    
    async def run_persona_generation(self, limit: int = 2):
        """Generate persona-based training data"""
        
        await self.connect_to_mongo()
        training_collection = self.database.training_data
        
        print("Generating Persona-Based Training Data")
        print("=" * 60)
        print("Creating training data for:")
        for persona_key, persona in self.personas.items():
            print(f"  • {persona['name']} ({persona['experience']})")
        print()
        
        # Get source documents
        cursor = training_collection.find({
            "source_type": "sleeper_scraper",
            "category": "player_list"
        }).limit(limit)
        
        docs = await cursor.to_list(length=limit)
        all_training_docs = []
        
        for i, doc in enumerate(docs, 1):
            print(f"Processing document {i}/{len(docs)}: {doc.get('category')}")
            
            try:
                persona_docs = await self.generate_persona_training_data(doc)
                all_training_docs.extend(persona_docs)
                
                print(f"   Created {len(persona_docs)} persona-based documents")
                
                # Show breakdown by persona
                persona_counts = {}
                for pdoc in persona_docs:
                    persona_name = pdoc['metadata']['persona_name']
                    persona_counts[persona_name] = persona_counts.get(persona_name, 0) + 1
                
                for persona_name, count in persona_counts.items():
                    print(f"      {persona_name}: {count} documents")
                
            except Exception as e:
                print(f"   Error: {e}")
                continue
            
            # Delay between API calls
            await asyncio.sleep(2)
        
        # Save all documents
        if all_training_docs:
            result = await training_collection.insert_many(all_training_docs)
            print(f"\nCreated {len(result.inserted_ids)} persona-based training documents!")
            
            # Show samples
            print("\nSample Persona Training Data:")
            print("=" * 70)
            
            for persona_key in self.personas.keys():
                persona_docs = [doc for doc in all_training_docs if doc['metadata']['persona'] == persona_key]
                if persona_docs:
                    sample = persona_docs[0]
                    print(f"\n{sample['metadata']['persona_name']}:")
                    print(f"   Q: {sample['prompt']}")
                    print(f"   A: {sample['response'][:150]}...")
        
        self.client.close()

async def main():
    """Main function"""
    
    # Load environment variables
    import os
    from pathlib import Path
    
    try:
        from dotenv import load_dotenv
        # Look for .env in the project root (three levels up from this file)
        root_dir = Path(__file__).parent.parent.parent
        env_file = root_dir / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            print(f"Loaded .env from: {env_file}")
        else:
            print(f"Warning: .env file not found at {env_file}")
    except ImportError:
        print("Warning: python-dotenv not installed")
    
    # Configuration from environment
    mongodb_url = os.getenv('MONGODB_ATLAS_URL') or os.getenv('MONGODB_URL')
    database_name = os.getenv('DATABASE_NAME', 'sportai_documents')
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    
    if not mongodb_url:
        raise ValueError("MongoDB URL not found in environment variables")
    if not claude_api_key:
        raise ValueError("Claude API key not found in environment variables")
    
    print("SportAI Persona-Based Training Data Generator")
    print("=" * 60)
    print("This creates training data tailored to your user personas:")
    print("• Fred (Newbie) - Basic explanations and guidance")
    print("• John (Rookie) - Simple advice to impress friends") 
    print("• Alice (Dabbler) - Data-driven analysis")
    print("• Max (Professional) - Advanced strategies")
    print()
    
    generator = PersonaTrainingGenerator(mongodb_url, database_name, claude_api_key)
    await generator.run_persona_generation(limit=1)

if __name__ == "__main__":
    asyncio.run(main())