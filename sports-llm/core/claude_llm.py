#!/usr/bin/env python3
"""
Claude LLM - Lightweight Fantasy Football AI
Fast, high-quality responses using Claude API with persona detection
"""

import aiohttp
import json
import os
from typing import Optional, Dict, Any
from pathlib import Path

class ClaudeLLM:
    """Fantasy Football AI using Claude API with automatic persona detection"""
    
    def __init__(self):
        # Load environment variables from root .env file
        try:
            from dotenv import load_dotenv
            # Look for .env in the project root (two levels up from this file)
            root_dir = Path(__file__).parent.parent.parent
            env_file = root_dir / '.env'
            if env_file.exists():
                load_dotenv(env_file)
                print(f"Loaded .env from: {env_file}")
            else:
                print(f"Warning: .env file not found at {env_file}")
        except ImportError:
            print("Warning: python-dotenv not installed")
        
        self.claude_api_key = os.getenv('CLAUDE_API_KEY')
        if not self.claude_api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")
        
        self.claude_url = "https://api.anthropic.com/v1/messages"
        self.user_query = None
    
    async def call_claude_api(self, prompt: str, max_tokens: int = 500) -> str:
        """Call Claude API with the given prompt"""
        
        headers = {
            "x-api-key": self.claude_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": "claude-sonnet-4-20250514",  # Using working model from context
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
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
                        return self.fallback_response()
        except Exception as e:
            print(f"Claude API request failed: {e}")
            return self.fallback_response()
    
    def fallback_response(self) -> str:
        """Fallback response when Claude API fails"""
        return "I'm having trouble accessing the latest data right now. Please try again in a moment, or check back later for updated fantasy advice."
    
    def create_fantasy_prompt(self, user_query: str, context: str) -> str:
        """Create a specialized prompt for fantasy football advice"""
        
        return f"""You are a top fantasy football expert like Matthew Berry. You provide actionable, conversational fantasy advice to help users make lineup decisions.

CONTEXT (Recent Data):
{context}

USER QUESTION: {user_query}

INSTRUCTIONS:
- Give direct, actionable fantasy advice (no emojis)
- Use fantasy terminology (start/sit, RB1/WR2, PPR, waiver wire, etc.)
- Be conversational but confident
- Include specific reasoning based on the context data
- Keep response focused and helpful (2-4 sentences)
- If the context doesn't have relevant info, give general fantasy advice principles

RESPONSE:"""
    
    def detect_user_persona(self, user_query: str) -> str:
        """Detect user persona based on question style"""
        
        query_lower = user_query.lower()
        
        # Newbie indicators
        if any(phrase in query_lower for phrase in [
            "what is", "what does", "how do i", "i'm new", "don't know", "explain", "help me understand"
        ]):
            return "newbie"
        
        # Professional indicators  
        elif any(phrase in query_lower for phrase in [
            "advanced", "edge", "contrarian", "ownership", "leverage", "game theory", "stack"
        ]):
            return "professional"
        
        # Dabbler indicators
        elif any(phrase in query_lower for phrase in [
            "data shows", "trends", "analytics", "stats", "numbers", "optimize"
        ]):
            return "dabbler"
        
        # Default to rookie
        else:
            return "rookie"
    
    def create_persona_prompt(self, user_query: str, context: str, persona: str) -> str:
        """Create persona-specific prompts"""
        
        base_context = f"""You are a fantasy football expert. Adjust your response style for this user type.

CONTEXT (Recent Data):
{context}

USER QUESTION: {user_query}

"""
        
        if persona == "newbie":
            return base_context + """USER TYPE: Complete beginner to fantasy football

RESPONSE STYLE:
- Explain fantasy terms simply
- Use encouraging, friendly tone (no emojis)
- Avoid complex stats
- Give step-by-step guidance
- Build confidence

RESPONSE:"""
        
        elif persona == "rookie":
            return base_context + """USER TYPE: Casual player who wants to impress friends

RESPONSE STYLE:
- Give confident, straightforward advice (no emojis)
- Include simple reasoning they can repeat
- Help them sound knowledgeable
- Focus on clear start/sit decisions

RESPONSE:"""
        
        elif persona == "dabbler":
            return base_context + """USER TYPE: Stats-savvy player who wants data-driven analysis

RESPONSE STYLE:
- Include specific statistics and trends (no emojis)
- Reference analytical concepts
- Mention historical performance
- Give data-backed reasoning

RESPONSE:"""
        
        elif persona == "professional":
            return base_context + """USER TYPE: Serious player who wants advanced strategy

RESPONSE STYLE:
- Discuss advanced metrics and game theory (no emojis)
- Mention contrarian plays and leverage
- Reference ownership percentages
- Give sophisticated analysis

RESPONSE:"""
        
        else:
            return self.create_fantasy_prompt(user_query, context)
    
    async def generate_text(self, context: str, max_length: int = 500, use_persona: bool = True) -> str:
        """Generate fantasy advice using Claude API"""
        
        if not self.user_query:
            return "No question provided"
        
        # Detect persona and create appropriate prompt
        if use_persona:
            persona = self.detect_user_persona(self.user_query)
            prompt = self.create_persona_prompt(self.user_query, context, persona)
        else:
            prompt = self.create_fantasy_prompt(self.user_query, context)
        
        # Call Claude API
        response = await self.call_claude_api(prompt, max_tokens=max_length)
        
        return response
    
    # Legacy compatibility methods (no longer needed)
    def load_pretrained_model(self):
        """Legacy method - Claude API doesn't require model loading"""
        pass
    
    def preprocess_input(self, input_text):
        """Legacy method - Claude handles preprocessing"""
        pass
    
    def fine_tuning(self, train_set, val_set, batch_size: int, epochs: int, learning_rate: float):
        """Legacy method - Claude doesn't need fine-tuning"""
        pass

# Main export
LLM = ClaudeLLM