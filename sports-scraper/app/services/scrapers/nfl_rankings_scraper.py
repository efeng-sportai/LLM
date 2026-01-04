"""
NFL Rankings Scraper
Scrapes NFL team rankings (offense, defense, total)

API Used: Sleeper API
Data Source: Sleeper.app player stats aggregated by team
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
from ..apis.sleeper_api import SleeperAPI
from .base_scraper import BaseScraper


class NFLRankingsScraper(BaseScraper):
    """Scraper for NFL team rankings using Sleeper API"""
    
    def __init__(self):
        super().__init__()
        self.sleeper_api = SleeperAPI()
    
    def get_team_rankings(
        self,
        season: str = None,
        season_type: str = "regular",
        ranking_types: List[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get NFL team rankings
        
        Args:
            season: Season year
            season_type: Season type
            ranking_types: List of ranking types ['offense', 'defense', 'total']
        """
        if season is None:
            season = str(datetime.now().year)
        
        if ranking_types is None:
            ranking_types = ['offense', 'defense']
        
        try:
            results = {}
            
            if 'offense' in ranking_types:
                results['offense'] = self._get_offensive_rankings(season, season_type)
            
            if 'defense' in ranking_types:
                results['defense'] = self._get_defensive_rankings(season, season_type)
            
            return results
        except Exception as e:
            raise Exception(f"Failed to get team rankings: {str(e)}")
    
    def _get_offensive_rankings(self, season: str, season_type: str) -> List[Dict[str, Any]]:
        """Get offensive team rankings based on player stats"""
        try:
            # Get player stats
            stats = self.sleeper_api.get_player_stats("nfl", season, season_type)
            all_players = self.sleeper_api.get_all_players("nfl")
            
            # Aggregate offensive stats by team
            team_offense = defaultdict(lambda: {
                'team': '',
                'total_pass_yd': 0,
                'total_rush_yd': 0,
                'total_rec_yd': 0,
                'total_pass_td': 0,
                'total_rush_td': 0,
                'total_rec_td': 0,
                'total_offensive_yards': 0,
                'total_offensive_tds': 0,
                'player_count': 0
            })
            
            # Offensive positions
            offensive_positions = ['QB', 'RB', 'WR', 'TE', 'FB']
            
            for player_id, player_stats in stats.items():
                if player_id not in all_players:
                    continue
                
                player = all_players[player_id]
                position = player.get('position', '')
                team = player.get('team')
                
                if position not in offensive_positions or not team:
                    continue
                
                # Aggregate stats
                team_data = team_offense[team]
                team_data['team'] = team
                team_data['player_count'] += 1
                
                # Add yards
                team_data['total_pass_yd'] += int(player_stats.get('pass_yd', 0) or 0)
                team_data['total_rush_yd'] += int(player_stats.get('rush_yd', 0) or 0)
                team_data['total_rec_yd'] += int(player_stats.get('rec_yd', 0) or 0)
                
                # Add TDs
                team_data['total_pass_td'] += int(player_stats.get('pass_td', 0) or 0)
                team_data['total_rush_td'] += int(player_stats.get('rush_td', 0) or 0)
                team_data['total_rec_td'] += int(player_stats.get('rec_td', 0) or 0)
            
            # Calculate totals and sort
            rankings = []
            for team, data in team_offense.items():
                data['total_offensive_yards'] = (
                    data['total_pass_yd'] + 
                    data['total_rush_yd'] + 
                    data['total_rec_yd']
                )
                data['total_offensive_tds'] = (
                    data['total_pass_td'] + 
                    data['total_rush_td'] + 
                    data['total_rec_td']
                )
                rankings.append(data)
            
            # Sort by total offensive yards (descending)
            rankings.sort(key=lambda x: x['total_offensive_yards'], reverse=True)
            
            # Add rankings
            for i, team_data in enumerate(rankings, 1):
                team_data['rank'] = i
                team_data['ranking_type'] = 'offense'
            
            return rankings
        except Exception as e:
            raise Exception(f"Failed to get offensive rankings: {str(e)}")
    
    def _get_defensive_rankings(self, season: str, season_type: str) -> List[Dict[str, Any]]:
        """Get defensive team rankings based on player stats"""
        try:
            # Get player stats
            stats = self.sleeper_api.get_player_stats("nfl", season, season_type)
            all_players = self.sleeper_api.get_all_players("nfl")
            
            # Aggregate defensive stats by team
            team_defense = defaultdict(lambda: {
                'team': '',
                'total_sacks': 0,
                'total_int': 0,
                'total_def_td': 0,
                'total_fumbles_rec': 0,
                'total_defensive_points': 0,
                'player_count': 0
            })
            
            # Defensive positions
            defensive_positions = ['DEF', 'LB', 'CB', 'S', 'DT', 'DE', 'NT']
            
            for player_id, player_stats in stats.items():
                if player_id not in all_players:
                    continue
                
                player = all_players[player_id]
                position = player.get('position', '')
                team = player.get('team')
                
                if position not in defensive_positions or not team:
                    continue
                
                # Aggregate stats
                team_data = team_defense[team]
                team_data['team'] = team
                team_data['player_count'] += 1
                
                # Add defensive stats
                team_data['total_sacks'] += float(player_stats.get('sack', 0) or 0)
                team_data['total_int'] += int(player_stats.get('int', 0) or 0)
                team_data['total_def_td'] += int(player_stats.get('def_td', 0) or 0)
                team_data['total_fumbles_rec'] += int(player_stats.get('fum_rec', 0) or 0)
            
            # Calculate defensive points and sort
            rankings = []
            for team, data in team_defense.items():
                # Simple defensive scoring: sacks + ints*2 + def_tds*6 + fumbles*2
                data['total_defensive_points'] = (
                    data['total_sacks'] + 
                    (data['total_int'] * 2) + 
                    (data['total_def_td'] * 6) + 
                    (data['total_fumbles_rec'] * 2)
                )
                rankings.append(data)
            
            # Sort by defensive points (descending)
            rankings.sort(key=lambda x: x['total_defensive_points'], reverse=True)
            
            # Add rankings
            for i, team_data in enumerate(rankings, 1):
                team_data['rank'] = i
                team_data['ranking_type'] = 'defense'
            
            return rankings
        except Exception as e:
            raise Exception(f"Failed to get defensive rankings: {str(e)}")