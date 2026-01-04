"""
Sleeper API Client
Pure API client for Sleeper.app endpoints
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime


class SleeperAPI:
    """Pure API client for Sleeper.app"""
    
    def __init__(self):
        self.base_url = "https://api.sleeper.app/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    # ==================== User Endpoints ====================
    
    def get_user(self, username: str = None, user_id: str = None) -> Dict[str, Any]:
        """Get Sleeper user information"""
        if user_id:
            url = f"{self.base_url}/user/{user_id}"
        elif username:
            url = f"{self.base_url}/user/{username}"
        else:
            raise ValueError("Must provide either username or user_id")
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_user_leagues(self, user_id: str, season: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get leagues for a Sleeper user"""
        url = f"{self.base_url}/user/{user_id}/leagues/nfl/{season or ''}"
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        leagues = response.json()
        return leagues if isinstance(leagues, list) else []
    
    # ==================== League Endpoints ====================
    
    def get_league(self, league_id: str) -> Dict[str, Any]:
        """Get Sleeper league information"""
        url = f"{self.base_url}/league/{league_id}"
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_league_rosters(self, league_id: str) -> List[Dict[str, Any]]:
        """Get rosters for a Sleeper league"""
        url = f"{self.base_url}/league/{league_id}/rosters"
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        rosters = response.json()
        return rosters if isinstance(rosters, list) else []
    
    def get_league_matchups(self, league_id: str, week: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get matchups for a Sleeper league"""
        url = f"{self.base_url}/league/{league_id}/matchups/{week or ''}"
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        matchups = response.json()
        return matchups if isinstance(matchups, list) else []
    
    def get_league_transactions(self, league_id: str, round_num: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get transactions for a Sleeper league"""
        url = f"{self.base_url}/league/{league_id}/transactions"
        if round_num:
            url += f"/{round_num}"
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        transactions = response.json()
        return transactions if isinstance(transactions, list) else []
    
    # ==================== Player Endpoints ====================
    
    def get_all_players(self, sport: str = "nfl") -> Dict[str, Any]:
        """Get all players for a sport"""
        url = f"{self.base_url}/players/{sport}"
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_trending_players(
        self, 
        sport: str = "nfl", 
        trend_type: str = "add", 
        lookback_hours: int = 24, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get trending players"""
        url = f"{self.base_url}/players/{sport}/trending/{trend_type}"
        params = {
            "lookback_hours": lookback_hours,
            "limit": limit
        }
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    # ==================== Stats Endpoints ====================
    
    def get_player_stats(
        self,
        sport: str = "nfl",
        season: str = None,
        season_type: str = "regular"
    ) -> Dict[str, Any]:
        """Get player statistics"""
        if season is None:
            season = str(datetime.now().year)
        url = f"{self.base_url}/stats/{sport}/{season_type}/{season}"
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    
    # ==================== Draft Endpoints ====================
    
    def get_draft(self, draft_id: str) -> Dict[str, Any]:
        """Get draft information"""
        url = f"{self.base_url}/draft/{draft_id}"
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()