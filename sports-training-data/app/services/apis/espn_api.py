"""
ESPN API Client
Pure API client for ESPN endpoints
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class ESPNAPI:
    """Pure API client for ESPN"""
    
    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    # ==================== Schedule/Scoreboard Endpoints ====================
    
    def get_scoreboard(self, date: str = None, season_type: int = 2) -> Dict[str, Any]:
        """
        Get NFL scoreboard for a specific date
        
        Args:
            date: Date in YYYYMMDD format (optional)
            season_type: 1=preseason, 2=regular, 3=playoffs
        """
        url = f"{self.base_url}/scoreboard"
        params = {}
        
        if date:
            params['dates'] = date
        if season_type:
            params['seasontype'] = str(season_type)
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_schedule(self, season: str = None, season_type: int = 2) -> List[Dict[str, Any]]:
        """
        Get NFL schedule for a season
        
        Args:
            season: Season year (e.g., '2024')
            season_type: 1=preseason, 2=regular, 3=playoffs
        """
        if season is None:
            season = str(datetime.now().year)
        
        # Calculate date range for the season
        if season_type == 2:  # Regular season
            start_date = datetime(int(season), 9, 1)
            end_date = datetime(int(season) + 1, 1, 31)
        elif season_type == 1:  # Preseason
            start_date = datetime(int(season), 8, 1)
            end_date = datetime(int(season), 8, 31)
        else:  # Playoffs
            start_date = datetime(int(season) + 1, 1, 1)
            end_date = datetime(int(season) + 1, 2, 28)
        
        all_games = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                date_str = current_date.strftime('%Y%m%d')
                scoreboard = self.get_scoreboard(date_str, season_type)
                
                if 'events' in scoreboard:
                    all_games.extend(scoreboard['events'])
                
                current_date += timedelta(days=7)  # Check weekly
            except Exception:
                current_date += timedelta(days=7)
                continue
        
        return all_games
    
    # ==================== Teams Endpoints ====================
    
    def get_teams(self) -> Dict[str, Any]:
        """Get NFL teams"""
        url = f"{self.base_url}/teams"
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_team(self, team_id: str) -> Dict[str, Any]:
        """Get specific NFL team"""
        url = f"{self.base_url}/teams/{team_id}"
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    
    # ==================== Standings Endpoints ====================
    
    def get_standings(self, season: str = None) -> Dict[str, Any]:
        """Get NFL standings"""
        url = f"{self.base_url}/standings"
        params = {}
        
        if season:
            params['season'] = season
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    # ==================== News Endpoints ====================
    
    def get_news(self, limit: int = 50) -> Dict[str, Any]:
        """Get NFL news"""
        url = f"{self.base_url}/news"
        params = {'limit': limit}
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()