"""
Sleeper API Scraper
Handles all Sleeper API endpoints for users, leagues, players, stats, etc.
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from .base_scraper import BaseScraper

# Get current year as default
CURRENT_YEAR = str(datetime.now().year)


class SleeperAPIScraper(BaseScraper):
    """Scraper for Sleeper API endpoints"""
    
    def __init__(self):
        super().__init__()
        # Sleeper API base URL (official API)
        self.sleeper_api_base = "https://api.sleeper.app/v1"
    
    def get_sleeper_user(self, username: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Get Sleeper user information
        
        Args:
            username: Sleeper username
            user_id: Sleeper user ID (use either username or user_id)
            
        Returns:
            Dictionary containing user data
        """
        if user_id:
            url = f"{self.sleeper_api_base}/user/{user_id}"
        elif username:
            url = f"{self.sleeper_api_base}/user/{username}"
        else:
            raise ValueError("Must provide either username or user_id")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Sleeper user: {str(e)}")
    
    def get_sleeper_leagues(self, user_id: str, season: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get leagues for a Sleeper user
        
        Args:
            user_id: Sleeper user ID
            season: Optional season year (e.g., '2024')
            
        Returns:
            List of league dictionaries
        """
        url = f"{self.sleeper_api_base}/user/{user_id}/leagues/nfl/{season or ''}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            leagues = response.json()
            return leagues if isinstance(leagues, list) else []
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Sleeper leagues: {str(e)}")
    
    def get_sleeper_league(self, league_id: str) -> Dict[str, Any]:
        """
        Get Sleeper league information
        
        Args:
            league_id: Sleeper league ID
            
        Returns:
            Dictionary containing league data
        """
        url = f"{self.sleeper_api_base}/league/{league_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Sleeper league: {str(e)}")
    
    def get_sleeper_rosters(self, league_id: str) -> List[Dict[str, Any]]:
        """
        Get rosters for a Sleeper league
        
        Args:
            league_id: Sleeper league ID
            
        Returns:
            List of roster dictionaries
        """
        url = f"{self.sleeper_api_base}/league/{league_id}/rosters"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            rosters = response.json()
            return rosters if isinstance(rosters, list) else []
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Sleeper rosters: {str(e)}")
    
    def get_sleeper_players(self, sport: str = "nfl") -> Dict[str, Any]:
        """
        Get all players for a sport from Sleeper
        
        Args:
            sport: Sport abbreviation (default: 'nfl')
            
        Returns:
            Dictionary mapping player IDs to player data
        """
        url = f"{self.sleeper_api_base}/players/{sport}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Sleeper players: {str(e)}")
    
    def get_sleeper_trending_players(
        self, 
        sport: str = "nfl", 
        trend_type: str = "add", 
        lookback_hours: int = 24, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get trending players from Sleeper
        
        Args:
            sport: Sport abbreviation (default: 'nfl')
            trend_type: Type of trend - 'add' (players being added) or 'drop' (players being dropped)
            lookback_hours: Hours to look back for trending data (default: 24)
            limit: Maximum number of trending players to return (default: 100)
            
        Returns:
            List of dictionaries with 'player_id' and 'count' (trending activity count)
        """
        url = f"{self.sleeper_api_base}/players/{sport}/trending/{trend_type}"
        params = {
            "lookback_hours": lookback_hours,
            "limit": limit
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            trending = response.json()
            
            # Get all players to enrich trending data
            all_players = self.get_sleeper_players(sport)
            
            # Enrich trending data with full player info
            enriched_trending = []
            for trend_item in trending:
                player_id = trend_item.get("player_id")
                count = trend_item.get("count", 0)
                
                if player_id and player_id in all_players:
                    player_data = all_players[player_id].copy()
                    player_data["trend_count"] = count
                    player_data["trend_type"] = trend_type
                    enriched_trending.append(player_data)
            
            return enriched_trending
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Sleeper trending players: {str(e)}")
    
    def get_sleeper_player_stats(
        self,
        sport: str = "nfl",
        season: str = None,
        season_type: str = "regular"
    ) -> Dict[str, Any]:
        """
        Get player statistics from Sleeper
        
        Args:
            sport: Sport abbreviation (default: 'nfl')
            season: Season year (default: current year)
            season_type: Season type - 'regular', 'pre', 'post' (default: 'regular')
            
        Returns:
            Dictionary mapping player IDs to stats
        """
        if season is None:
            season = CURRENT_YEAR
        url = f"{self.sleeper_api_base}/stats/{sport}/{season_type}/{season}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Sleeper player stats: {str(e)}")
    
    def get_sleeper_top_players_by_stats(
        self,
        sport: str = "nfl",
        position: Optional[str] = None,
        stat_key: str = "pts_half_ppr",
        limit: int = 100,
        season: str = None,
        season_type: str = "regular"
    ) -> List[Dict[str, Any]]:
        """
        Get top NFL players from Sleeper sorted by statistics
        
        Args:
            sport: Sport abbreviation (default: 'nfl')
            position: Filter by position (QB, RB, WR, TE, etc.) - optional
            stat_key: Stat to sort by (default: 'pts_half_ppr' for fantasy points)
                     Options: 'pts_half_ppr', 'pts_ppr', 'pts_std', 'pass_td', 'rush_td', 
                             'rec_td', 'pass_yd', 'rush_yd', 'rec_yd', etc.
            limit: Maximum number of top players to return (default: 100)
            season: Season year (default: current year)
            season_type: Season type - 'regular', 'pre', 'post' (default: 'regular')
            
        Returns:
            List of top player dictionaries with stats
        """
        if season is None:
            season = CURRENT_YEAR
        try:
            # Get player stats
            stats = self.get_sleeper_player_stats(sport, season, season_type)
            
            # Get all players to enrich stats with player info
            all_players = self.get_sleeper_players(sport)
            
            # Combine stats with player data and filter
            players_with_stats = []
            for player_id, player_stats in stats.items():
                if player_id not in all_players:
                    continue
                
                player_data = all_players[player_id].copy()
                
                # Filter by position if specified
                if position:
                    player_pos = player_data.get("position", "")
                    if player_pos != position:
                        continue
                
                # For team defenses (DEF), they might not have status/team fields like individual players
                # Note: Sleeper API uses "DEF" for team defenses, not "DST"
                is_team_defense = position == "DEF" or player_data.get("position", "") == "DEF"
                
                if not is_team_defense:
                    # Only include active players with teams (for individual players)
                    player_status = player_data.get("status", "").upper() or ""
                    player_team = player_data.get("team")
                    has_team = player_team and player_team != "None" and player_team is not None
                    
                    if player_status != "ACTIVE" or not has_team:
                        continue
                else:
                    # For team defenses, check if they have a team (required)
                    player_team = player_data.get("team")
                    has_team = player_team and player_team != "None" and player_team is not None
                    if not has_team:
                        continue
                
                # Get stat value (default to 0 if stat not found)
                # Handle None values properly
                stat_value = player_stats.get(stat_key)
                if stat_value is None:
                    stat_value = 0
                else:
                    try:
                        stat_value = float(stat_value)
                    except (ValueError, TypeError):
                        stat_value = 0
                
                effective_stat_key = stat_key  # Track which stat key we're actually using
                if stat_value == 0 and is_team_defense:
                    # Try alternative stat keys for team defenses
                    alt_stat_keys = ["pts_std", "pts_half_ppr", "pts_ppr", "def_td", "def_st_td"]
                    for alt_key in alt_stat_keys:
                        alt_value = player_stats.get(alt_key)
                        if alt_value is not None:
                            try:
                                alt_value = float(alt_value)
                                if alt_value != 0:
                                    stat_value = alt_value
                                    effective_stat_key = alt_key  # Track which stat key worked
                                    break
                            except (ValueError, TypeError):
                                continue
                
                if stat_value == 0:
                    continue  # Skip players/defenses with 0 for this stat
                
                # Combine player data with stats
                player_data["stats"] = player_stats
                player_data["stat_value"] = stat_value
                player_data["player_id"] = player_id
                
                players_with_stats.append(player_data)
            
            # Sort by stat value (descending)
            players_with_stats.sort(key=lambda x: float(x.get("stat_value", 0)), reverse=True)
            
            return players_with_stats[:limit]
        except Exception as e:
            raise Exception(f"Failed to fetch Sleeper top players by stats: {str(e)}")
    
    def get_sleeper_draft(self, draft_id: str) -> Dict[str, Any]:
        """
        Get draft information from Sleeper
        
        Args:
            draft_id: Sleeper draft ID
            
        Returns:
            Dictionary containing draft data
        """
        url = f"{self.sleeper_api_base}/draft/{draft_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Sleeper draft: {str(e)}")
    
    def get_sleeper_matchups(self, league_id: str, week: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get matchups for a Sleeper league
        
        Args:
            league_id: Sleeper league ID
            week: Optional week number (defaults to current week)
            
        Returns:
            List of matchup dictionaries
        """
        url = f"{self.sleeper_api_base}/league/{league_id}/matchups/{week or ''}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            matchups = response.json()
            return matchups if isinstance(matchups, list) else []
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Sleeper matchups: {str(e)}")
    
    def get_sleeper_transactions(self, league_id: str, round_num: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transactions for a Sleeper league
        
        Args:
            league_id: Sleeper league ID
            round_num: Optional round number
            
        Returns:
            List of transaction dictionaries
        """
        url = f"{self.sleeper_api_base}/league/{league_id}/transactions"
        if round_num:
            url += f"/{round_num}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            transactions = response.json()
            return transactions if isinstance(transactions, list) else []
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Sleeper transactions: {str(e)}")
    
    def get_sleeper_injured_players(
        self,
        sport: str = "nfl",
        injury_status: Optional[str] = None,
        status: Optional[str] = None,
        has_team: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get injured/out players from Sleeper
        
        Args:
            sport: Sport abbreviation (default: 'nfl')
            injury_status: Filter by injury status - 'Out', 'Questionable', 'Doubtful', 'IR', 'PUP', etc. (optional)
            status: Filter by player status - 'Active', 'Injured Reserve', 'Inactive', 'Physically Unable to Perform', etc. (optional)
            has_team: Only include players with teams (default: True)
            
        Returns:
            List of player dictionaries with injury/status information
        """
        try:
            # Get all players
            all_players = self.get_sleeper_players(sport)
            
            injured_players = []
            
            for player_id, player_data in all_players.items():
                if not isinstance(player_data, dict):
                    continue
                
                # Get injury and status info
                player_injury_status = player_data.get("injury_status")
                player_status = player_data.get("status", "")
                team = player_data.get("team")
                
                # Filter by team if requested
                if has_team:
                    if not team or team == "None" or team is None:
                        continue
                
                # Filter by injury_status if specified
                if injury_status:
                    if player_injury_status != injury_status:
                        continue
                
                # Filter by status if specified
                if status:
                    if player_status != status:
                        continue
                
                # Include if has injury status (Out, Questionable, Doubtful, etc.) or non-Active status
                has_injury_info = (
                    player_injury_status or
                    player_data.get("injury_notes") or
                    player_data.get("injury_body_part") or
                    (player_status and player_status != "Active")
                )
                
                if not has_injury_info:
                    continue
                
                # Create enriched player data
                player_info = player_data.copy()
                player_info["player_id"] = player_id
                injured_players.append(player_info)
            
            return injured_players
        except Exception as e:
            raise Exception(f"Failed to fetch Sleeper injured players: {str(e)}")

