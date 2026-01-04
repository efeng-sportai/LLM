"""
NFL.com Web API Client
Web scraping client for NFL.com data (official stats, news)
"""

import requests
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup


class NFLComAPI:
    """Web scraping client for NFL.com"""
    
    def __init__(self):
        self.base_url = "https://www.nfl.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    # ==================== Player Stats ====================
    
    def get_player_stats(self, position: str = "QB", season: str = None) -> List[Dict[str, Any]]:
        """Get player statistics by position"""
        if season is None:
            season = str(datetime.now().year)
        
        # NFL.com stats URLs by position
        position_urls = {
            'QB': f"/stats/player-stats/category/passing/season/{season}/seasontype/REG",
            'RB': f"/stats/player-stats/category/rushing/season/{season}/seasontype/REG",
            'WR': f"/stats/player-stats/category/receiving/season/{season}/seasontype/REG",
            'TE': f"/stats/player-stats/category/receiving/season/{season}/seasontype/REG",
            'K': f"/stats/player-stats/category/field-goals/season/{season}/seasontype/REG",
            'DEF': f"/stats/team-stats/category/defense/season/{season}/seasontype/REG"
        }
        
        url_path = position_urls.get(position.upper())
        if not url_path:
            raise ValueError(f"Unsupported position: {position}")
        
        url = f"{self.base_url}{url_path}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_player_stats_table(soup, position)
        except Exception as e:
            raise Exception(f"Failed to get {position} stats from NFL.com: {str(e)}")
    
    def _parse_player_stats_table(self, soup: BeautifulSoup, position: str) -> List[Dict[str, Any]]:
        """Parse player stats table from NFL.com"""
        players = []
        
        # Find stats table (NFL.com uses various table structures)
        tables = soup.find_all('table')
        
        for table in tables:
            # Get headers
            thead = table.find('thead')
            if not thead:
                continue
            
            headers = [th.get_text(strip=True) for th in thead.find_all(['th', 'td'])]
            if not headers:
                continue
            
            # Get data rows
            tbody = table.find('tbody')
            if not tbody:
                continue
            
            for row in tbody.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) != len(headers):
                    continue
                
                player_data = {'position': position, 'source': 'nfl_com'}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        header = headers[i].lower().replace(' ', '_').replace('%', 'pct')
                        value = cell.get_text(strip=True)
                        
                        # Convert numeric values
                        if value and value != '' and value != '--' and value != 'N/A':
                            if value.replace('.', '').replace('-', '').replace(',', '').isdigit():
                                try:
                                    clean_value = value.replace(',', '')
                                    player_data[header] = float(clean_value) if '.' in clean_value else int(clean_value)
                                except ValueError:
                                    player_data[header] = value
                            else:
                                player_data[header] = value
                
                if player_data.get('player') or player_data.get('name'):
                    players.append(player_data)
            
            # If we found data, break (use first valid table)
            if players:
                break
        
        return players
    
    # ==================== Team Stats ====================
    
    def get_team_stats(self, stat_category: str = "offense", season: str = None) -> List[Dict[str, Any]]:
        """Get team statistics by category"""
        if season is None:
            season = str(datetime.now().year)
        
        # NFL.com team stats URLs
        category_urls = {
            'offense': f"/stats/team-stats/category/offense/season/{season}/seasontype/REG",
            'defense': f"/stats/team-stats/category/defense/season/{season}/seasontype/REG",
            'special_teams': f"/stats/team-stats/category/special-teams/season/{season}/seasontype/REG"
        }
        
        url_path = category_urls.get(stat_category.lower())
        if not url_path:
            raise ValueError(f"Unsupported stat category: {stat_category}")
        
        url = f"{self.base_url}{url_path}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_team_stats_table(soup, stat_category)
        except Exception as e:
            raise Exception(f"Failed to get team {stat_category} stats: {str(e)}")
    
    def _parse_team_stats_table(self, soup: BeautifulSoup, stat_category: str) -> List[Dict[str, Any]]:
        """Parse team stats table"""
        teams = []
        
        # Find team stats table
        tables = soup.find_all('table')
        
        for table in tables:
            # Get headers
            thead = table.find('thead')
            if not thead:
                continue
            
            headers = [th.get_text(strip=True) for th in thead.find_all(['th', 'td'])]
            if not headers:
                continue
            
            # Get data rows
            tbody = table.find('tbody')
            if not tbody:
                continue
            
            for row in tbody.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) != len(headers):
                    continue
                
                team_data = {'stat_category': stat_category, 'source': 'nfl_com'}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        header = headers[i].lower().replace(' ', '_').replace('%', 'pct')
                        value = cell.get_text(strip=True)
                        
                        # Convert numeric values
                        if value and value != '' and value != '--' and value != 'N/A':
                            if value.replace('.', '').replace('-', '').replace(',', '').isdigit():
                                try:
                                    clean_value = value.replace(',', '')
                                    team_data[header] = float(clean_value) if '.' in clean_value else int(clean_value)
                                except ValueError:
                                    team_data[header] = value
                            else:
                                team_data[header] = value
                
                if team_data.get('team') or team_data.get('tm'):
                    teams.append(team_data)
            
            # If we found data, break
            if teams:
                break
        
        return teams
    
    # ==================== Game Center Data ====================
    
    def get_game_center_data(self, game_id: str) -> Dict[str, Any]:
        """Get detailed game data from NFL.com game center"""
        url = f"{self.base_url}/games/{game_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_game_center(soup, game_id)
        except Exception as e:
            raise Exception(f"Failed to get game center data for {game_id}: {str(e)}")
    
    def _parse_game_center(self, soup: BeautifulSoup, game_id: str) -> Dict[str, Any]:
        """Parse game center data"""
        game_data = {
            'game_id': game_id,
            'source': 'nfl_com',
            'scraped_at': datetime.now().isoformat()
        }
        
        # Get team names and scores
        team_elements = soup.find_all(['div', 'span'], class_=re.compile(r'team|score', re.I))
        
        teams = []
        scores = []
        
        for elem in team_elements:
            text = elem.get_text(strip=True)
            
            # Check if it's a team name (usually 3 letters)
            if len(text) == 3 and text.isupper():
                teams.append(text)
            
            # Check if it's a score (numeric)
            elif text.isdigit():
                scores.append(int(text))
        
        if len(teams) >= 2:
            game_data['away_team'] = teams[0]
            game_data['home_team'] = teams[1]
        
        if len(scores) >= 2:
            game_data['away_score'] = scores[0]
            game_data['home_score'] = scores[1]
        
        # Get game status
        status_elem = soup.find(['div', 'span'], class_=re.compile(r'status|quarter', re.I))
        if status_elem:
            game_data['game_status'] = status_elem.get_text(strip=True)
        
        # Get game stats tables
        stats_tables = soup.find_all('table')
        game_data['stats_tables'] = []
        
        for table in stats_tables:
            table_data = self._parse_stats_table(table)
            if table_data:
                game_data['stats_tables'].append(table_data)
        
        return game_data
    
    def _parse_stats_table(self, table) -> Optional[Dict[str, Any]]:
        """Parse a stats table from game center"""
        if not table:
            return None
        
        # Get table caption/title
        caption = table.find('caption')
        table_title = caption.get_text(strip=True) if caption else "Unknown Stats"
        
        # Get headers
        thead = table.find('thead')
        if not thead:
            return None
        
        headers = [th.get_text(strip=True) for th in thead.find_all(['th', 'td'])]
        
        # Get data rows
        tbody = table.find('tbody')
        if not tbody:
            return None
        
        rows = []
        for row in tbody.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) == len(headers):
                row_data = {}
                for i, cell in enumerate(cells):
                    header = headers[i].lower().replace(' ', '_')
                    value = cell.get_text(strip=True)
                    row_data[header] = value
                rows.append(row_data)
        
        return {
            'title': table_title,
            'headers': headers,
            'rows': rows
        }