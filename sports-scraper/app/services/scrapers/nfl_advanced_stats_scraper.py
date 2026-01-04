"""
NFL Advanced Stats Scraper
Uses Pro Football Reference API and NFL.com API to get advanced team and player statistics
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from .base_scraper import BaseScraper
from ..apis.pro_football_reference_api import ProFootballReferenceAPI
from ..apis.nfl_com_api import NFLComAPI


class NFLAdvancedStatsScraper(BaseScraper):
    """Scraper for NFL advanced statistics using Pro Football Reference API and NFL.com API"""
    
    def __init__(self):
        super().__init__()
        self.pfr_api = ProFootballReferenceAPI()
        self.nfl_api = NFLComAPI()
    
    def get_team_advanced_stats(
        self,
        season: str = None,
        source: str = "pfr"
    ) -> List[Dict[str, Any]]:
        """
        Get advanced team statistics
        
        Args:
            season: Season year (default: current year)
            source: Data source - 'pfr' or 'nfl' (default: 'pfr')
        """
        if season is None:
            season = str(datetime.now().year)
        
        try:
            if source.lower() == "pfr":
                stats = self.pfr_api.get_team_advanced_stats(season)
            elif source.lower() == "nfl":
                # Get multiple stat categories from NFL.com
                offense_stats = self.nfl_api.get_team_stats("offense", season)
                defense_stats = self.nfl_api.get_team_stats("defense", season)
                special_teams_stats = self.nfl_api.get_team_stats("special_teams", season)
                
                # Combine all stats
                stats = offense_stats + defense_stats + special_teams_stats
            else:
                raise ValueError(f"Unsupported source: {source}")
            
            # Enrich with metadata
            for stat in stats:
                stat.update({
                    'season': season,
                    'data_source': source,
                    'scraped_at': datetime.now().isoformat(),
                    'data_type': 'team_advanced_stats'
                })
            
            return stats
        except Exception as e:
            raise Exception(f"Failed to get team advanced stats from {source}: {str(e)}")
    
    def get_player_season_stats(
        self,
        position: str = "QB",
        season: str = None,
        source: str = "pfr"
    ) -> List[Dict[str, Any]]:
        """
        Get player season statistics by position
        
        Args:
            position: Player position (QB, RB, WR, TE, K, DEF)
            season: Season year (default: current year)
            source: Data source - 'pfr' or 'nfl' (default: 'pfr')
        """
        if season is None:
            season = str(datetime.now().year)
        
        try:
            if source.lower() == "pfr":
                stats = self.pfr_api.get_player_season_stats(position, season)
            elif source.lower() == "nfl":
                stats = self.nfl_api.get_player_stats(position, season)
            else:
                raise ValueError(f"Unsupported source: {source}")
            
            # Enrich with metadata
            for stat in stats:
                stat.update({
                    'season': season,
                    'position': position,
                    'data_source': source,
                    'scraped_at': datetime.now().isoformat(),
                    'data_type': 'player_season_stats'
                })
            
            return stats
        except Exception as e:
            raise Exception(f"Failed to get {position} season stats from {source}: {str(e)}")
    
    def get_all_position_stats(
        self,
        season: str = None,
        source: str = "pfr"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get season stats for all major positions
        
        Args:
            season: Season year (default: current year)
            source: Data source - 'pfr' or 'nfl' (default: 'pfr')
        """
        if season is None:
            season = str(datetime.now().year)
        
        positions = ["QB", "RB", "WR", "TE", "K"]
        all_stats = {}
        
        for position in positions:
            try:
                stats = self.get_player_season_stats(position, season, source)
                all_stats[position] = stats
            except Exception as e:
                print(f"Warning: Failed to get {position} stats: {str(e)}")
                all_stats[position] = []
        
        return all_stats
    
    def get_weekly_matchups(
        self,
        season: str = None,
        week: int = 1,
        source: str = "pfr"
    ) -> List[Dict[str, Any]]:
        """
        Get weekly matchup data with advanced metrics
        
        Args:
            season: Season year (default: current year)
            week: Week number (default: 1)
            source: Data source - 'pfr' (default: 'pfr')
        """
        if season is None:
            season = str(datetime.now().year)
        
        try:
            if source.lower() == "pfr":
                matchups = self.pfr_api.get_weekly_matchups(season, week)
            else:
                raise ValueError(f"Unsupported source: {source}")
            
            # Enrich with metadata
            for matchup in matchups:
                matchup.update({
                    'season': season,
                    'week': week,
                    'data_source': source,
                    'scraped_at': datetime.now().isoformat(),
                    'data_type': 'weekly_matchup'
                })
            
            return matchups
        except Exception as e:
            raise Exception(f"Failed to get week {week} matchups from {source}: {str(e)}")
    
    def format_team_advanced_stats_for_training(
        self,
        stats: List[Dict[str, Any]],
        season: str
    ) -> str:
        """
        Format team advanced stats into training data response
        
        Args:
            stats: List of team stat dictionaries
            season: Season year
        """
        if not stats:
            return f"No advanced team stats found for {season} season."
        
        response_parts = []
        response_parts.append(f"NFL Team Advanced Statistics - {season} Season:\n")
        
        # Sort by team name
        sorted_stats = sorted(stats, key=lambda x: x.get('team', x.get('tm', '')))
        
        for i, team_stats in enumerate(sorted_stats, 1):
            team_name = team_stats.get('team', team_stats.get('tm', 'Unknown'))
            response_parts.append(f"\n{i}. {team_name}")
            
            # Key stats from PFR data
            stats_list = []
            
            # Games played
            if team_stats.get('g'):
                stats_list.append(f"Games: {team_stats['g']}")
            
            # Total yards (offensive)
            if team_stats.get('yds'):
                stats_list.append(f"Total Yds: {team_stats['yds']:,}")
            
            # Points allowed (defensive)
            if team_stats.get('pa'):
                stats_list.append(f"Points Allowed: {team_stats['pa']}")
            
            # Plays
            if team_stats.get('ply'):
                stats_list.append(f"Plays: {team_stats['ply']:,}")
            
            # Yards per play
            if team_stats.get('y_p'):
                stats_list.append(f"Yds/Play: {team_stats['y_p']}")
            
            # Turnovers
            if team_stats.get('to'):
                stats_list.append(f"Turnovers: {team_stats['to']}")
            
            # Touchdowns
            if team_stats.get('td'):
                stats_list.append(f"TDs: {team_stats['td']}")
            
            # Interceptions
            if team_stats.get('int'):
                stats_list.append(f"INTs: {team_stats['int']}")
            
            if stats_list:
                response_parts.append(f"   {', '.join(stats_list[:6])}")  # Show top 6 stats
            
            # Additional advanced metrics
            advanced_stats = []
            if team_stats.get('scpct'):
                advanced_stats.append(f"Score %: {team_stats['scpct']}")
            if team_stats.get('topct'):
                advanced_stats.append(f"TO %: {team_stats['topct']}")
            if team_stats.get('exp'):
                advanced_stats.append(f"Expected: {team_stats['exp']}")
            
            if advanced_stats:
                response_parts.append(f"   Advanced: {', '.join(advanced_stats)}")
        
        response_parts.append(f"\nTotal teams: {len(stats)}")
        response_parts.append(f"Source: Pro Football Reference")
        return "\n".join(response_parts)
    
    def format_player_season_stats_for_training(
        self,
        stats: List[Dict[str, Any]],
        position: str,
        season: str
    ) -> str:
        """
        Format player season stats into training data response
        
        Args:
            stats: List of player stat dictionaries
            position: Player position
            season: Season year
        """
        if not stats:
            return f"No {position} season stats found for {season}."
        
        response_parts = []
        response_parts.append(f"NFL {position} Season Statistics - {season}:\n")
        
        # Sort by relevant stat (position-dependent)
        if position == "QB":
            sorted_stats = sorted(stats, key=lambda x: x.get('yds', 0), reverse=True)
        elif position == "RB":
            sorted_stats = sorted(stats, key=lambda x: x.get('yds', 0), reverse=True)
        elif position in ["WR", "TE"]:
            sorted_stats = sorted(stats, key=lambda x: x.get('yds', 0), reverse=True)
        elif position == "K":
            sorted_stats = sorted(stats, key=lambda x: x.get('pts', 0), reverse=True)
        else:
            sorted_stats = stats
        
        for i, player_stats in enumerate(sorted_stats[:50], 1):  # Top 50
            player_name = player_stats.get('player', 'Unknown')
            team = player_stats.get('team', 'N/A')
            
            response_parts.append(f"\n{i}. {player_name} ({team})")
            
            # Position-specific stats using actual PFR field names
            if position == "QB":
                stats_list = []
                if player_stats.get('cmp') and player_stats.get('att'):
                    completion_pct = player_stats.get('cmppct', 0)
                    stats_list.append(f"{player_stats['cmp']}/{player_stats['att']} ({completion_pct}%)")
                if player_stats.get('yds'):
                    stats_list.append(f"{player_stats['yds']:,} yds")
                if player_stats.get('td'):
                    stats_list.append(f"{player_stats['td']} TD")
                if player_stats.get('int'):
                    stats_list.append(f"{player_stats['int']} INT")
                if player_stats.get('rate'):
                    stats_list.append(f"{player_stats['rate']} rating")
                if stats_list:
                    response_parts.append(f"   {', '.join(stats_list)}")
            
            elif position == "RB":
                stats_list = []
                if player_stats.get('att'):
                    stats_list.append(f"{player_stats['att']} carries")
                if player_stats.get('yds'):
                    stats_list.append(f"{player_stats['yds']:,} yds")
                if player_stats.get('td'):
                    stats_list.append(f"{player_stats['td']} TD")
                if player_stats.get('y/a'):
                    stats_list.append(f"{player_stats['y/a']} YPC")
                if stats_list:
                    response_parts.append(f"   {', '.join(stats_list)}")
            
            elif position in ["WR", "TE"]:
                stats_list = []
                if player_stats.get('rec'):
                    stats_list.append(f"{player_stats['rec']} rec")
                if player_stats.get('yds'):
                    stats_list.append(f"{player_stats['yds']:,} yds")
                if player_stats.get('td'):
                    stats_list.append(f"{player_stats['td']} TD")
                if player_stats.get('y/r'):
                    stats_list.append(f"{player_stats['y/r']} YPR")
                if stats_list:
                    response_parts.append(f"   {', '.join(stats_list)}")
            
            elif position == "K":
                stats_list = []
                if player_stats.get('fgm') and player_stats.get('fga'):
                    fg_pct = (player_stats['fgm'] / player_stats['fga']) * 100 if player_stats['fga'] > 0 else 0
                    stats_list.append(f"{player_stats['fgm']}/{player_stats['fga']} FG ({fg_pct:.1f}%)")
                if player_stats.get('xpm'):
                    stats_list.append(f"{player_stats['xpm']} XP")
                if player_stats.get('pts'):
                    stats_list.append(f"{player_stats['pts']} pts")
                if stats_list:
                    response_parts.append(f"   {', '.join(stats_list)}")
        
        response_parts.append(f"\nTotal players: {len(stats)}")
        response_parts.append(f"Source: Pro Football Reference")
        return "\n".join(response_parts)