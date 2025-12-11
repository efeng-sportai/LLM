"""
NFL Schedule Scraper
Fetches NFL schedule from ESPN API and web scraping fallbacks
"""

import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

# Get current year as default
CURRENT_YEAR = str(datetime.now().year)


class NFLScheduleScraper(BaseScraper):
    """Scraper for NFL schedule from ESPN API and web sources"""
    
    def get_nfl_schedule(
        self,
        season: str = None,
        season_type: str = "regular",
        week: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get NFL schedule/matchups from ESPN API (most reliable source)
        
        Args:
            season: Season year (default: current year)
            season_type: Season type - 'regular', 'pre', 'post' (default: 'regular')
            week: Optional week number (default: None = all weeks)
            
        Returns:
            List of game dictionaries with teams, date, time, etc.
        """
        if season is None:
            season = CURRENT_YEAR
        games = []
        
        # Method 1: Try ESPN API (most reliable)
        try:
            # ESPN uses season type: 1 = preseason, 2 = regular, 3 = playoffs
            espn_season_type = {
                "pre": 1,
                "regular": 2,
                "post": 3
            }.get(season_type.lower(), 2)
            
            # Calculate dates for the season
            # For simplicity, we'll fetch by weeks
            if week:
                # Fetch specific week
                games = self._get_espn_schedule_week(season, espn_season_type, week)
            else:
                # Fetch all weeks for the season
                all_games = []
                # Regular season has 18 weeks, preseason has 3, playoffs have 4
                max_weeks = 18 if season_type == "regular" else (3 if season_type == "pre" else 4)
                
                for w in range(1, max_weeks + 1):
                    week_games = self._get_espn_schedule_week(season, espn_season_type, w)
                    all_games.extend(week_games)
                
                games = all_games
            
            if games:
                return games
        except Exception as e:
            # If ESPN fails, try fallback methods
            pass
        
        # Method 2: Fallback to NFL.com __NEXT_DATA__ parsing
        try:
            nfl_games = self._get_nfl_schedule_from_web(season, season_type, week)
            if nfl_games:
                return nfl_games
        except Exception as e:
            pass
        
        # If all methods fail, return empty list
        return []
    
    def _get_espn_schedule_week(
        self,
        season: str,
        season_type: int,
        week: int
    ) -> List[Dict[str, Any]]:
        """
        Get NFL schedule for a specific week from ESPN API
        """
        # ESPN API endpoint for NFL scoreboard
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        
        # Calculate dates for the week
        # Week 1 of regular season 2025 starts around September
        # For simplicity, we'll fetch the week by trying multiple dates
        games = []
        
        # Try multiple dates around the expected week
        # Regular season weeks: Sep-Dec
        if season_type == 2:  # Regular season
            # Start date approximately in September
            start_date = datetime(int(season), 9, 1)
            # Add weeks to get to the requested week
            target_date = start_date + timedelta(weeks=week-1)
        elif season_type == 1:  # Preseason
            # Preseason starts in August
            start_date = datetime(int(season), 8, 1)
            target_date = start_date + timedelta(weeks=week-1)
        else:  # Playoffs
            # Playoffs start in January
            start_date = datetime(int(season) + 1, 1, 1)
            target_date = start_date + timedelta(weeks=week-1)
        
        # Try the target date and a few days around it
        for day_offset in range(-2, 3):
            test_date = target_date + timedelta(days=day_offset)
            date_str = test_date.strftime('%Y%m%d')
            
            params = {
                'dates': date_str,
                'seasontype': str(season_type)
            }
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'events' in data and data['events']:
                    for event in data['events']:
                        game = self._parse_espn_event(event, season, season_type, week)
                        if game and game not in games:
                            games.append(game)
                
                # If we found games, we can stop trying other dates
                if games:
                    break
            except Exception as e:
                continue
        
        return games
    
    def _parse_espn_event(
        self,
        event: Dict[str, Any],
        season: str,
        season_type: int,
        week: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Parse an ESPN event into our game format
        """
        try:
            # Extract date
            date_str = event.get('date', '')
            
            # Extract teams
            away_team = None
            home_team = None
            away_score = None
            home_score = None
            
            if 'competitions' in event and event['competitions']:
                competition = event['competitions'][0]
                
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
            
            if away_team and home_team:
                game = {
                    'season': season,
                    'season_type': 'regular' if season_type == 2 else ('pre' if season_type == 1 else 'post'),
                    'week': week,
                    'away_team': away_team,
                    'home_team': home_team,
                    'date': date_str,
                    'source': 'espn'
                }
                
                if away_score is not None and home_score is not None:
                    game['away_score'] = away_score
                    game['home_score'] = home_score
                
                return game
        except Exception as e:
            pass
        
        return None
    
    def _get_nfl_schedule_from_web(
        self,
        season: str,
        season_type: str,
        week: Optional[int]
    ) -> List[Dict[str, Any]]:
        """
        Fallback method: Parse NFL.com schedule from web scraping
        """
        # NFL.com schedule URL
        base_url = f"https://www.nfl.com/schedules/{season}"
        if season_type == "regular":
            url = f"{base_url}/REG{week}" if week else f"{base_url}/REG"
        elif season_type == "pre":
            url = f"{base_url}/PRE{week}" if week else f"{base_url}/PRE"
        elif season_type == "post":
            url = f"{base_url}/POST{week}" if week else f"{base_url}/POST"
        else:
            url = base_url
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            html = response.text
            
            games = []
            
            # Try to extract __NEXT_DATA__
            next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
            if next_data_match:
                try:
                    data = json.loads(next_data_match.group(1))
                    # Recursively search for schedule data
                    games_data = self._extract_games_from_json(data)
                    if games_data:
                        games.extend(games_data)
                except:
                    pass
            
            return games
        except Exception as e:
            return []
    
    def _extract_games_from_json(self, data: Any, depth: int = 0) -> List[Dict[str, Any]]:
        """Recursively extract game data from JSON structure"""
        if depth > 5:  # Limit recursion depth
            return []
        
        games = []
        
        if isinstance(data, dict):
            # Check if this dict looks like a game
            if 'away_team' in data or 'home_team' in data or ('team' in data and isinstance(data.get('team'), dict)):
                games.append(data)
            # Recurse into nested structures
            for value in data.values():
                games.extend(self._extract_games_from_json(value, depth + 1))
        elif isinstance(data, list):
            for item in data:
                games.extend(self._extract_games_from_json(item, depth + 1))
        
        return games

