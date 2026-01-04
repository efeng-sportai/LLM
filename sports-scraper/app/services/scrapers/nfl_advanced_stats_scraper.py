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
    
    def __init__(self, rate_limit_delay: float = 2.0):
        super().__init__()
        self.pfr_api = ProFootballReferenceAPI(rate_limit_delay=rate_limit_delay)
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
    
    def get_enhanced_player_season_stats(
        self,
        position: str = "QB",
        season: str = None,
        source: str = "pfr",
        include_advanced: bool = True,
        include_game_logs: bool = True,
        max_players: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get enhanced player season statistics with advanced metrics for ALL players
        
        Args:
            position: Player position (QB, RB, WR, TE, K)
            season: Season year (default: current year)
            source: Data source - 'pfr' or 'nfl' (default: 'pfr')
            include_advanced: Include advanced calculated metrics
            include_game_logs: Include per-game breakdowns
            max_players: Maximum number of players (None = ALL players)
        """
        if season is None:
            season = str(datetime.now().year)
        
        try:
            if source.lower() == "pfr" and include_advanced:
                # Use enhanced method with rate limiting for ALL players
                stats = self.pfr_api.get_enhanced_player_stats(
                    position=position, 
                    season=season, 
                    include_game_logs=include_game_logs,
                    max_players=max_players  # None = all players
                )
            elif source.lower() == "pfr":
                # Use basic method for all players
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
                    'data_type': 'comprehensive_player_stats' if include_game_logs else 'enhanced_player_season_stats',
                    'enhanced': include_advanced,
                    'includes_game_logs': include_game_logs,
                    'all_players_processed': max_players is None
                })
            
            return stats
        except Exception as e:
            raise Exception(f"Failed to get enhanced {position} season stats from {source}: {str(e)}")
    
    def get_players_with_actual_game_logs(
        self,
        position: str = "QB",
        season: str = None,
        source: str = "pfr",
        max_players: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get players with ACTUAL game-by-game logs (like the detailed format you showed)
        
        Args:
            position: Player position (QB, RB, WR, TE, K)
            season: Season year (default: current year)
            source: Data source - 'pfr' only for now
            max_players: Maximum number of players (None = ALL players)
        """
        if season is None:
            season = str(datetime.now().year)
        
        try:
            if source.lower() == "pfr":
                # Use the enhanced method that gets actual game logs
                stats = self.pfr_api.get_enhanced_player_with_game_logs(
                    position=position, 
                    season=season, 
                    max_players=max_players
                )
            else:
                raise ValueError(f"Game logs only supported for PFR source, got: {source}")
            
            # Enrich with metadata
            for stat in stats:
                stat.update({
                    'season': season,
                    'position': position,
                    'data_source': source,
                    'scraped_at': datetime.now().isoformat(),
                    'data_type': 'player_with_game_logs',
                    'has_actual_game_logs': stat.get('has_actual_game_logs', False),
                    'all_players_processed': max_players is None
                })
            
            return stats
        except Exception as e:
            raise Exception(f"Failed to get {position} players with game logs from {source}: {str(e)}")
    
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
        
        # Show all players, not just top 50
        display_limit = len(sorted_stats)  # Show all players
        
        for i, player_stats in enumerate(sorted_stats[:display_limit], 1):
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
        
    def format_enhanced_player_stats_for_training(
        self,
        stats: List[Dict[str, Any]],
        position: str,
        season: str
    ) -> str:
        """
        Format enhanced player season stats into training data response
        
        Args:
            stats: List of enhanced player stat dictionaries
            position: Player position
            season: Season year
        """
        if not stats:
            return f"No enhanced {position} season stats found for {season}."
        
        response_parts = []
        response_parts.append(f"Enhanced NFL {position} Season Statistics - {season}:\n")
        
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
        
        # Show all players
        display_limit = len(sorted_stats)
        
        for i, player_stats in enumerate(sorted_stats[:display_limit], 1):
            player_name = player_stats.get('player', 'Unknown')
            team = player_stats.get('team', 'N/A')
            
            response_parts.append(f"\n{i}. {player_name} ({team})")
            
            # Position-specific stats with enhanced metrics
            if position == "QB":
                stats_list = []
                # Basic stats
                if player_stats.get('cmp') and player_stats.get('att'):
                    completion_pct = player_stats.get('completion_pct', player_stats.get('cmppct', 0))
                    stats_list.append(f"{player_stats['cmp']}/{player_stats['att']} ({completion_pct}%)")
                if player_stats.get('yds'):
                    stats_list.append(f"{player_stats['yds']:,} yds")
                if player_stats.get('td'):
                    stats_list.append(f"{player_stats['td']} TD")
                if player_stats.get('int'):
                    stats_list.append(f"{player_stats['int']} INT")
                
                # Enhanced stats
                enhanced_stats = []
                if player_stats.get('yards_per_attempt'):
                    enhanced_stats.append(f"{player_stats['yards_per_attempt']} Y/A")
                if player_stats.get('yards_per_game'):
                    enhanced_stats.append(f"{player_stats['yards_per_game']} YPG")
                if player_stats.get('td_pct'):
                    enhanced_stats.append(f"{player_stats['td_pct']}% TD rate")
                
                if stats_list:
                    response_parts.append(f"   Basic: {', '.join(stats_list)}")
                if enhanced_stats:
                    response_parts.append(f"   Advanced: {', '.join(enhanced_stats)}")
            
            elif position == "RB":
                stats_list = []
                if player_stats.get('att'):
                    stats_list.append(f"{player_stats['att']} carries")
                if player_stats.get('yds'):
                    stats_list.append(f"{player_stats['yds']:,} yds")
                if player_stats.get('td'):
                    stats_list.append(f"{player_stats['td']} TD")
                
                # Enhanced stats
                enhanced_stats = []
                if player_stats.get('yards_per_carry'):
                    enhanced_stats.append(f"{player_stats['yards_per_carry']} YPC")
                if player_stats.get('yards_per_game'):
                    enhanced_stats.append(f"{player_stats['yards_per_game']} YPG")
                if player_stats.get('td_per_game'):
                    enhanced_stats.append(f"{player_stats['td_per_game']} TD/G")
                
                if stats_list:
                    response_parts.append(f"   Basic: {', '.join(stats_list)}")
                if enhanced_stats:
                    response_parts.append(f"   Advanced: {', '.join(enhanced_stats)}")
            
            elif position in ["WR", "TE"]:
                stats_list = []
                if player_stats.get('rec'):
                    stats_list.append(f"{player_stats['rec']} rec")
                if player_stats.get('yds'):
                    stats_list.append(f"{player_stats['yds']:,} yds")
                if player_stats.get('td'):
                    stats_list.append(f"{player_stats['td']} TD")
                
                # Enhanced stats
                enhanced_stats = []
                if player_stats.get('yards_per_reception'):
                    enhanced_stats.append(f"{player_stats['yards_per_reception']} YPR")
                if player_stats.get('rec_per_game'):
                    enhanced_stats.append(f"{player_stats['rec_per_game']} RPG")
                if player_stats.get('catch_pct'):
                    enhanced_stats.append(f"{player_stats['catch_pct']}% catch rate")
                
                if stats_list:
                    response_parts.append(f"   Basic: {', '.join(stats_list)}")
                if enhanced_stats:
                    response_parts.append(f"   Advanced: {', '.join(enhanced_stats)}")
            
            elif position == "K":
                stats_list = []
                if player_stats.get('fgm') and player_stats.get('fga'):
                    fg_pct = player_stats.get('fg_pct', (player_stats['fgm'] / player_stats['fga']) * 100 if player_stats['fga'] > 0 else 0)
                    stats_list.append(f"{player_stats['fgm']}/{player_stats['fga']} FG ({fg_pct:.1f}%)")
                if player_stats.get('xpm'):
                    stats_list.append(f"{player_stats['xpm']} XP")
                if player_stats.get('pts'):
                    stats_list.append(f"{player_stats['pts']} pts")
                
                # Enhanced stats
                enhanced_stats = []
                if player_stats.get('points_per_game'):
                    enhanced_stats.append(f"{player_stats['points_per_game']} PPG")
                if player_stats.get('xp_pct'):
                    enhanced_stats.append(f"{player_stats['xp_pct']}% XP rate")
                
                if stats_list:
                    response_parts.append(f"   Basic: {', '.join(stats_list)}")
                if enhanced_stats:
                    response_parts.append(f"   Advanced: {', '.join(enhanced_stats)}")
        
    def format_comprehensive_player_stats_for_training(
        self,
        stats: List[Dict[str, Any]],
        position: str,
        season: str
    ) -> str:
        """
        Format comprehensive player stats (season + per-game) into training data response
        
        Args:
            stats: List of comprehensive player stat dictionaries
            position: Player position
            season: Season year
        """
        if not stats:
            return f"No comprehensive {position} season stats found for {season}."
        
        response_parts = []
        response_parts.append(f"Comprehensive NFL {position} Statistics - {season} Season (ALL PLAYERS):\n")
        response_parts.append(f"Includes: Season totals, advanced metrics, per-game averages, and consistency scores\n")
        
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
        
        # Show ALL players
        for i, player_stats in enumerate(sorted_stats, 1):
            player_name = player_stats.get('player', 'Unknown')
            team = player_stats.get('team', 'N/A')
            games_played = player_stats.get('g', 0)
            
            response_parts.append(f"\n{i}. {player_name} ({team}) - {games_played} games")
            
            # Position-specific comprehensive stats
            if position == "QB":
                # Season totals
                season_stats = []
                if player_stats.get('cmp') and player_stats.get('att'):
                    completion_pct = player_stats.get('completion_pct', player_stats.get('cmppct', 0))
                    season_stats.append(f"{player_stats['cmp']}/{player_stats['att']} ({completion_pct}%)")
                if player_stats.get('yds'):
                    season_stats.append(f"{player_stats['yds']:,} yds")
                if player_stats.get('td'):
                    season_stats.append(f"{player_stats['td']} TD")
                if player_stats.get('int'):
                    season_stats.append(f"{player_stats['int']} INT")
                
                # Advanced metrics
                advanced_stats = []
                if player_stats.get('yards_per_attempt'):
                    advanced_stats.append(f"{player_stats['yards_per_attempt']} Y/A")
                if player_stats.get('td_pct'):
                    advanced_stats.append(f"{player_stats['td_pct']}% TD rate")
                if player_stats.get('int_pct'):
                    advanced_stats.append(f"{player_stats['int_pct']}% INT rate")
                
                # Per-game averages
                per_game_stats = []
                if player_stats.get('yards_per_game'):
                    per_game_stats.append(f"{player_stats['yards_per_game']} YPG")
                if player_stats.get('avg_yds_per_game'):
                    per_game_stats.append(f"{player_stats['avg_yds_per_game']} avg YPG")
                if player_stats.get('avg_attempts_per_game'):
                    per_game_stats.append(f"{player_stats['avg_attempts_per_game']} att/G")
                
                # Consistency
                consistency_stats = []
                if player_stats.get('season_consistency_score'):
                    consistency_stats.append(f"{player_stats['season_consistency_score']} consistency")
                if player_stats.get('total_games_analyzed'):
                    consistency_stats.append(f"{player_stats['total_games_analyzed']} games analyzed")
                
                if season_stats:
                    response_parts.append(f"   Season: {', '.join(season_stats)}")
                if advanced_stats:
                    response_parts.append(f"   Advanced: {', '.join(advanced_stats)}")
                if per_game_stats:
                    response_parts.append(f"   Per-Game: {', '.join(per_game_stats)}")
                if consistency_stats:
                    response_parts.append(f"   Consistency: {', '.join(consistency_stats)}")
            
            elif position == "RB":
                # Season totals
                season_stats = []
                if player_stats.get('att'):
                    season_stats.append(f"{player_stats['att']} carries")
                if player_stats.get('yds'):
                    season_stats.append(f"{player_stats['yds']:,} yds")
                if player_stats.get('td'):
                    season_stats.append(f"{player_stats['td']} TD")
                
                # Advanced metrics
                advanced_stats = []
                if player_stats.get('yards_per_carry'):
                    advanced_stats.append(f"{player_stats['yards_per_carry']} YPC")
                if player_stats.get('td_per_carry'):
                    advanced_stats.append(f"{player_stats['td_per_carry']} TD/carry")
                
                # Per-game averages
                per_game_stats = []
                if player_stats.get('yards_per_game'):
                    per_game_stats.append(f"{player_stats['yards_per_game']} YPG")
                if player_stats.get('avg_carries_per_game'):
                    per_game_stats.append(f"{player_stats['avg_carries_per_game']} carries/G")
                if player_stats.get('td_per_game'):
                    per_game_stats.append(f"{player_stats['td_per_game']} TD/G")
                
                # Consistency
                consistency_stats = []
                if player_stats.get('season_consistency_score'):
                    consistency_stats.append(f"{player_stats['season_consistency_score']} consistency")
                
                if season_stats:
                    response_parts.append(f"   Season: {', '.join(season_stats)}")
                if advanced_stats:
                    response_parts.append(f"   Advanced: {', '.join(advanced_stats)}")
                if per_game_stats:
                    response_parts.append(f"   Per-Game: {', '.join(per_game_stats)}")
                if consistency_stats:
                    response_parts.append(f"   Consistency: {', '.join(consistency_stats)}")
            
            elif position in ["WR", "TE"]:
                # Season totals
                season_stats = []
                if player_stats.get('rec'):
                    season_stats.append(f"{player_stats['rec']} rec")
                if player_stats.get('yds'):
                    season_stats.append(f"{player_stats['yds']:,} yds")
                if player_stats.get('td'):
                    season_stats.append(f"{player_stats['td']} TD")
                
                # Advanced metrics
                advanced_stats = []
                if player_stats.get('yards_per_reception'):
                    advanced_stats.append(f"{player_stats['yards_per_reception']} YPR")
                if player_stats.get('catch_pct'):
                    advanced_stats.append(f"{player_stats['catch_pct']}% catch rate")
                if player_stats.get('td_per_reception'):
                    advanced_stats.append(f"{player_stats['td_per_reception']} TD/rec")
                
                # Per-game averages
                per_game_stats = []
                if player_stats.get('rec_per_game'):
                    per_game_stats.append(f"{player_stats['rec_per_game']} RPG")
                if player_stats.get('yards_per_game'):
                    per_game_stats.append(f"{player_stats['yards_per_game']} YPG")
                if player_stats.get('avg_receptions_per_game'):
                    per_game_stats.append(f"{player_stats['avg_receptions_per_game']} avg RPG")
                
                # Consistency
                consistency_stats = []
                if player_stats.get('season_consistency_score'):
                    consistency_stats.append(f"{player_stats['season_consistency_score']} consistency")
                
                if season_stats:
                    response_parts.append(f"   Season: {', '.join(season_stats)}")
                if advanced_stats:
                    response_parts.append(f"   Advanced: {', '.join(advanced_stats)}")
                if per_game_stats:
                    response_parts.append(f"   Per-Game: {', '.join(per_game_stats)}")
                if consistency_stats:
                    response_parts.append(f"   Consistency: {', '.join(consistency_stats)}")
            
            elif position == "K":
                # Season totals
                season_stats = []
                if player_stats.get('fgm') and player_stats.get('fga'):
                    fg_pct = player_stats.get('fg_pct', (player_stats['fgm'] / player_stats['fga']) * 100 if player_stats['fga'] > 0 else 0)
                    season_stats.append(f"{player_stats['fgm']}/{player_stats['fga']} FG ({fg_pct:.1f}%)")
                if player_stats.get('xpm'):
                    season_stats.append(f"{player_stats['xpm']} XP")
                if player_stats.get('pts'):
                    season_stats.append(f"{player_stats['pts']} pts")
                
                # Per-game averages
                per_game_stats = []
                if player_stats.get('points_per_game'):
                    per_game_stats.append(f"{player_stats['points_per_game']} PPG")
                
                if season_stats:
                    response_parts.append(f"   Season: {', '.join(season_stats)}")
                if per_game_stats:
                    response_parts.append(f"   Per-Game: {', '.join(per_game_stats)}")
        
    def format_player_game_logs_for_training(
        self,
        stats: List[Dict[str, Any]],
        position: str,
        season: str
    ) -> str:
        """
        Format player game logs in the detailed format (Date, Team, Opp, Result, detailed stats per game)
        
        Args:
            stats: List of player dictionaries with game logs
            position: Player position
            season: Season year
        """
        if not stats:
            return f"No {position} players with game logs found for {season}."
        
        response_parts = []
        response_parts.append(f"NFL {position} Game-by-Game Logs - {season} Season:\n")
        response_parts.append(f"Format: Date | Team | Opp | Result | Detailed Game Stats\n")
        
        # Sort by total yards (or relevant stat)
        if position == "QB":
            sorted_stats = sorted(stats, key=lambda x: x.get('yds', 0), reverse=True)
        elif position == "RB":
            sorted_stats = sorted(stats, key=lambda x: x.get('yds', 0), reverse=True)
        elif position in ["WR", "TE"]:
            sorted_stats = sorted(stats, key=lambda x: x.get('yds', 0), reverse=True)
        else:
            sorted_stats = stats
        
        players_with_logs = [p for p in sorted_stats if p.get('game_logs')]
        
        for i, player_stats in enumerate(players_with_logs, 1):
            player_name = player_stats.get('player', 'Unknown')
            team = player_stats.get('team', 'N/A')
            game_logs = player_stats.get('game_logs', [])
            
            if not game_logs:
                continue
            
            response_parts.append(f"\n{i}. {player_name} ({team}) - {len(game_logs)} games logged:")
            
            # Season summary first
            season_summary = []
            if player_stats.get('yds'):
                season_summary.append(f"{player_stats['yds']:,} total yds")
            if player_stats.get('td'):
                season_summary.append(f"{player_stats['td']} total TD")
            if player_stats.get('g'):
                season_summary.append(f"{player_stats['g']} games")
            
            if season_summary:
                response_parts.append(f"   Season: {', '.join(season_summary)}")
            
            # Game-by-game logs in detailed format
            response_parts.append("   Game Logs:")
            
            for game in game_logs[:16]:  # Show up to 16 games (regular season)
                game_line = self._format_single_game_log(game, position)
                if game_line:
                    response_parts.append(f"     {game_line}")
            
            # Add per-game averages if available
            if player_stats.get('has_actual_game_logs'):
                avg_stats = []
                if player_stats.get('avg_yds_per_game'):
                    avg_stats.append(f"{player_stats['avg_yds_per_game']} YPG")
                if player_stats.get('avg_td_per_game'):
                    avg_stats.append(f"{player_stats['avg_td_per_game']} TD/G")
                
                if avg_stats:
                    response_parts.append(f"   Averages: {', '.join(avg_stats)}")
            
            # Add consistency scores
            consistency_stats = []
            if player_stats.get('yds_consistency'):
                consistency_stats.append(f"Yards consistency: {player_stats['yds_consistency']}")
            if player_stats.get('td_consistency'):
                consistency_stats.append(f"TD consistency: {player_stats['td_consistency']}")
            
            if consistency_stats:
                response_parts.append(f"   Consistency: {', '.join(consistency_stats)}")
        
        response_parts.append(f"\nTotal players with game logs: {len(players_with_logs)}")
        response_parts.append(f"Total players processed: {len(stats)}")
        response_parts.append(f"Source: Pro Football Reference Game Logs")
        return "\n".join(response_parts)
    
    def _format_single_game_log(self, game: Dict[str, Any], position: str) -> str:
        """Format a single game log entry in the detailed format"""
        try:
            # Extract basic game info
            date = game.get('date', 'N/A')
            team = game.get('tm', game.get('team', 'N/A'))
            opp = game.get('opp', 'N/A')
            result = game.get('result', 'N/A')
            
            # Position-specific stats formatting
            if position == "QB":
                # QB format: Date | Team | Opp | Result | Passing stats | Rushing stats
                # Passing stats
                pass_att = game.get('passing_att', 0)
                pass_cmp = game.get('passing_cmp', 0)
                pass_yds = game.get('passing_yds', 0)
                pass_td = game.get('passing_td', 0)
                pass_int = game.get('passing_int', 0)
                pass_lng = game.get('passing_lng', 0)
                pass_ya = round(pass_yds / pass_att, 1) if pass_att > 0 else 0.0
                
                # Rushing stats
                rush_att = game.get('rushing_att', 0)
                rush_yds = game.get('rushing_yds', 0)
                rush_td = game.get('rushing_td', 0)
                rush_lng = game.get('rushing_lng', 0)
                
                return f"{date} | {team} | {opp} | {result} | {pass_cmp}/{pass_att} | {pass_yds} yds | {pass_td} TD | {pass_int} INT | {pass_ya} Y/A | {rush_att} rush | {rush_yds} rush yds | {rush_td} rush TD"
            
            elif position == "RB":
                # RB format: Date | Team | Opp | Result | Rushing stats | Receiving stats
                # Rushing stats
                rush_att = game.get('rushing_att', 0)
                rush_yds = game.get('rushing_yds', 0)
                rush_td = game.get('rushing_td', 0)
                rush_lng = game.get('rushing_lng', 0)
                rush_ya = round(rush_yds / rush_att, 1) if rush_att > 0 else 0.0
                
                # Receiving stats
                rec_tgt = game.get('receiving_tgt', 0)
                rec_rec = game.get('receiving_rec', 0)
                rec_yds = game.get('receiving_yds', 0)
                rec_td = game.get('receiving_td', 0)
                rec_lng = game.get('receiving_lng', 0)
                
                return f"{date} | {team} | {opp} | {result} | {rush_att} att | {rush_yds} yds | {rush_td} TD | {rush_lng} lng | {rush_ya} Y/A | {rec_tgt} tgt | {rec_rec} rec | {rec_yds} rec yds | {rec_td} rec TD"
            
            elif position in ["WR", "TE"]:
                # WR/TE format: Date | Team | Opp | Result | Receiving stats
                rec_tgt = game.get('receiving_tgt', 0)
                rec_rec = game.get('receiving_rec', 0)
                rec_yds = game.get('receiving_yds', 0)
                rec_td = game.get('receiving_td', 0)
                rec_lng = game.get('receiving_lng', 0)
                rec_yr = round(rec_yds / rec_rec, 1) if rec_rec > 0 else 0.0
                catch_pct = round((rec_rec / rec_tgt) * 100, 1) if rec_tgt > 0 else 0.0
                y_tgt = round(rec_yds / rec_tgt, 1) if rec_tgt > 0 else 0.0
                
                return f"{date} | {team} | {opp} | {result} | {rec_tgt} tgt | {rec_rec} rec | {rec_yds} yds | {rec_yr} Y/R | {rec_td} TD | {rec_lng} lng | {catch_pct}% | {y_tgt} Y/Tgt"
            
            else:
                # Generic format
                return f"{date} | {team} | {opp} | {result} | Basic stats available"
        
        except Exception as e:
            return f"Error formatting game log: {e}"