"""
NFL Team Rankings Scraper
Fetches NFL team rankings from ESPN API and aggregates player stats
"""

import json
import re
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

# Get current year as default
CURRENT_YEAR = str(datetime.now().year)


class NFLRankingsScraper(BaseScraper):
    """Scraper for NFL team rankings"""
    
    def __init__(self, sleeper_api_scraper=None, standings_scraper=None):
        """
        Initialize NFL Rankings Scraper
        
        Args:
            sleeper_api_scraper: Optional SleeperAPIScraper instance for player stats
            standings_scraper: Optional NFLStandingsScraper instance for standings data
        """
        super().__init__()
        self.sleeper_api_scraper = sleeper_api_scraper
        self.standings_scraper = standings_scraper
    
    def get_nfl_team_rankings(
        self,
        season: str = None,
        season_type: str = "regular",
        ranking_type: str = "offense"
    ) -> List[Dict[str, Any]]:
        """
        Get NFL team rankings by offense, defense, etc. from ESPN API
        
        Args:
            season: Season year (default: current year)
            season_type: Season type - 'regular', 'pre', 'post' (default: 'regular')
            ranking_type: Type of ranking - 'offense', 'defense', 'total' (default: 'offense')
            
        Returns:
            List of team ranking dictionaries with stats
        """
        if season is None:
            season = CURRENT_YEAR
        # Use ESPN stats API which has team statistics
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/statistics"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            teams_rankings = []
            
            # Parse stats data - ESPN stats API returns player-level stats, not team stats
            # Strategy:
            # - For offense: Aggregate player stats by team (passing + rushing + receiving yards)
            # - For defense: Use web scraping fallback (team defensive stats)
            # - For total: Use standings data (already scraped)
            
            # For total rankings, use existing standings
            if ranking_type == "total":
                if not self.standings_scraper:
                    raise Exception("NFLStandingsScraper instance required for total rankings")
                standings = self.standings_scraper.get_sleeper_nfl_standings(season, season_type, "league")
                for standing in standings:
                    team_info = standing.get('team', {})
                    if isinstance(team_info, dict):
                        team_name = team_info.get('full_name', team_info.get('name', ''))
                    else:
                        team_name = str(team_info) if team_info else ''
                    
                    wins = standing.get('wins', 0)
                    losses = standing.get('losses', 0)
                    win_pct = wins / (wins + losses) if (wins + losses) > 0 else 0.0
                    
                    # Extract team abbreviation from team name using a comprehensive mapping
                    team_abbr = self._get_team_abbreviation(team_name)
                    
                    if team_name and team_abbr:
                        teams_rankings.append({
                            'team': team_name,
                            'abbreviation': team_abbr,
                            'ranking_type': ranking_type,
                            'ranking_value': win_pct,
                            'stats': {
                                'wins': wins,
                                'losses': losses,
                                'win_pct': {
                                    'value': win_pct,
                                    'display': f"{win_pct:.3f}"
                                },
                                'record': f"{wins}-{losses}"
                            },
                            'season': season,
                            'season_type': season_type
                        })
            # For offense, aggregate from player stats
            elif ranking_type == "offense":
                if not self.sleeper_api_scraper:
                    raise Exception("SleeperAPIScraper instance required for offense rankings")
                # Get all players with stats and aggregate by team
                try:
                    all_players = self.sleeper_api_scraper.get_sleeper_players("nfl")
                    player_stats = self.sleeper_api_scraper.get_sleeper_player_stats("nfl", season, season_type)
                    
                    # Aggregate stats by team
                    team_stats_dict = {}
                    
                    for player_id, stats in player_stats.items():
                        player = all_players.get(player_id)
                        if not player or not isinstance(player, dict):
                            continue
                        
                        team = player.get('team', '')
                        position = player.get('position', '')
                        
                        if not team or not position:
                            continue
                        
                        # Only aggregate offensive players for offense rankings
                        if position in ['QB', 'RB', 'WR', 'TE', 'WR', 'FB']:
                            if team not in team_stats_dict:
                                team_stats_dict[team] = {
                                    'team': team,  # Will update with full name later
                                    'abbreviation': team,
                                    'total_yards': 0,
                                    'total_points': 0
                                }
                            
                            # Aggregate yards and points from player stats
                            # Stats format: {stat_type: value}
                            if isinstance(stats, dict):
                                # Look for rushing yards, receiving yards, passing yards
                                rushing = stats.get('rush_yd', 0) or stats.get('rushing_yd', 0) or 0
                                receiving = stats.get('rec_yd', 0) or stats.get('receiving_yd', 0) or 0
                                passing = stats.get('pass_yd', 0) or stats.get('passing_yd', 0) or 0
                                
                                # Add to team totals
                                team_stats_dict[team]['total_yards'] += rushing + receiving + passing
                                
                                # Aggregate points
                                pts = stats.get('pts_half_ppr', 0) or stats.get('pts_std', 0) or 0
                                team_stats_dict[team]['total_points'] += pts
                    
                    # Convert to rankings list
                    for team_abbr, team_data in team_stats_dict.items():
                        if team_data['total_yards'] > 0:
                            teams_rankings.append({
                                'team': team_data['team'],
                                'abbreviation': team_abbr,
                                'ranking_type': ranking_type,
                                'ranking_value': team_data['total_yards'],
                                'stats': {
                                    'total_yards': {
                                        'value': team_data['total_yards'],
                                        'display': f"{team_data['total_yards']:.0f}"
                                    }
                                },
                                'season': season,
                                'season_type': season_type
                            })
                except Exception as e:
                    # If aggregation fails, continue with empty list
                    pass
            # For defense, aggregate defensive player stats by team
            elif ranking_type == "defense":
                if not self.sleeper_api_scraper:
                    raise Exception("SleeperAPIScraper instance required for defense rankings")
                # Get all players with stats and aggregate defensive stats by team
                try:
                    all_players = self.sleeper_api_scraper.get_sleeper_players("nfl")
                    player_stats = self.sleeper_api_scraper.get_sleeper_player_stats("nfl", season, season_type)
                    
                    # Aggregate defensive stats by team
                    team_stats_dict = {}
                    
                    for player_id, stats in player_stats.items():
                        player = all_players.get(player_id)
                        if not player or not isinstance(player, dict):
                            continue
                        
                        team = player.get('team', '')
                        position = player.get('position', '')
                        
                        if not team or not position:
                            continue
                        
                        # Only aggregate defensive players for defense rankings
                        # Defensive positions: DEF, LB, CB, S, DT, DE, NT
                        if position in ['DEF', 'LB', 'CB', 'S', 'DT', 'DE', 'NT', 'OLB', 'ILB', 'FS', 'SS']:
                            if team not in team_stats_dict:
                                team_stats_dict[team] = {
                                    'team': team,
                                    'abbreviation': team,
                                    'yards_allowed': 0,
                                    'points_allowed': 0,
                                    'sacks': 0,
                                    'interceptions': 0,
                                    'total_defense_score': 0  # Combined metric
                                }
                            
                            # Aggregate defensive stats
                            if isinstance(stats, dict):
                                # For defense, lower is better, so we track allowed stats
                                # We'll use inverse logic - teams that allow fewer yards/points rank higher
                                # For now, aggregate sacks and interceptions (positive defensive stats)
                                sacks = stats.get('sacks', 0) or stats.get('sack', 0) or 0
                                interceptions = stats.get('interceptions', 0) or stats.get('int', 0) or stats.get('ints', 0) or 0
                                
                                team_stats_dict[team]['sacks'] += sacks
                                team_stats_dict[team]['interceptions'] += interceptions
                                team_stats_dict[team]['total_defense_score'] += sacks + interceptions * 2  # Interceptions worth more
                    
                    # Convert to rankings list - higher defensive score = better defense
                    for team_abbr, team_data in team_stats_dict.items():
                        if team_data['total_defense_score'] > 0:
                            teams_rankings.append({
                                'team': team_data['team'],
                                'abbreviation': team_abbr,
                                'ranking_type': ranking_type,
                                'ranking_value': team_data['total_defense_score'],  # Higher = better
                                'stats': {
                                    'total_defense_score': {
                                        'value': team_data['total_defense_score'],
                                        'display': f"{team_data['total_defense_score']:.0f}"
                                    },
                                    'sacks': team_data['sacks'],
                                    'interceptions': team_data['interceptions']
                                },
                                'season': season,
                                'season_type': season_type
                            })
                except Exception as e:
                    # If aggregation fails, try web scraping as fallback
                    teams_rankings = self._get_nfl_team_rankings_from_web(season, season_type, ranking_type)
            
            # Sort by ranking_value
            if ranking_type == "defense":
                # For defense with our score-based approach, higher is better (more sacks/interceptions)
                teams_rankings.sort(key=lambda x: x['ranking_value'] if x['ranking_value'] is not None else float('-inf'), reverse=True)
            else:
                # For offense and total, higher is better
                teams_rankings.sort(key=lambda x: x['ranking_value'] if x['ranking_value'] is not None else float('-inf'), reverse=True)
            
            return teams_rankings
            
        except Exception as e:
            raise Exception(f"Failed to fetch/parse NFL team rankings: {str(e)}")
    
    def _get_team_abbreviation(self, team_name: str) -> str:
        """Get team abbreviation from team name"""
        if not team_name:
            return ""
        
        team_name_lower = team_name.lower()
        # Comprehensive NFL team name to abbreviation mapping
        team_abbr_map = {
            'arizona cardinals': 'ARI', 'cardinals': 'ARI',
            'atlanta falcons': 'ATL', 'falcons': 'ATL',
            'baltimore ravens': 'BAL', 'ravens': 'BAL',
            'buffalo bills': 'BUF', 'bills': 'BUF',
            'carolina panthers': 'CAR', 'panthers': 'CAR',
            'chicago bears': 'CHI', 'bears': 'CHI',
            'cincinnati bengals': 'CIN', 'bengals': 'CIN',
            'cleveland browns': 'CLE', 'browns': 'CLE',
            'dallas cowboys': 'DAL', 'cowboys': 'DAL',
            'denver broncos': 'DEN', 'broncos': 'DEN',
            'detroit lions': 'DET', 'lions': 'DET',
            'green bay packers': 'GB', 'packers': 'GB',
            'houston texans': 'HOU', 'texans': 'HOU',
            'indianapolis colts': 'IND', 'colts': 'IND',
            'jacksonville jaguars': 'JAX', 'jaguars': 'JAX',
            'kansas city chiefs': 'KC', 'chiefs': 'KC',
            'las vegas raiders': 'LV', 'raiders': 'LV', 'oakland raiders': 'LV',
            'los angeles chargers': 'LAC', 'chargers': 'LAC',
            'los angeles rams': 'LAR', 'rams': 'LAR',
            'miami dolphins': 'MIA', 'dolphins': 'MIA',
            'minnesota vikings': 'MIN', 'vikings': 'MIN',
            'new england patriots': 'NE', 'patriots': 'NE',
            'new orleans saints': 'NO', 'saints': 'NO',
            'new york giants': 'NYG', 'giants': 'NYG',
            'new york jets': 'NYJ', 'jets': 'NYJ',
            'philadelphia eagles': 'PHI', 'eagles': 'PHI',
            'pittsburgh steelers': 'PIT', 'steelers': 'PIT',
            'san francisco 49ers': 'SF', '49ers': 'SF',
            'seattle seahawks': 'SEA', 'seahawks': 'SEA',
            'tampa bay buccaneers': 'TB', 'buccaneers': 'TB',
            'tennessee titans': 'TEN', 'titans': 'TEN',
            'washington commanders': 'WAS', 'commanders': 'WAS', 'redskins': 'WAS', 'washington football team': 'WAS',
        }
        
        # Try exact match first
        if team_name_lower in team_abbr_map:
            return team_abbr_map[team_name_lower]
        
        # Try partial matches
        for key, abbr in team_abbr_map.items():
            if key in team_name_lower or team_name_lower in key:
                return abbr
        
        # Last resort: use first 2-3 letters from each word
        words = team_name.split()
        if len(words) >= 2:
            # Take first letter of first two words (e.g., "Green Bay" -> "GB")
            return ''.join([w[0].upper() for w in words[:2]])
        else:
            # Take first 3 letters
            return team_name[:3].upper()
    
    def _get_nfl_team_rankings_from_web(
        self,
        season: str,
        season_type: str,
        ranking_type: str
    ) -> List[Dict[str, Any]]:
        """
        Fallback method: Get team rankings from web scraping (NFL.com team stats)
        """
        # NFL.com team stats URL - try different endpoints
        urls = {
            "offense": f"https://www.nfl.com/stats/team-stats/offense/{season}/reg/all",
            "defense": f"https://www.nfl.com/stats/team-stats/defense/{season}/reg/all",
            "total": f"https://www.nfl.com/standings/{season}/REG"
        }
        
        url = urls.get(ranking_type, urls["offense"])
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            html = response.text
            
            soup = BeautifulSoup(html, 'html.parser')
            teams_rankings = []
            
            # Try to extract __NEXT_DATA__ first
            next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
            if next_data_match:
                try:
                    data = json.loads(next_data_match.group(1))
                    # Recursively search for team stats
                    teams_data = self._extract_team_stats_from_json(data, ranking_type)
                    if teams_data:
                        return teams_data
                except:
                    pass
            
            # Fallback: Parse HTML table
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')[1:]  # Skip header
                for i, row in enumerate(rows, 1):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # Try to extract team name and stat value
                        team_name = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                        stat_value = None
                        
                        # Look for stat value in other cells
                        for cell in cells[1:]:
                            text = cell.get_text(strip=True)
                            # Try to parse as number
                            try:
                                stat_value = float(text.replace(',', ''))
                                break
                            except:
                                continue
                        
                        if team_name and stat_value is not None:
                            teams_rankings.append({
                                'team': team_name,
                                'abbreviation': team_name[:3].upper() if len(team_name) >= 3 else team_name.upper(),
                                'ranking_type': ranking_type,
                                'ranking_value': -stat_value if ranking_type == "defense" else stat_value,
                                'season': season,
                                'season_type': season_type
                            })
            
            return teams_rankings
        except Exception as e:
            return []
    
    def _extract_team_stats_from_json(self, data: Any, ranking_type: str, depth: int = 0) -> List[Dict[str, Any]]:
        """Recursively extract team stats from JSON structure"""
        if depth > 5:  # Limit recursion depth
            return []
        
        teams_rankings = []
        
        if isinstance(data, dict):
            # Check if this dict looks like team stats
            if 'team' in data and ('yards' in str(data).lower() or 'points' in str(data).lower() or 'win' in str(data).lower()):
                team_name = data.get('team', {}).get('displayName', '') if isinstance(data.get('team'), dict) else ''
                team_abbr = data.get('team', {}).get('abbreviation', '') if isinstance(data.get('team'), dict) else ''
                
                if team_name or team_abbr:
                    stat_value = None
                    if ranking_type == "offense":
                        stat_value = data.get('totalYards') or data.get('yards') or data.get('pointsFor')
                    elif ranking_type == "defense":
                        stat_value = data.get('yardsAllowed') or data.get('yardsAgainst') or data.get('pointsAgainst')
                        if stat_value is not None:
                            stat_value = -stat_value  # Lower is better
                    elif ranking_type == "total":
                        stat_value = data.get('winPercentage') or data.get('wins')
                    
                    if stat_value is not None:
                        teams_rankings.append({
                            'team': team_name or team_abbr,
                            'abbreviation': team_abbr or team_name[:3].upper(),
                            'ranking_type': ranking_type,
                            'ranking_value': stat_value,
                            'season': data.get('season', ''),
                            'season_type': data.get('season_type', '')
                        })
            
            # Recurse into nested structures
            for value in data.values():
                teams_rankings.extend(self._extract_team_stats_from_json(value, ranking_type, depth + 1))
        elif isinstance(data, list):
            for item in data:
                teams_rankings.extend(self._extract_team_stats_from_json(item, ranking_type, depth + 1))
        
        return teams_rankings

