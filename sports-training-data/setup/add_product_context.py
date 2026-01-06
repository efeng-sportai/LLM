#!/usr/bin/env python3
"""
Add SportAI Product Context to Training Data
Adds product vision, user personas, and conversational flows
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

async def add_product_context():
    """Add SportAI product context and user personas to training data"""
    
    # Get MongoDB connection
    mongodb_url = os.getenv('MONGODB_ATLAS_URL') or os.getenv('MONGODB_URL')
    database_name = os.getenv('DATABASE_NAME', 'sportai_documents')
    
    if not mongodb_url:
        raise ValueError("MongoDB URL not found in environment variables")
    
    client = AsyncIOMotorClient(mongodb_url)
    database = client[database_name]
    training_collection = database.training_data
    
    # Product vision and strategy
    product_vision = """
SportAI Product Vision & Strategy

Vision: To transition SportAI from a static "lineup tool" to a dynamic, conversational "fantasy analyst."

Mission: Become the indispensable, proactive, and trusted co-manager for fantasy sports players, leveraging SportAI's advanced reasoning to deliver actionable insights that win leagues.

Core Pillars:
1. Personalized Reasoning (RAG): Deliver conversational experience grounded in real-time user context (roster, league rules) and high-velocity data (news, stats)
2. Performance & Trust: Lightning-fast response time (sub-4 second P95) for 15,000+ concurrent users
3. Ubiquitous Delivery: Launch across iOS, Android, and Web platforms

Core User Personas:

The Casual Manager:
- Overwhelmed by data
- Needs quick, trusted "who do I start?" answers
- Wants simple recommendations with brief justification
- Prefers static/if-then tools available in chat

The Power User:
- Data-savvy fantasy player
- Needs a "sparring partner" to validate/challenge theses
- Seeks deep-slate DFS value and complex trade-off analysis
- Wants conversational/dynamic LLM responses with detailed reasoning

Response Strategy by Persona:
- Casual Manager: Provide definitive recommendations with 1-2 sentence justifications
- Power User: Offer detailed analysis, stat breakdowns, and strategic reasoning
"""

    # Conversational flows and examples
    conversational_flows = """
SportAI Conversational Flow Examples

Flow 1: The "Start/Sit" Dilemma (Core Loop)
User: "Should I start Chris Olave or George Pickens in my flex?"
SportAI Response Strategy:
- Check user's league context (PPR, scoring rules)
- Analyze matchups and recent performance
- Provide clear recommendation with reasoning
- Offer follow-up stat details if requested

Example Response: "I'd start Chris Olave. His target volume (9.5/game) gives him a safer floor, even against a tough ATL secondary. Pickens is more boom/bust with the weather concerns in Pittsburgh. Want to see the full stat breakdown?"

Flow 2: The "Waiver Wire" Hunt
User: "I need a streaming QB, who is available?"
SportAI Response Strategy:
- Consider user's league waiver wire availability
- Rank available options by matchup and upside
- Provide clear recommendation with reasoning

Example Response: "Looking at available QBs... Baker Mayfield (vs. CAR) has the safer floor against a weak Panthers defense. Jordan Love (vs. NYG) has higher upside but has been inconsistent. I recommend streaming Mayfield for reliability."

Flow 3: The "DFS" Builder
User: "Build me a high-upside GPP lineup for DraftKings main slate."
SportAI Response Strategy:
- Focus on tournament strategy (ceiling over floor)
- Identify low-owned stacks and contrarian plays
- Explain game theory and leverage concepts
- Provide full lineup with detailed rationale

Key Response Principles:
1. Always ground recommendations in data
2. Explain the "why" behind advice
3. Maintain conversation context for follow-ups
4. Adapt complexity to user persona (Casual vs Power)
5. Include disclaimers about verifying information
"""

    # User stories and requirements
    user_requirements = """
SportAI Core Product Requirements

P0 Requirements (MVP):
1. Conversational Query: Users can ask natural language questions and receive data-driven recommendations
2. Fantasy Platform Integration: Secure connection to ESPN, Yahoo, Sleeper for roster and league context
3. Grounded Rationale: Show key data points used in recommendations (RAG output)

P1 Requirements:
4. Multi-Turn Context: Understand follow-up questions in conversation context
5. Waiver/Trade Analysis: Analyze waiver wire and trades based on specific roster needs

P2 Requirements:
6. Proactive Insights: Notifications for significant events affecting user's lineup

User Story Examples:
- "As a Casual Manager, I can ask a simple start/sit question and get a definitive recommendation with 1-2 sentence justification"
- "As a Power User, I can ask for detailed stats or matchup analysis"
- "As a user, I can see disclaimers on all AI-generated content"
- "As a user, follow-up questions maintain conversation context"

Response Guidelines:
- Provide clear, actionable advice
- Include brief rationale for recommendations
- Offer deeper analysis when requested
- Maintain conversation context across turns
- Always include appropriate disclaimers
"""

    # Create training documents
    documents = [
        {
            "prompt": "What is SportAI's product vision and strategy?",
            "response": product_vision.strip(),
            "category": "product_vision",
            "topics": ["vision", "strategy", "personas", "pillars"]
        },
        {
            "prompt": "How should SportAI respond to different types of users?",
            "response": conversational_flows.strip(),
            "category": "conversational_flows",
            "topics": ["user_flows", "response_strategy", "examples"]
        },
        {
            "prompt": "What are SportAI's core product requirements and user stories?",
            "response": user_requirements.strip(),
            "category": "product_requirements",
            "topics": ["requirements", "user_stories", "guidelines"]
        }
    ]
    
    inserted_ids = []
    
    for doc_data in documents:
        training_doc = {
            "prompt": doc_data["prompt"],
            "response": doc_data["response"],
            "context": f"SportAI product context - {doc_data['category']}",
            "category": doc_data["category"],
            "difficulty_level": "intermediate",
            "source_type": "product_documentation",
            "metadata": {
                "content_type": "product_context",
                "topics": doc_data["topics"],
                "importance": "critical",
                "created_by": "product_team",
                "added_at": datetime.utcnow().isoformat()
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = await training_collection.insert_one(training_doc)
        inserted_ids.append(result.inserted_id)
        print(f"Added: {doc_data['category']} - {doc_data['prompt'][:50]}...")
    
    # Add specific persona-based Q&A pairs
    persona_qa = [
        {
            "prompt": "I'm overwhelmed by all the fantasy data. Can you just tell me who to start?",
            "response": "Absolutely! I'm here to cut through the noise and give you clear, simple recommendations. Just tell me which players you're deciding between, and I'll give you a definitive answer with a quick explanation. No need to dig through stats - that's what I'm here for.",
            "persona": "casual_manager",
            "category": "persona_response"
        },
        {
            "prompt": "I want to challenge my DFS lineup theory. Can you analyze my contrarian stack idea?",
            "response": "I love being a sparring partner for advanced strategy! Share your stack idea and I'll break down the game theory, ownership projections, and leverage potential. We can dive deep into the matchup data, weather factors, and tournament dynamics to validate or refine your approach.",
            "persona": "power_user", 
            "category": "persona_response"
        },
        {
            "prompt": "How should SportAI adapt its responses to different user types?",
            "response": "SportAI adapts to two core personas: Casual Managers get quick, definitive recommendations with 1-2 sentence justifications - they want simple answers to 'who do I start?' Power Users get detailed analysis, stat breakdowns, and strategic reasoning - they want a sparring partner for complex decisions. The key is recognizing user intent and adjusting complexity accordingly.",
            "persona": "system_knowledge",
            "category": "response_strategy"
        }
    ]
    
    for qa in persona_qa:
        qa_doc = {
            "prompt": qa["prompt"],
            "response": qa["response"],
            "context": f"SportAI persona-based response - {qa['persona']}",
            "category": qa["category"],
            "difficulty_level": "intermediate",
            "source_type": "persona_training",
            "metadata": {
                "content_type": "persona_qa",
                "persona": qa["persona"],
                "response_type": "adaptive",
                "added_at": datetime.utcnow().isoformat()
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = await training_collection.insert_one(qa_doc)
        inserted_ids.append(result.inserted_id)
        print(f"Added persona Q&A: {qa['persona']} - {qa['prompt'][:40]}...")
    
    client.close()
    
    print(f"\nProduct Context Added Successfully!")
    print(f"Total documents added: {len(inserted_ids)}")
    print("Categories added:")
    print("- Product Vision & Strategy")
    print("- Conversational Flows & Examples") 
    print("- Product Requirements & User Stories")
    print("- Persona-Based Response Training")
    print("\nYour LLM now understands SportAI's product vision and user personas!")

if __name__ == "__main__":
    asyncio.run(add_product_context())