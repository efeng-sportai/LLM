#!/usr/bin/env python3
"""
Training Data Transformer for SportAI
Converts statistical data into expert fantasy football advice using Claude AI
"""

import asyncio
import json
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import re
from typing import Dict, List, Any
import os
from pathlib import Path

# Load environment variables from root .env file
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

class TrainingDataTransformer:
    """Transform statistical data into expert advice using Claude AI"""
    
    def __init__(self):
        # Get configuration from environment
        self.mongodb_url = os.getenv('MONGODB_ATLAS_URL') or os.getenv('MONGODB_URL')
        self.database_name = os.getenv('DATABASE_NAME', 'sportai_documents')
        self.claude_api_key = os.getenv('CLAUDE_API_KEY')
        
        if not self.mongodb_url:
            raise ValueError("MongoDB URL not found in environment variables")
        if not self.claude_api_key:
            raise ValueError("Claude API key not found in environment variables. Please set CLAUDE_API_KEY in your .env file")
        
        self.claude_url = "https://api.anthropic.com/v1/messages"
        self.client = None
        self.database = None
    
    async def connect_to_mongo(self):
        """Connect to MongoDB"""
        self.client = AsyncIOMotorClient(self.mongodb_url)
        self.database = self.client[self.database_name]
        await self.client.admin.command('ping')
        print("Connected to MongoDB")
    
    async def call_claude_api(self, prompt: str) -> str:
        """Call Claude API to transform data"""
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
                        error_text = await response.text()
                        print(f"Claude API error {response.status}: {error_text}")
                        return self.fallback_transformation()
        except Exception as e:
            print(f"Claude API request failed: {e}")
            return self.fallback_transformation()
    
    def fallback_transformation(self) -> str:
        """Fallback if Claude API fails"""
        return "Based on current performance and matchup data, consider this player's recent trends and injury status when making your fantasy decision. Monitor practice reports and weather conditions for additional context."
    
    def create_expert_prompt(self, data: Dict, advice_type: str) -> str:
        """Create prompts for Claude to generate expert fantasy advice"""
        
        base_context = """You are Matthew Berry, a top fantasy football expert writing for ESPN. Convert the following statistical data into conversational, actionable fantasy football advice that helps users make lineup decisions.

Guidelines:
- Write like you're talking to a fantasy owner who needs to make a decision
- Use fantasy football terminology (RB1, WR2, PPR, start/sit, waiver wire, etc.)
- Be confident but acknowledge uncertainty when appropriate
- Focus on actionable advice, not just stats
- Keep responses 2-3 sentences for quick decisions
- Include specific reasoning based on the data provided
- Use an engaging, slightly casual tone like Matthew Berry (no emojis)

"""
        
        if advice_type == "start_sit":
            return base_context + f"""
TASK: Create start/sit advice for this player

PLAYER DATA:
{json.dumps(data, indent=2)}

Question: "Should I start {data.get('player_name', 'this player')} this week?"

Focus on:
- Clear start or sit recommendation
- Specific reasons based on matchup, recent performance, or trends
- Risk/reward assessment
- Alternative suggestions if sitting
- Confidence level in the recommendation

Response format: Direct advice in 2-3 sentences explaining your recommendation with Matthew Berry's engaging style (no emojis).
"""
        
        elif advice_type == "waiver_wire":
            return base_context + f"""
TASK: Create waiver wire pickup advice

AVAILABLE PLAYERS DATA:
{json.dumps(data, indent=2)}

Question: "Who should I pick up on waivers this week?"

Focus on:
- Top 1-2 waiver wire targets from the data
- Why they're worth adding (opportunity, matchup, breakout potential)
- How much FAAB to spend or waiver priority to use
- What type of leagues they're valuable in
- Urgency level of the pickup

Response format: Prioritized recommendations with reasoning in 2-3 sentences.
"""
        
        elif advice_type == "player_rankings":
            return base_context + f"""
TASK: Convert player rankings into draft/roster advice

RANKINGS DATA:
{json.dumps(data, indent=2)}

Question: "Who should I target at {data.get('position', 'this position')} in fantasy?"

Focus on:
- Top tier players worth targeting early
- Value picks in middle/later rounds
- Players to avoid and why
- Differences between PPR and standard scoring if relevant
- Draft strategy for this position

Response format: Tiered recommendations with reasoning in 2-3 sentences.
"""
        
        elif advice_type == "trade_analysis":
            return base_context + f"""
TASK: Create trade value analysis

PLAYER DATA:
{json.dumps(data, indent=2)}

Question: "What's {data.get('player_name', 'this player')}'s trade value right now?"

Focus on:
- Current trade value tier (elite, high-end, mid-tier, low)
- What type of return to expect in trades
- Whether to buy, sell, or hold
- Factors affecting value (schedule, injury risk, age, etc.)
- Best time to make a move

Response format: Clear trade recommendation with reasoning in 2-3 sentences.
"""
        
        return base_context + f"Convert this data into fantasy football advice: {json.dumps(data, indent=2)}"
    
    def extract_top_players_from_response(self, response_text: str, limit: int = 10) -> List[Dict]:
        """Extract player information from statistical response"""
        players = []
        lines = response_text.split('\n')
        
        for line in lines:
            # Match patterns like "1. Josh Allen (QB) - BUF - 287.4 FP"
            match = re.match(r'(\d+)\.\s*([^(]+)\s*\(([^)]+)\)\s*-\s*([^-]+)\s*-\s*(.+)', line.strip())
            if match and len(players) < limit:
                rank, name, position, team, stats = match.groups()
                players.append({
                    'rank': int(rank),
                    'player_name': name.strip(),
                    'position': position.strip(),
                    'team': team.strip(),
                    'stats_summary': stats.strip()
                })
        
        return players
    
    async def transform_player_rankings(self, doc: Dict) -> List[Dict]:
        """Transform player ranking documents into multiple advice types"""
        
        response_text = doc.get('response', '')
        metadata = doc.get('metadata', {})
        
        # Extract top players
        top_players = self.extract_top_players_from_response(response_text, limit=5)
        
        transformed_docs = []
        
        if top_players:
            # 1. Create start/sit advice for top players
            for player in top_players[:3]:  # Top 3 players
                prompt = self.create_expert_prompt(player, "start_sit")
                expert_response = await self.call_claude_api(prompt)
                
                start_sit_doc = {
                    "prompt": f"Should I start {player['player_name']} ({player['position']}) this week?",
                    "response": expert_response,
                    "context": f"Start/sit analysis for {player['player_name']} based on current performance and rankings",
                    "category": "start_sit_advice",
                    "difficulty_level": "intermediate",
                    "source_type": "ai_expert_advice",
                    "metadata": {
                        "original_doc_id": str(doc.get('_id')),
                        "player_name": player['player_name'],
                        "position": player['position'],
                        "team": player['team'],
                        "rank": player['rank'],
                        "advice_type": "start_sit",
                        "ai_model": "claude-sonnet-4",
                        "transformed_at": datetime.utcnow().isoformat()
                    },
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "is_active": True
                }
                transformed_docs.append(start_sit_doc)
            
            # 2. Create general position advice
            position_data = {
                "position": metadata.get('position', 'players'),
                "scoring_type": metadata.get('ppr_label', 'PPR'),
                "top_players": top_players[:5],
                "total_analyzed": len(top_players)
            }
            
            prompt = self.create_expert_prompt(position_data, "player_rankings")
            expert_response = await self.call_claude_api(prompt)
            
            rankings_doc = {
                "prompt": f"Who should I target at {position_data['position']} in {position_data['scoring_type']} fantasy leagues?",
                "response": expert_response,
                "context": f"Fantasy {position_data['position']} rankings and draft strategy for {position_data['scoring_type']} leagues",
                "category": "draft_strategy",
                "difficulty_level": "intermediate",
                "source_type": "ai_expert_advice",
                "metadata": {
                    "original_doc_id": str(doc.get('_id')),
                    "position": position_data['position'],
                    "scoring_type": position_data['scoring_type'],
                    "advice_type": "player_rankings",
                    "ai_model": "claude-sonnet-4",
                    "transformed_at": datetime.utcnow().isoformat()
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True
            }
            transformed_docs.append(rankings_doc)
        
        return transformed_docs
    
    async def transform_player_news(self, doc: Dict) -> List[Dict]:
        """Transform player news into fantasy impact analysis"""
        
        metadata = doc.get('metadata', {})
        response_text = doc.get('response', '')
        
        player_data = {
            "player_name": metadata.get('player_name', 'Unknown Player'),
            "position": metadata.get('position', 'Unknown'),
            "team": metadata.get('team', 'Unknown'),
            "news_summary": response_text[:500],
            "news_source": metadata.get('news_source', 'ESPN')
        }
        
        # Create fantasy impact analysis
        prompt = self.create_expert_prompt(player_data, "trade_analysis")
        expert_response = await self.call_claude_api(prompt)
        
        news_doc = {
            "prompt": f"How does the latest news affect {player_data['player_name']}'s fantasy value?",
            "response": expert_response,
            "context": f"Fantasy impact analysis of recent news about {player_data['player_name']}",
            "category": "news_analysis",
            "difficulty_level": "intermediate",
            "source_type": "ai_expert_advice",
            "metadata": {
                "original_doc_id": str(doc.get('_id')),
                "player_name": player_data['player_name'],
                "position": player_data['position'],
                "team": player_data['team'],
                "advice_type": "news_impact",
                "ai_model": "claude-sonnet-4",
                "transformed_at": datetime.utcnow().isoformat()
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        return [news_doc]
    
    async def run_transformation(self, limit: int = 5):
        """Run the complete transformation process"""
        
        await self.connect_to_mongo()
        training_collection = self.database.training_data
        
        print(f"Using AI to transform {limit} documents into expert fantasy advice...")
        print("This will create start/sit advice, draft strategy, and news analysis.\n")
        
        # Get documents to transform
        cursor = training_collection.find({
            "source_type": "sleeper_scraper",
            "category": {"$in": ["player_list", "player_news"]}
        }).limit(limit)
        
        docs = await cursor.to_list(length=limit)
        all_transformed_docs = []
        
        for i, doc in enumerate(docs, 1):
            category = doc.get('category', '')
            print(f"Processing document {i}/{len(docs)}: {category}")
            
            try:
                if category == 'player_list':
                    transformed_docs = await self.transform_player_rankings(doc)
                elif category == 'player_news':
                    transformed_docs = await self.transform_player_news(doc)
                else:
                    continue
                
                all_transformed_docs.extend(transformed_docs)
                print(f"   Created {len(transformed_docs)} expert advice documents")
                
                # Show what was created
                for j, tdoc in enumerate(transformed_docs, 1):
                    print(f"      {j}. {tdoc['category']}: {tdoc['prompt'][:50]}...")
                
            except Exception as e:
                print(f"   Error transforming document: {e}")
                continue
            
            # Small delay to be respectful to Claude API
            await asyncio.sleep(1)
        
        # Save all transformed documents
        if all_transformed_docs:
            result = await training_collection.insert_many(all_transformed_docs)
            print(f"\nSuccessfully created {len(result.inserted_ids)} expert advice documents!")
            
            # Show detailed samples
            print("\nSample Expert Advice (AI Generated):")
            print("=" * 70)
            
            for i, doc in enumerate(all_transformed_docs[:2], 1):
                print(f"\n{i}. Category: {doc['category']}")
                print(f"   Prompt: {doc['prompt']}")
                print(f"   Response: {doc['response'][:200]}...")
        else:
            print("No documents were transformed.")
        
        self.client.close()

async def main():
    """Main function"""
    
    print("SportAI Training Data Transformer")
    print("=" * 60)
    print("This will use AI to convert your statistical data into:")
    print("• Expert start/sit recommendations")
    print("• Draft strategy advice")
    print("• News impact analysis")
    print("• Trade value assessments")
    print()
    
    transformer = TrainingDataTransformer()
    await transformer.run_transformation(limit=2)

if __name__ == "__main__":
    asyncio.run(main())