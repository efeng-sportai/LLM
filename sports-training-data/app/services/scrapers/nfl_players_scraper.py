"""
NFL Players Scraper
Scrapes NFL player data, rankings, and statistics

API Used: Sleeper API
Data Source: Sleeper.app player and stats endpoints
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from ..apis.sleeper_api import SleeperAPI
from .base_scraper import BaseScraper


class NFLPlayersScraper(BaseScraper):
    """Scraper for NFL player data using Sleeper API"""
    
    def __init__(self):
        super().__init__()
        self.sleeper_api = SleeperAPI()
    
    def get_all_players(self) -> Dict[str, Any]:
        """Get all NFL players"""
        try:
            return self.sleeper_api.get_all_players("nfl")
        except Exception as e:
            raise Exception(f"Failed to get NFL players: {str(e)}")
    
    def get_trending_players(
        self,
        trend_type: str = "add",
        lookback_hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get trending NFL players
        
        Args:
            trend_type: 'add' or 'drop'
            lookback_hours: Hours to look back
            limit: Max number of players
        """
        try:
            # Get trending data
            trending = self.sleeper_api.get_trending_players(
                "nfl", trend_type, lookback_hours, limit
            )
            
            # Get all players to enrich data
            all_players = self.get_all_players()
            
            # Enrich trending data
            enriched_players = []
            for trend_item in trending:
                player_id = trend_item.get("player_id")
                count = trend_item.get("count", 0)
                
                if player_id and player_id in all_players:
                    player_data = all_players[player_id].copy()
                    player_data["trend_count"] = count
                    player_data["trend_type"] = trend_type
                    player_data["player_id"] = player_id
                    enriched_players.append(player_data)
            
            return enriched_players
        except Exception as e:
            raise Exception(f"Failed to get trending players: {str(e)}")
    
    def get_top_players_by_stats(
        self,
        position: Optional[str] = None,
        stat_key: str = "pts_half_ppr",
        limit: int = 100,
        season: str = None,
        season_type: str = "regular"
    ) -> List[Dict[str, Any]]:
        """
        Get top NFL players by statistics
        
        Args:
            position: Filter by position (QB, RB, WR, TE, etc.)
            stat_key: Stat to sort by (pts_half_ppr, pts_ppr, pts_std, etc.)
            limit: Max number of players
            season: Season year
            season_type: Season type
        """
        if season is None:
            season = str(datetime.now().year)
        
        try:
            # Get player stats
            stats = self.sleeper_api.get_player_stats("nfl", season, season_type)
            
            # Get all players
            all_players = self.get_all_players()
            
            # Combine and filter
            players_with_stats = []
            for player_id, player_stats in stats.items():
                if player_id not in all_players:
                    continue
                
                player_data = all_players[player_id].copy()
                
                # Filter by position
                if position and player_data.get("position") != position:
                    continue
                
                # Filter active players with teams (except team defenses)
                is_team_defense = position == "DEF" or player_data.get("position") == "DEF"
                
                if not is_team_defense:
                    status = player_data.get("status", "").upper()
                    team = player_data.get("team")
                    has_team = team and team != "None" and team is not None
                    
                    if status != "ACTIVE" or not has_team:
                        continue
                else:
                    # For team defenses, just check they have a team
                    team = player_data.get("team")
                    has_team = team and team != "None" and team is not None
                    if not has_team:
                        continue
                
                # Get stat value
                stat_value = player_stats.get(stat_key, 0)
                if stat_value is None:
                    stat_value = 0
                else:
                    try:
                        stat_value = float(stat_value)
                    except (ValueError, TypeError):
                        stat_value = 0
                
                # Try alternative stats for team defenses if needed
                if stat_value == 0 and is_team_defense:
                    alt_keys = ["pts_std", "pts_half_ppr", "pts_ppr", "def_td", "def_st_td"]
                    for alt_key in alt_keys:
                        alt_value = player_stats.get(alt_key, 0)
                        if alt_value:
                            try:
                                stat_value = float(alt_value)
                                if stat_value > 0:
                                    break
                            except (ValueError, TypeError):
                                continue
                
                if stat_value <= 0:
                    continue
                
                # Add to results
                player_data["stats"] = player_stats
                player_data["stat_value"] = stat_value
                player_data["player_id"] = player_id
                players_with_stats.append(player_data)
            
            # Sort by stat value (descending)
            players_with_stats.sort(key=lambda x: float(x.get("stat_value", 0)), reverse=True)
            
            return players_with_stats[:limit]
        except Exception as e:
            raise Exception(f"Failed to get top players by stats: {str(e)}")
    
    def get_injured_players(
        self,
        injury_status: Optional[str] = None,
        status: Optional[str] = None,
        has_team: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get injured/out NFL players
        
        Args:
            injury_status: Filter by injury status
            status: Filter by player status
            has_team: Only include players with teams
        """
        try:
            all_players = self.get_all_players()
            injured_players = []
            
            for player_id, player_data in all_players.items():
                if not isinstance(player_data, dict):
                    continue
                
                # Get injury and status info
                player_injury_status = player_data.get("injury_status")
                player_status = player_data.get("status", "")
                team = player_data.get("team")
                
                # Filter by team
                if has_team and (not team or team == "None" or team is None):
                    continue
                
                # Filter by injury_status
                if injury_status and player_injury_status != injury_status:
                    continue
                
                # Filter by status
                if status and player_status != status:
                    continue
                
                # Include if has injury info or non-Active status
                has_injury_info = (
                    player_injury_status or
                    player_data.get("injury_notes") or
                    player_data.get("injury_body_part") or
                    (player_status and player_status != "Active")
                )
                
                if not has_injury_info:
                    continue
                
                player_info = player_data.copy()
                player_info["player_id"] = player_id
                injured_players.append(player_info)
            
            return injured_players
        except Exception as e:
            raise Exception(f"Failed to get injured players: {str(e)}")