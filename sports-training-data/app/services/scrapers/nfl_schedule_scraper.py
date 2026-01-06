"""
NFL Schedule Scraper
Scrapes NFL schedule/matchup data

API Used: ESPN API
Data Source: ESPN NFL API endpoints
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from ..apis.espn_api import ESPNAPI
from .base_scraper import BaseScraper


class NFLScheduleScraper(BaseScraper):
    """Scraper for NFL schedule data using ESPN API"""
    
    def __init__(self):
        super().__init__()
        self.espn_api = ESPNAPI()
    
    def get_schedule(
        self,
        season: str = None,
        season_type: str = "regular",
        week: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get NFL schedule/matchups
        
        Args:
            season: Season year (default: current year)
            season_type: Season type - 'regular', 'pre', 'post' (default: 'regular')
            week: Optional week number (default: None = all weeks)
            
        Returns:
            List of game dictionaries
        """
        if season is None:
            season = str(datetime.now().year)
        
        # Convert season type to ESPN format
        espn_season_type = {
            "pre": 1,
            "regular": 2,
            "post": 3
        }.get(season_type.lower(), 2)
        
        try:
            if week:
                # Get specific week
                games = self._get_week_schedule(season, espn_season_type, week)
            else:
                # Get all games for the season
                games = self.espn_api.get_schedule(season, espn_season_type)
            
            # Parse and format games
            formatted_games = []
            for game in games:
                parsed_game = self._parse_espn_game(game, season, season_type, week)
                if parsed_game:
                    formatted_games.append(parsed_game)
            
            return formatted_games
        except Exception as e:
            raise Exception(f"Failed to get NFL schedule: {str(e)}")
    
    def _get_week_schedule(self, season: str, season_type: int, week: int) -> List[Dict[str, Any]]:
        """Get schedule for a specific week"""
        from datetime import timedelta
        
        # Calculate approximate date for the week
        if season_type == 2:  # Regular season
            start_date = datetime(int(season), 9, 1)
            target_date = start_date + timedelta(weeks=week-1)
        elif season_type == 1:  # Preseason
            start_date = datetime(int(season), 8, 1)
            target_date = start_date + timedelta(weeks=week-1)
        else:  # Playoffs
            start_date = datetime(int(season) + 1, 1, 1)
            target_date = start_date + timedelta(weeks=week-1)
        
        # Try a few days around the target date
        games = []
        for day_offset in range(-3, 4):
            from datetime import timedelta
            test_date = target_date + timedelta(days=day_offset)
            date_str = test_date.strftime('%Y%m%d')
            
            try:
                scoreboard = self.espn_api.get_scoreboard(date_str, season_type)
                if 'events' in scoreboard and scoreboard['events']:
                    games.extend(scoreboard['events'])
            except Exception:
                continue
        
        return games
    
    def _parse_espn_game(
        self,
        game: Dict[str, Any],
        season: str,
        season_type: str,
        week: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """Parse ESPN game data into our format"""
        try:
            # Extract basic info
            game_id = game.get('id', '')
            date_str = game.get('date', '')
            
            # Extract teams and scores
            away_team = None
            home_team = None
            away_score = None
            home_score = None
            
            if 'competitions' in game and game['competitions']:
                competition = game['competitions'][0]
                
                if 'competitors' in competition:
                    for competitor in competition['competitors']:
                        team = competitor.get('team', {})
                        abbreviation = team.get('abbreviation', '')
                        score = competitor.get('score')
                        is_home = competitor.get('homeAway') == 'home'
                        
                        if is_home:
                            home_team = abbreviation
                            home_score = int(score) if score else None
                        else:
                            away_team = abbreviation
                            away_score = int(score) if score else None
            
            if not (away_team and home_team):
                return None
            
            parsed_game = {
                'game_id': game_id,
                'season': season,
                'season_type': season_type,
                'week': week,
                'away_team': away_team,
                'home_team': home_team,
                'date': date_str,
                'source': 'espn_api'
            }
            
            # Add scores if available
            if away_score is not None and home_score is not None:
                parsed_game['away_score'] = away_score
                parsed_game['home_score'] = home_score
                parsed_game['completed'] = True
            else:
                parsed_game['completed'] = False
            
            return parsed_game
        except Exception:
            return None