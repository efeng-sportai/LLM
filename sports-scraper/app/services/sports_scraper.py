"""
Sports Scraper Service
Main service that coordinates all sports data scraping using organized APIs and scrapers

Architecture:
- APIs: Pure API clients (sleeper_api.py, espn_api.py)
- Scrapers: Data-specific scrapers that use APIs (nfl_schedule_scraper.py, etc.)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from .apis.sleeper_api import SleeperAPI
from .apis.espn_api import ESPNAPI
from .apis.espn_web_api import ESPNWebAPI
from .apis.pro_football_reference_api import ProFootballReferenceAPI
from .scrapers.nfl_schedule_scraper import NFLScheduleScraper
from .scrapers.nfl_players_scraper import NFLPlayersScraper
from .scrapers.nfl_rankings_scraper import NFLRankingsScraper
from .scrapers.nfl_news import NFLNewsScraper  # Keep existing news scraper
from .scrapers.nfl_game_logs_scraper import NFLGameLogsScraper
from .scrapers.nfl_advanced_stats_scraper import NFLAdvancedStatsScraper
from ..utils.season_utils import get_smart_season_defaults

# Smart season detection
season_defaults = get_smart_season_defaults()
CURRENT_YEAR = season_defaults["season"]


class SportsScraper:
    """Main sports scraper service using organized APIs and scrapers"""
    
    def __init__(self):
        # API clients
        self.sleeper_api = SleeperAPI()
        self.espn_api = ESPNAPI()
        self.espn_web_api = ESPNWebAPI()
        self.pfr_api = ProFootballReferenceAPI()
        
        # Specialized scrapers
        self.nfl_schedule = NFLScheduleScraper()
        self.nfl_players = NFLPlayersScraper()
        self.nfl_rankings = NFLRankingsScraper()
        
        # New granular data scrapers
        self.nfl_game_logs = NFLGameLogsScraper()
        self.nfl_advanced_stats = NFLAdvancedStatsScraper()
        
        # Keep existing news scraper (uses RSS feeds)
        self.nfl_news = NFLNewsScraper(sleeper_api=self.sleeper_api)
    
    # ==================== User/League Methods (Sleeper API) ====================
    
    def get_sleeper_user(self, username: str = None, user_id: str = None) -> Dict[str, Any]:
        """Get Sleeper user information"""
        try:
            return self.sleeper_api.get_user(username, user_id)
        except Exception as e:
            raise Exception(f"Failed to fetch Sleeper user: {str(e)}")
    
    def get_sleeper_leagues(self, user_id: str, season: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get leagues for a Sleeper user"""
        try:
            return self.sleeper_api.get_user_leagues(user_id, season)
        except Exception as e:
            raise Exception(f"Failed to fetch Sleeper leagues: {str(e)}")
    
    def get_sleeper_league(self, league_id: str) -> Dict[str, Any]:
        """Get Sleeper league information"""
        try:
            return self.sleeper_api.get_league(league_id)
        except Exception as e:
            raise Exception(f"Failed to fetch Sleeper league: {str(e)}")
    
    def get_sleeper_rosters(self, league_id: str) -> List[Dict[str, Any]]:
        """Get rosters for a Sleeper league"""
        try:
            return self.sleeper_api.get_league_rosters(league_id)
        except Exception as e:
            raise Exception(f"Failed to fetch Sleeper rosters: {str(e)}")
    
    def get_sleeper_matchups(self, league_id: str, week: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get matchups for a Sleeper league"""
        try:
            return self.sleeper_api.get_league_matchups(league_id, week)
        except Exception as e:
            raise Exception(f"Failed to fetch Sleeper matchups: {str(e)}")
    
    def get_sleeper_transactions(self, league_id: str, round_num: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get transactions for a Sleeper league"""
        try:
            return self.sleeper_api.get_league_transactions(league_id, round_num)
        except Exception as e:
            raise Exception(f"Failed to fetch Sleeper transactions: {str(e)}")
    
    def get_sleeper_players(self, sport: str = "nfl") -> Dict[str, Any]:
        """Get all players for a sport from Sleeper"""
        try:
            return self.sleeper_api.get_all_players(sport)
        except Exception as e:
            raise Exception(f"Failed to fetch Sleeper players: {str(e)}")
    
    def get_sleeper_player_stats(
        self,
        sport: str = "nfl",
        season: str = None,
        season_type: str = "regular"
    ) -> Dict[str, Any]:
        """Get player statistics from Sleeper"""
        if season is None:
            season = CURRENT_YEAR
        try:
            return self.sleeper_api.get_player_stats(sport, season, season_type)
        except Exception as e:
            raise Exception(f"Failed to fetch Sleeper player stats: {str(e)}")
    
    # ==================== NFL Schedule Methods (ESPN API) ====================
    
    def get_nfl_schedule(
        self,
        season: str = None,
        season_type: str = "regular",
        week: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get NFL schedule using ESPN API"""
        if season is None:
            season = CURRENT_YEAR
        return self.nfl_schedule.get_schedule(season, season_type, week)
    
    # ==================== NFL Player Methods (Sleeper API) ====================
    
    def get_sleeper_trending_players(
        self,
        sport: str = "nfl",
        trend_type: str = "add",
        lookback_hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get trending players using Sleeper API"""
        return self.nfl_players.get_trending_players(trend_type, lookback_hours, limit)
    
    def get_sleeper_top_players_by_stats(
        self,
        sport: str = "nfl",
        position: Optional[str] = None,
        stat_key: str = "pts_half_ppr",
        limit: int = 100,
        season: str = None,
        season_type: str = "regular"
    ) -> List[Dict[str, Any]]:
        """Get top players by stats using Sleeper API"""
        if season is None:
            season = CURRENT_YEAR
        return self.nfl_players.get_top_players_by_stats(
            position, stat_key, limit, season, season_type
        )
    
    def get_sleeper_injured_players(
        self,
        sport: str = "nfl",
        injury_status: Optional[str] = None,
        status: Optional[str] = None,
        has_team: bool = True
    ) -> List[Dict[str, Any]]:
        """Get injured players using Sleeper API"""
        return self.nfl_players.get_injured_players(injury_status, status, has_team)
    
    # ==================== NFL Standings Methods (Sleeper API) ====================
    
    def get_sleeper_nfl_standings(
        self,
        season: str = None,
        season_type: str = "regular",
        grouping: str = "league"
    ) -> List[Dict[str, Any]]:
        """Get NFL standings using Sleeper API"""
        if season is None:
            season = CURRENT_YEAR
        return self.nfl_standings.get_standings(season, season_type, grouping)
    
    # ==================== NFL Rankings Methods (Sleeper API) ====================
    
    def get_nfl_team_rankings(
        self,
        season: str = None,
        season_type: str = "regular",
        ranking_types: List[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get NFL team rankings using Sleeper API"""
        if season is None:
            season = CURRENT_YEAR
        return self.nfl_rankings.get_team_rankings(season, season_type, ranking_types)
    
    # ==================== NFL News Methods (RSS Feeds) ====================
    
    def get_nfl_news_from_rss(
        self,
        source: str = "espn",
        limit: int = 50,
        max_age_hours: int = 168
    ) -> List[Dict[str, Any]]:
        """Get NFL news from RSS feeds"""
        return self.nfl_news.get_nfl_news_from_rss(source, limit, max_age_hours)
    
    def match_news_to_players(
        self,
        news_items: List[Dict[str, Any]],
        sport: str = "nfl"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Match news items to players"""
        return self.nfl_news.match_news_to_players(news_items, sport)
    
    # ==================== Legacy Methods (for backward compatibility) ====================
    
    def get_sleeper_draft(self, draft_id: str) -> Dict[str, Any]:
        """Get draft information from Sleeper"""
        try:
            return self.sleeper_api.get_draft(draft_id)
        except Exception as e:
            raise Exception(f"Failed to fetch Sleeper draft: {str(e)}")
    
    # ==================== NEW GRANULAR DATA METHODS ====================
    
    # ==================== Player Game Logs Methods ====================
    
    def get_player_game_logs(
        self,
        player_id: str,
        season: str = None,
        source: str = "espn"
    ) -> List[Dict[str, Any]]:
        """Get individual game logs for a player"""
        return self.nfl_game_logs.get_player_game_logs(player_id, season, source)
    
    def get_multiple_player_game_logs(
        self,
        player_ids: List[str],
        season: str = None,
        source: str = "espn"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get game logs for multiple players"""
        return self.nfl_game_logs.get_multiple_player_game_logs(player_ids, season, source)
    
    # ==================== Advanced Stats Methods ====================
    
    def get_team_advanced_stats(
        self,
        season: str = None,
        source: str = "pfr"
    ) -> List[Dict[str, Any]]:
        """Get advanced team statistics"""
        return self.nfl_advanced_stats.get_team_advanced_stats(season, source)
    
    def get_player_season_stats(
        self,
        position: str = "QB",
        season: str = None,
        source: str = "pfr"
    ) -> List[Dict[str, Any]]:
        """Get player season statistics by position"""
        return self.nfl_advanced_stats.get_player_season_stats(position, season, source)
    
    def get_all_position_stats(
        self,
        season: str = None,
        source: str = "pfr"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get season stats for all major positions"""
        return self.nfl_advanced_stats.get_all_position_stats(season, source)
    
    def get_weekly_matchups(
        self,
        season: str = None,
        week: int = 1,
        source: str = "pfr"
    ) -> List[Dict[str, Any]]:
        """Get weekly matchup data with advanced metrics"""
        return self.nfl_advanced_stats.get_weekly_matchups(season, week, source)
    
    # ==================== Utility Methods ====================
    
    def save_to_document_format(self, data: Dict[str, Any], source: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Convert scraped data to document format for MongoDB storage"""
        from .scrapers.base_scraper import BaseScraper
        base_scraper = BaseScraper()
        return base_scraper.save_to_document_format(data, source, title)
    
    def batch_fetch(self, urls: List[str], source: str = "sleeper") -> List[Dict[str, Any]]:
        """Batch fetch multiple URLs"""
        from .scrapers.base_scraper import BaseScraper
        base_scraper = BaseScraper()
        return base_scraper.batch_fetch(urls, source)