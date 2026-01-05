"""
NFL Game Logs Scraper
Uses Pro Football Reference API to get individual player game logs
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from .base_scraper import BaseScraper
from ..apis.pro_football_reference_api import ProFootballReferenceAPI


class NFLGameLogsScraper(BaseScraper):
    """Scraper for NFL player game logs using Pro Football Reference API"""
    
    def __init__(self):
        super().__init__()
        self.pfr_api = ProFootballReferenceAPI()
    
    def get_player_game_logs(
        self,
        player_id: str,
        season: str = None,
        source: str = "pfr"
    ) -> List[Dict[str, Any]]:
        """
        Get individual game logs for a player
        
        Args:
            player_id: Player ID (format depends on source)
            season: Season year (default: current year)
            source: Data source - 'pfr' only (default: 'pfr')
        """
        if season is None:
            season = str(datetime.now().year)
        
        try:
            if source.lower() == "pfr":
                game_logs = self.pfr_api.get_player_game_log(player_id, season)
            else:
                raise ValueError(f"Unsupported source: {source}. Only 'pfr' is supported.")
            
            # Enrich with metadata
            for game_log in game_logs:
                game_log.update({
                    'season': season,
                    'data_source': source,
                    'scraped_at': datetime.now().isoformat(),
                    'data_type': 'game_log'
                })
            
            return game_logs
        except Exception as e:
            raise Exception(f"Failed to get game logs for player {player_id} from {source}: {str(e)}")
    
    def get_multiple_player_game_logs(
        self,
        player_ids: List[str],
        season: str = None,
        source: str = "pfr"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get game logs for multiple players
        
        Args:
            player_ids: List of player IDs
            season: Season year (default: current year)
            source: Data source - 'pfr' only (default: 'pfr')
        """
        if season is None:
            season = str(datetime.now().year)
        
        all_game_logs = {}
        
        for player_id in player_ids:
            try:
                game_logs = self.get_player_game_logs(player_id, season, source)
                all_game_logs[player_id] = game_logs
            except Exception as e:
                print(f"Warning: Failed to get game logs for player {player_id}: {str(e)}")
                all_game_logs[player_id] = []
        
        return all_game_logs
    
    def get_top_performers_game_logs(
        self,
        position: str = "QB",
        season: str = None,
        source: str = "pfr",
        limit: int = 20
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get game logs for top performers at a position
        
        Args:
            position: Player position (QB, RB, WR, TE, K)
            season: Season year (default: current year)
            source: Data source - 'pfr' only (default: 'pfr')
            limit: Number of top players to get logs for
        """
        raise NotImplementedError("Top performers game logs requires integration with player ranking systems. Use get_player_game_logs for specific players instead.")
    
    def get_recent_game_logs(
        self,
        weeks_back: int = 4,
        season: str = None,
        source: str = "pfr"
    ) -> List[Dict[str, Any]]:
        """
        Get recent game logs across all players
        
        Args:
            weeks_back: Number of weeks to look back
            season: Season year (default: current year)
            source: Data source - 'pfr' only (default: 'pfr')
        """
        raise NotImplementedError("Recent game logs requires integration with schedule/week detection systems. Use get_player_game_logs for specific players instead.")
    
    def format_game_logs_for_training(
        self,
        game_logs: List[Dict[str, Any]],
        player_name: str,
        position: str
    ) -> str:
        """
        Format game logs into training data response
        
        Args:
            game_logs: List of game log dictionaries
            player_name: Player name
            position: Player position
        """
        if not game_logs:
            return f"No game logs found for {player_name} ({position})."
        
        response_parts = []
        response_parts.append(f"{player_name} ({position}) - Game Log:\n")
        
        # Sort by date if available
        sorted_logs = sorted(
            game_logs,
            key=lambda x: x.get('date', ''),
            reverse=True
        )
        
        for i, game in enumerate(sorted_logs, 1):
            game_info = []
            
            # Basic game info
            if game.get('date'):
                game_info.append(f"Date: {game['date']}")
            if game.get('opp'):
                game_info.append(f"vs {game['opp']}")
            
            response_parts.append(f"\nGame {i}: {', '.join(game_info)}")
            
            # Position-specific stats
            if position == "QB":
                stats = []
                if game.get('pass_cmp') and game.get('pass_att'):
                    stats.append(f"{game['pass_cmp']}/{game['pass_att']} passing")
                if game.get('pass_yds'):
                    stats.append(f"{game['pass_yds']} pass yds")
                if game.get('pass_td'):
                    stats.append(f"{game['pass_td']} pass TD")
                if game.get('int'):
                    stats.append(f"{game['int']} INT")
                if stats:
                    response_parts.append(f"  Stats: {', '.join(stats)}")
            
            elif position in ["RB", "WR", "TE"]:
                stats = []
                if game.get('rush_att'):
                    stats.append(f"{game['rush_att']} carries")
                if game.get('rush_yds'):
                    stats.append(f"{game['rush_yds']} rush yds")
                if game.get('rush_td'):
                    stats.append(f"{game['rush_td']} rush TD")
                if game.get('rec'):
                    stats.append(f"{game['rec']} rec")
                if game.get('rec_yds'):
                    stats.append(f"{game['rec_yds']} rec yds")
                if game.get('rec_td'):
                    stats.append(f"{game['rec_td']} rec TD")
                if stats:
                    response_parts.append(f"  Stats: {', '.join(stats)}")
            
            elif position == "K":
                stats = []
                if game.get('fg_made') and game.get('fg_att'):
                    stats.append(f"{game['fg_made']}/{game['fg_att']} FG")
                if game.get('xp_made') and game.get('xp_att'):
                    stats.append(f"{game['xp_made']}/{game['xp_att']} XP")
                if stats:
                    response_parts.append(f"  Stats: {', '.join(stats)}")
            
            # Fantasy points if available
            if game.get('fantasy_points'):
                response_parts.append(f"  Fantasy Points: {game['fantasy_points']}")
        
        response_parts.append(f"\nTotal games: {len(game_logs)}")
        return "\n".join(response_parts)