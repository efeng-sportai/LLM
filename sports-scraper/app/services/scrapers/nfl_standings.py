"""
NFL Standings Scraper
Scrapes NFL standings from Sleeper.com webpage
"""

import json
import re
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

# Get current year as default
CURRENT_YEAR = str(datetime.now().year)


class NFLStandingsScraper(BaseScraper):
    """Scraper for NFL standings from Sleeper.com"""
    
    def get_sleeper_nfl_standings(
        self,
        season: str = None,
        season_type: str = "regular",
        grouping: str = "league"
    ) -> List[Dict[str, Any]]:
        """
        Get NFL standings from Sleeper webpage
        
        Args:
            season: Season year (default: current year)
            season_type: Season type - 'regular', 'pre', 'post' (default: 'regular')
            grouping: Grouping type - 'league', 'conference', 'division' (default: 'league')
            
        Returns:
            List of team standings dictionaries with team info and stats
        """
        if season is None:
            season = CURRENT_YEAR
        # Sleeper doesn't have a direct API endpoint for standings, so we scrape the webpage
        url = f"https://sleeper.com/sports/nfl/standings?grouping={grouping}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            html = response.text
            
            # Try to extract JSON data from embedded scripts
            # The data is in self.__next_f.push format or embedded JSON
            
            # Method 1: Extract from self.__next_f.push calls
            push_pattern = r'self\.__next_f\.push\(\[1,"(.*?)"\]\)'
            push_matches = re.findall(push_pattern, html)
            
            for push_content in push_matches:
                if 'standings' in push_content and 'team' in push_content:
                    # Try to extract the standings array
                    # Look for the pattern: "standings":[...
                    standings_match = re.search(r'"standings":(\[.*?\])', push_content, re.DOTALL)
                    if standings_match:
                        json_str = standings_match.group(1)
                        try:
                            standings = json.loads(json_str)
                            if isinstance(standings, list) and standings and isinstance(standings[0], dict):
                                if 'team' in standings[0] or 'wins' in standings[0]:
                                    return standings
                        except json.JSONDecodeError:
                            continue
                    
                    # Try alternative: find any array with team data
                    team_array_pattern = r'(\[.*?"team":\{.*?"wins":\d+.*?"losses":\d+.*?\])'
                    team_match = re.search(team_array_pattern, push_content, re.DOTALL)
                    if team_match:
                        try:
                            json_str = team_match.group(1)
                            # Clean up JSON - remove trailing commas
                            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                            standings = json.loads(json_str)
                            if isinstance(standings, list) and standings and isinstance(standings[0], dict):
                                if 'team' in standings[0] or 'wins' in standings[0]:
                                    return standings
                        except:
                            continue
            
            # Method 2: Look for JSON directly in HTML (not in scripts)
            json_array_pattern = r'\[.*?"team":\{.*?"wins":\d+.*?"losses":\d+.*?\]'
            direct_matches = re.findall(json_array_pattern, html, re.DOTALL)
            for match in direct_matches[:3]:  # Try first 3 matches
                try:
                    # Clean up JSON
                    json_str = re.sub(r',(\s*[}\]])', r'\1', match)
                    data = json.loads(json_str)
                    if isinstance(data, list) and data and isinstance(data[0], dict):
                        if 'team' in data[0] or 'wins' in data[0]:
                            return data
                except:
                    continue
            
            # If JSON extraction fails, fall back to HTML table scraping
            # This is a simpler, more reliable approach
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for the standings table
            # Based on the HTML structure from the webpage
            tables = soup.find_all('table')
            if tables:
                standings = []
                for table in tables:
                    rows = table.find_all('tr')[1:]  # Skip header row
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 4:
                            try:
                                # Cell structure based on actual HTML:
                                # Cell 0: Rank (e.g., "1", "T3")
                                # Cell 1: Team identifier (e.g., "IndianapolisColts")
                                # Cell 2: Full team name (e.g., "Indianapolis Colts")
                                # Cell 3: Record (e.g., "7-1" or "5-1-1")
                                
                                # Extract team name from cell 2 (full team name)
                                team_name = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                                
                                # If cell 2 is empty, try cell 1
                                if not team_name and len(cells) > 1:
                                    team_name = cells[1].get_text(strip=True)
                                
                                # Extract W-L-T record from cell 3
                                record_text = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                                
                                # If record not in cell 3, try cell 2
                                if not record_text and len(cells) > 2:
                                    record_text = cells[2].get_text(strip=True)
                                
                                # Parse record (format: "7-1" or "5-1-1")
                                record_parts = record_text.split('-') if record_text else []
                                wins = int(record_parts[0]) if len(record_parts) > 0 and record_parts[0].isdigit() else 0
                                losses = int(record_parts[1]) if len(record_parts) > 1 and record_parts[1].isdigit() else 0
                                ties = int(record_parts[2]) if len(record_parts) > 2 and record_parts[2].isdigit() else 0
                                
                                # Only add if we have a valid team name
                                if team_name and team_name not in ["1", "2", "T3", "T7", "T11", "T14", "T19", "T22", "T25", "T27", "T30"]:
                                    standings.append({
                                        'team': {'full_name': team_name, 'name': team_name},
                                        'wins': wins,
                                        'losses': losses,
                                        'ties': ties,
                                        'record': record_text
                                    })
                            except Exception as e:
                                continue
                
                if standings:
                    return standings
            
            raise Exception("Could not extract standings data from webpage")
            
        except Exception as e:
            raise Exception(f"Failed to fetch/parse Sleeper NFL standings: {str(e)}")

