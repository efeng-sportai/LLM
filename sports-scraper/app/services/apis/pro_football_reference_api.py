"""
Pro Football Reference Web API Client
Web scraping client for Pro-Football-Reference.com data (advanced stats, game logs)
"""

import requests
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup


class ProFootballReferenceAPI:
    """Web scraping client for Pro-Football-Reference.com"""
    
    def __init__(self):
        self.base_url = "https://www.pro-football-reference.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    # ==================== Player Game Logs ====================
    
    def get_player_game_log(self, player_id: str, season: str = None) -> List[Dict[str, Any]]:
        """Get detailed game logs for a player"""
        if season is None:
            season = str(datetime.now().year)
        
        url = f"{self.base_url}/players/{player_id[0]}/{player_id}/gamelog/{season}/"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_game_log_table(soup, player_id)
        except Exception as e:
            raise Exception(f"Failed to get game log for player {player_id}: {str(e)}")
    
    def _parse_game_log_table(self, soup: BeautifulSoup, player_id: str) -> List[Dict[str, Any]]:
        """Parse game log table from PFR page"""
        games = []
        
        # Find the game log table (usually has id 'stats')
        table = soup.find('table', {'id': 'stats'})
        if not table:
            return games
        
        # Get headers
        thead = table.find('thead')
        if not thead:
            return games
        
        header_rows = thead.find_all('tr')
        headers = []
        for row in header_rows:
            row_headers = [th.get_text(strip=True) for th in row.find_all(['th', 'td'])]
            if row_headers and len(row_headers) > headers:
                headers = row_headers
        
        # Get data rows
        tbody = table.find('tbody')
        if not tbody:
            return games
        
        for row in tbody.find_all('tr'):
            # Skip header rows within tbody
            if row.get('class') and 'thead' in row.get('class'):
                continue
            
            cells = row.find_all(['td', 'th'])
            if len(cells) != len(headers):
                continue
            
            game_data = {'player_id': player_id}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    header = headers[i].lower().replace(' ', '_').replace('%', 'pct')
                    value = cell.get_text(strip=True)
                    
                    # Convert numeric values
                    if value and value != '' and value != '--':
                        if value.replace('.', '').replace('-', '').isdigit():
                            try:
                                game_data[header] = float(value) if '.' in value else int(value)
                            except ValueError:
                                game_data[header] = value
                        else:
                            game_data[header] = value
            
            if game_data.get('date') or game_data.get('opp'):
                games.append(game_data)
        
        return games
    
    # ==================== Advanced Team Stats ====================
    
    def get_team_advanced_stats(self, season: str = None) -> List[Dict[str, Any]]:
        """Get advanced team statistics"""
        if season is None:
            season = str(datetime.now().year)
        
        url = f"{self.base_url}/years/{season}/opp.htm"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_team_stats_table(soup)
        except Exception as e:
            raise Exception(f"Failed to get team advanced stats: {str(e)}")
    
    def _parse_team_stats_table(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse team stats table"""
        teams = []
        
        # Find team stats table - it's actually called 'team_stats'
        table = soup.find('table', {'id': 'team_stats'})
        if not table:
            return teams
        
        # Get headers - PFR has complex header structure
        thead = table.find('thead')
        if not thead:
            return teams
        
        # Get the last header row which has the actual column names
        header_rows = thead.find_all('tr')
        headers = []
        if header_rows:
            # Use the last row for headers as it has the most specific column names
            last_row = header_rows[-1]
            headers = [th.get_text(strip=True) for th in last_row.find_all(['th', 'td'])]
        
        if not headers:
            return teams
        
        # Get data rows
        tbody = table.find('tbody')
        if not tbody:
            return teams
        
        for row in tbody.find_all('tr'):
            # Skip header rows within tbody
            if row.get('class') and 'thead' in row.get('class'):
                continue
                
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:  # Need at least rank, team, and one stat
                continue
            
            team_data = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    header = headers[i].lower().replace(' ', '_').replace('%', 'pct').replace('/', '_')
                    # Clean up header names
                    header = header.replace('(', '').replace(')', '').replace('-', '_')
                    value = cell.get_text(strip=True)
                    
                    # Convert numeric values
                    if value and value != '' and value != '--':
                        if value.replace('.', '').replace('-', '').replace(',', '').isdigit():
                            try:
                                clean_value = value.replace(',', '')
                                team_data[header] = float(clean_value) if '.' in clean_value else int(clean_value)
                            except ValueError:
                                team_data[header] = value
                        else:
                            team_data[header] = value
            
            # Look for team name in various possible columns
            team_name = None
            for key, value in team_data.items():
                if isinstance(value, str) and len(value) > 3 and any(word in value.lower() for word in ['texans', 'seahawks', 'eagles', 'cowboys', 'patriots', 'packers', 'steelers', 'ravens', 'chiefs', 'bills']):
                    team_name = value
                    team_data['team'] = team_name
                    break
            
            if team_name or team_data.get('tm') or len(team_data) > 3:
                teams.append(team_data)
        
        return teams
    
    # ==================== Player Season Stats ====================
    
    def get_player_season_stats(self, position: str = "QB", season: str = None) -> List[Dict[str, Any]]:
        """Get season stats for players by position"""
        if season is None:
            season = str(datetime.now().year)
        
        # Map positions to PFR URLs
        position_urls = {
            'QB': f"/years/{season}/passing.htm",
            'RB': f"/years/{season}/rushing.htm", 
            'WR': f"/years/{season}/receiving.htm",
            'TE': f"/years/{season}/receiving.htm",
            'K': f"/years/{season}/kicking.htm",
            'DEF': f"/years/{season}/opp.htm"
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
            raise Exception(f"Failed to get {position} stats: {str(e)}")
    
    def _parse_player_stats_table(self, soup: BeautifulSoup, position: str) -> List[Dict[str, Any]]:
        """Parse player stats table"""
        players = []
        
        # Find the main stats table (varies by position)
        table_ids = ['passing', 'rushing', 'receiving', 'kicking', 'team_stats']
        table = None
        
        for table_id in table_ids:
            table = soup.find('table', {'id': table_id})
            if table:
                break
        
        if not table:
            return players
        
        # Get headers
        thead = table.find('thead')
        if not thead:
            return players
        
        header_rows = thead.find_all('tr')
        headers = []
        for row in header_rows:
            row_headers = [th.get_text(strip=True) for th in row.find_all(['th', 'td'])]
            if row_headers and len(row_headers) > len(headers):
                headers = row_headers
        
        # Get data rows
        tbody = table.find('tbody')
        if not tbody:
            return players
        
        for row in tbody.find_all('tr'):
            # Skip header rows within tbody
            if row.get('class') and 'thead' in row.get('class'):
                continue
            
            cells = row.find_all(['td', 'th'])
            if len(cells) != len(headers):
                continue
            
            player_data = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    header = headers[i].lower().replace(' ', '_').replace('%', 'pct')
                    value = cell.get_text(strip=True)
                    
                    # Convert numeric values
                    if value and value != '' and value != '--':
                        if value.replace('.', '').replace('-', '').replace(',', '').isdigit():
                            try:
                                clean_value = value.replace(',', '')
                                player_data[header] = float(clean_value) if '.' in clean_value else int(clean_value)
                            except ValueError:
                                player_data[header] = value
                        else:
                            player_data[header] = value
            
            # Only include players if they have a name/player field
            if not (player_data.get('player') or player_data.get('name')):
                continue
            
            # For receiving stats, filter by actual position from the 'pos' column
            if position in ['WR', 'TE'] and 'pos' in player_data:
                actual_position = str(player_data['pos']).upper().strip()
                # Skip if this player doesn't match the requested position
                if position == 'WR' and actual_position != 'WR':
                    continue
                elif position == 'TE' and actual_position != 'TE':
                    continue
            
            # Set the position for this player
            player_data['position'] = position
            players.append(player_data)
        
        return players
    
    # ==================== Weekly Matchup Data ====================
    
    def get_weekly_matchups(self, season: str = None, week: int = 1) -> List[Dict[str, Any]]:
        """Get weekly matchup data with game details"""
        if season is None:
            season = str(datetime.now().year)
        
        url = f"{self.base_url}/years/{season}/week_{week}.htm"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_weekly_matchups(soup, season, week)
        except Exception as e:
            raise Exception(f"Failed to get week {week} matchups: {str(e)}")
    
    def _parse_weekly_matchups(self, soup: BeautifulSoup, season: str, week: int) -> List[Dict[str, Any]]:
        """Parse weekly matchup data"""
        matchups = []
        
        # Find game summaries
        game_summaries = soup.find_all('div', class_='game_summary')
        
        for game_div in game_summaries:
            matchup = {
                'season': season,
                'week': week,
                'source': 'pro_football_reference'
            }
            
            # Get teams
            teams = game_div.find_all('tr')
            if len(teams) >= 2:
                # Away team (first row)
                away_row = teams[0]
                away_team_cell = away_row.find('td')
                if away_team_cell:
                    matchup['away_team'] = away_team_cell.get_text(strip=True)
                
                # Home team (second row)  
                home_row = teams[1]
                home_team_cell = home_row.find('td')
                if home_team_cell:
                    matchup['home_team'] = home_team_cell.get_text(strip=True)
            
            # Get scores if available
            score_cells = game_div.find_all('td', class_='right')
            if len(score_cells) >= 2:
                try:
                    matchup['away_score'] = int(score_cells[0].get_text(strip=True))
                    matchup['home_score'] = int(score_cells[1].get_text(strip=True))
                except ValueError:
                    pass
            
            # Get game date/time
            date_elem = game_div.find('td', class_='right gamelink')
            if date_elem:
                matchup['game_date'] = date_elem.get_text(strip=True)
            
            if matchup.get('away_team') and matchup.get('home_team'):
                matchups.append(matchup)
        
        return matchups