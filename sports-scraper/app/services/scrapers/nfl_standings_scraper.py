"""
NFL Standings Scraper
Scrapes NFL team standings and records

API Used: Sleeper API (web scraping fallback)
Data Source: Sleeper.com standings pages
"""

import re
import json
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class NFLStandingsScraper(BaseScraper):
    """Scraper for NFL standings data"""
    
    def __init__(self):
        super().__init__()
    
    def get_standings(
        self,
        season: str = None,
        season_type: str = "regular",
        grouping: str = "league"
    ) -> List[Dict[str, Any]]:
        """
        Get NFL standings
        
        Args:
            season: Season year
            season_type: Season type (regular, pre, post)
            grouping: How to group standings (league, conference, division)
        """
        if season is None:
            from datetime import datetime
            season = str(datetime.now().year)
        
        try:
            # Try Sleeper.com web scraping
            standings = self._get_sleeper_standings(season, season_type)
            
            if not standings:
                # Fallback to basic team list
                standings = self._get_basic_team_standings()
            
            return standings
        except Exception as e:
            raise Exception(f"Failed to get NFL standings: {str(e)}")
    
    def _get_sleeper_standings(self, season: str, season_type: str) -> List[Dict[str, Any]]:
        """Get standings from Sleeper.com"""
        try:
            # Sleeper standings URL
            url = f"https://sleeper.com/nfl/standings/{season}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            html = response.text
            
            standings = []
            
            # Try to extract __NEXT_DATA__
            next_data_match = re.search(
                r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                html, re.DOTALL
            )
            
            if next_data_match:
                try:
                    data = json.loads(next_data_match.group(1))
                    standings_data = self._extract_standings_from_json(data)
                    if standings_data:
                        standings.extend(standings_data)
                except Exception:
                    pass
            
            # Fallback: Parse HTML tables
            if not standings:
                standings = self._parse_standings_html(html)
            
            return standings
        except Exception:
            return []
    
    def _extract_standings_from_json(self, data: Any, depth: int = 0) -> List[Dict[str, Any]]:
        """Recursively extract standings from JSON"""
        if depth > 5:
            return []
        
        standings = []
        
        if isinstance(data, dict):
            # Look for team standings data
            if self._looks_like_team_record(data):
                standings.append(data)
            
            # Recurse into nested structures
            for value in data.values():
                standings.extend(self._extract_standings_from_json(value, depth + 1))
        elif isinstance(data, list):
            for item in data:
                standings.extend(self._extract_standings_from_json(item, depth + 1))
        
        return standings
    
    def _looks_like_team_record(self, data: Dict[str, Any]) -> bool:
        """Check if data looks like a team record"""
        if not isinstance(data, dict):
            return False
        
        # Look for team record indicators
        has_team = any(key in data for key in ['team', 'team_name', 'abbreviation'])
        has_record = any(key in data for key in ['wins', 'losses', 'win_pct', 'record'])
        
        return has_team and has_record
    
    def _parse_standings_html(self, html: str) -> List[Dict[str, Any]]:
        """Parse standings from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            standings = []
            
            # Look for standings tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        try:
                            team_cell = cells[0].get_text(strip=True)
                            record_cell = cells[1].get_text(strip=True)
                            
                            # Parse record (e.g., "12-4" or "12-4-0")
                            record_match = re.match(r'(\d+)-(\d+)(?:-(\d+))?', record_cell)
                            if record_match:
                                wins = int(record_match.group(1))
                                losses = int(record_match.group(2))
                                ties = int(record_match.group(3) or 0)
                                
                                standings.append({
                                    'team': team_cell,
                                    'wins': wins,
                                    'losses': losses,
                                    'ties': ties,
                                    'win_pct': wins / (wins + losses + ties) if (wins + losses + ties) > 0 else 0,
                                    'source': 'sleeper_html'
                                })
                        except Exception:
                            continue
            
            return standings
        except Exception:
            return []
    
    def _get_basic_team_standings(self) -> List[Dict[str, Any]]:
        """Get basic NFL team list as fallback"""
        # NFL teams with basic structure
        nfl_teams = [
            # AFC East
            {'team': 'BUF', 'conference': 'AFC', 'division': 'East'},
            {'team': 'MIA', 'conference': 'AFC', 'division': 'East'},
            {'team': 'NE', 'conference': 'AFC', 'division': 'East'},
            {'team': 'NYJ', 'conference': 'AFC', 'division': 'East'},
            # AFC North
            {'team': 'BAL', 'conference': 'AFC', 'division': 'North'},
            {'team': 'CIN', 'conference': 'AFC', 'division': 'North'},
            {'team': 'CLE', 'conference': 'AFC', 'division': 'North'},
            {'team': 'PIT', 'conference': 'AFC', 'division': 'North'},
            # AFC South
            {'team': 'HOU', 'conference': 'AFC', 'division': 'South'},
            {'team': 'IND', 'conference': 'AFC', 'division': 'South'},
            {'team': 'JAX', 'conference': 'AFC', 'division': 'South'},
            {'team': 'TEN', 'conference': 'AFC', 'division': 'South'},
            # AFC West
            {'team': 'DEN', 'conference': 'AFC', 'division': 'West'},
            {'team': 'KC', 'conference': 'AFC', 'division': 'West'},
            {'team': 'LV', 'conference': 'AFC', 'division': 'West'},
            {'team': 'LAC', 'conference': 'AFC', 'division': 'West'},
            # NFC East
            {'team': 'DAL', 'conference': 'NFC', 'division': 'East'},
            {'team': 'NYG', 'conference': 'NFC', 'division': 'East'},
            {'team': 'PHI', 'conference': 'NFC', 'division': 'East'},
            {'team': 'WAS', 'conference': 'NFC', 'division': 'East'},
            # NFC North
            {'team': 'CHI', 'conference': 'NFC', 'division': 'North'},
            {'team': 'DET', 'conference': 'NFC', 'division': 'North'},
            {'team': 'GB', 'conference': 'NFC', 'division': 'North'},
            {'team': 'MIN', 'conference': 'NFC', 'division': 'North'},
            # NFC South
            {'team': 'ATL', 'conference': 'NFC', 'division': 'South'},
            {'team': 'CAR', 'conference': 'NFC', 'division': 'South'},
            {'team': 'NO', 'conference': 'NFC', 'division': 'South'},
            {'team': 'TB', 'conference': 'NFC', 'division': 'South'},
            # NFC West
            {'team': 'ARI', 'conference': 'NFC', 'division': 'West'},
            {'team': 'LAR', 'conference': 'NFC', 'division': 'West'},
            {'team': 'SF', 'conference': 'NFC', 'division': 'West'},
            {'team': 'SEA', 'conference': 'NFC', 'division': 'West'},
        ]
        
        # Add placeholder records
        for team in nfl_teams:
            team.update({
                'wins': 0,
                'losses': 0,
                'ties': 0,
                'win_pct': 0.0,
                'source': 'fallback'
            })
        
        return nfl_teams