#!/usr/bin/env python3
"""
Add Fantasy Football Overview Document to Training Data
Adds foundational knowledge about traditional fantasy vs DFS
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from pathlib import Path

# Load environment variables from root .env file
try:
    from dotenv import load_dotenv
    root_dir = Path(__file__).parent.parent
    env_file = root_dir / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded .env from: {env_file}")
    else:
        print(f"Warning: .env file not found at {env_file}")
except ImportError:
    print("Warning: python-dotenv not installed")

async def add_fantasy_overview():
    """Add fantasy football overview document to training data"""
    
    # Get MongoDB connection
    mongodb_url = os.getenv('MONGODB_ATLAS_URL') or os.getenv('MONGODB_URL')
    database_name = os.getenv('DATABASE_NAME', 'sportai_documents')
    
    if not mongodb_url:
        raise ValueError("MongoDB URL not found in environment variables")
    
    client = AsyncIOMotorClient(mongodb_url)
    database = client[database_name]
    training_collection = database.training_data
    
    # Fantasy football overview content
    overview_content = """
Overview

Traditional fantasy originated as mail-in or paper-based leagues. As such, they mimic the season-based structure of actual sports leagues. Team managers draft players prior to the commencement of the season, and must utilize the leagues transaction structure (trades, waivers, etc.) to alter their original lineups. Such leagues are still popular on the internet today, most casual fantasy players are in these kinds of leagues. Well-known platforms include ESPN, Yahoo and CBS.

Conversely, DFS emerged as a product of the application-era, allowing participants to allocate a budget among players to build their lineup. Such lineups can be entered in contests which are tied to one slate of games, or an event (NFL Sunday, a night of NBA games, a golf tournament). The experience provides a seamless mix of small-stakes sports betting and traditional fantasy rulesets. Therefore, DFS has skyrocketed in popularity after its emergence-- some analysts predict it to be a 1.5 billion dollar industry by 2024.

Decision-Making in DFS vs. Traditional Fantasy

Clearly, in traditional fantasy leagues, drafts represent a large portion of the important decisions a player makes in a given year. However, that has little relevance to our product as currently envisioned. For traditional fantasy players, leagues are won and lost on transactions and start/sit decisions. Alternatively, successful DFS players garner the highest rate of returns across all positions. Therefore, it is common to quantify a players scoring total per dollar spent.

DFS Tournaments vs. H2H

DFS competitions can be generalized into the above two categories. Tournaments, especially in the lower stakes, attract large fields. Depending on the structure of the tournament, there may be a cap on entries per person. Unless the tournament is a freeroll, there is an entry fee per lineup entered, which are pooled together to payout the top finishers. Therefore, the accepted approach to tournament play is to maximize your lineup's ceiling.

Meanwhile, the H2H format is self-explanatory. In these games, players are simply trying to maximize their lineups returns to budget. Hypothetically, to do so is to find the highest 'pts/$k' for each position, constrained by budget.

Scoring Systems

BASKETBALL & FOOTBALL: Scoring & Rulesets Vary

Popular platforms include:
- FanDuel: Different scoring systems for NBA and NFL
- DraftKings: Various game types with different rules
- ESPN: Customizable scoring with standard and PPR options

NOTE: Many user-made leagues use customized scoring. Often alterations are minimal, and fantasy-adjacent sites use "standard scoring" OR "PPR standard scoring" for quantifications-- hence these rulesets are the accepted vernacular in inter-league forums. PPR stands for points per reception and represents a general category of rulesets. Regardless of the underlying specifics, play in these types of leagues are distinct, and most fantasy content differentiates recommendations between PPR and standard leagues. Speaking from observation, PPR is about as popular as standard scoring.

Key Concepts for Fantasy Advice:
- Traditional Fantasy: Focus on season-long value, trades, waiver wire, start/sit decisions
- DFS: Focus on value per dollar, ceiling plays for tournaments, floor plays for H2H
- PPR vs Standard: Different player values based on reception scoring
- Tournament Strategy: High ceiling, contrarian plays, leverage
- Cash Game Strategy: High floor, safe plays, consistent scoring
"""

    # Create training document
    training_doc = {
        "prompt": "What's the difference between traditional fantasy football and DFS? How should strategy differ?",
        "response": overview_content.strip(),
        "context": "Foundational knowledge about fantasy football formats, scoring systems, and strategic differences",
        "category": "fantasy_fundamentals",
        "difficulty_level": "intermediate",
        "source_type": "educational_content",
        "metadata": {
            "content_type": "overview",
            "topics": ["traditional_fantasy", "dfs", "scoring_systems", "strategy", "ppr", "tournaments"],
            "importance": "high",
            "created_by": "manual_addition",
            "added_at": datetime.utcnow().isoformat()
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }
    
    # Insert the document
    result = await training_collection.insert_one(training_doc)
    
    print("Fantasy Football Overview Added Successfully!")
    print(f"Document ID: {result.inserted_id}")
    print(f"Category: {training_doc['category']}")
    print(f"Topics covered: {', '.join(training_doc['metadata']['topics'])}")
    
    # Also add some specific Q&A pairs based on this content
    qa_pairs = [
        {
            "prompt": "What's the difference between traditional fantasy and DFS?",
            "response": "Traditional fantasy mimics season-long sports leagues where you draft players before the season and manage through trades and waivers. DFS (Daily Fantasy Sports) lets you build lineups with a salary budget for specific game slates. Traditional fantasy focuses on season-long value and start/sit decisions, while DFS emphasizes value per dollar and maximizing returns within budget constraints.",
            "category": "fantasy_fundamentals"
        },
        {
            "prompt": "What's the difference between PPR and standard scoring?",
            "response": "PPR stands for 'Points Per Reception' - players get points for each catch they make. In standard scoring, players only get points for yards and touchdowns, not catches. This makes pass-catching running backs and slot receivers much more valuable in PPR leagues. Most fantasy content differentiates between PPR and standard because player values change significantly between the two formats.",
            "category": "scoring_systems"
        },
        {
            "prompt": "How should my strategy differ between DFS tournaments and cash games?",
            "response": "In DFS tournaments, focus on maximizing your lineup's ceiling with high-upside, contrarian plays since you need to finish in the top percentages of a large field. In cash games (H2H, 50/50s), prioritize high floor players and consistent scoring since you only need to beat 50% of the field. Tournament strategy accepts more risk for higher reward, while cash game strategy emphasizes safety and reliability.",
            "category": "dfs_strategy"
        }
    ]
    
    # Add the Q&A pairs
    for i, qa in enumerate(qa_pairs, 1):
        qa_doc = {
            "prompt": qa["prompt"],
            "response": qa["response"],
            "context": f"Fantasy football fundamentals Q&A - {qa['category']}",
            "category": qa["category"],
            "difficulty_level": "beginner",
            "source_type": "educational_qa",
            "metadata": {
                "content_type": "qa_pair",
                "parent_overview": str(result.inserted_id),
                "qa_number": i,
                "added_at": datetime.utcnow().isoformat()
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        qa_result = await training_collection.insert_one(qa_doc)
        print(f"Added Q&A {i}: {qa['prompt'][:50]}...")
    
    client.close()
    print(f"\nTotal documents added: {len(qa_pairs) + 1}")
    print("Your LLM now has foundational fantasy football knowledge!")

if __name__ == "__main__":
    asyncio.run(add_fantasy_overview())