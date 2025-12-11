"""
Sports Data Scraper Service
Facade that delegates to specialized scraper modules
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from .scrapers.sleeper_api import SleeperAPIScraper
from .scrapers.nfl_schedule import NFLScheduleScraper
from .scrapers.nfl_rankings import NFLRankingsScraper
from .scrapers.nfl_news import NFLNewsScraper
from .scrapers.nfl_standings import NFLStandingsScraper

# Get current year as default
CURRENT_YEAR = str(datetime.now().year)


class SportsScraper:
    """Service for scraping sports data from multiple sources"""
    
    def __init__(self):
        # Initialize all scraper modules
        self.sleeper_api = SleeperAPIScraper()
        self.nfl_schedule = NFLScheduleScraper()
        self.nfl_standings = NFLStandingsScraper()
        self.nfl_news = NFLNewsScraper(sleeper_api_scraper=self.sleeper_api)
        self.nfl_rankings = NFLRankingsScraper(
            sleeper_api_scraper=self.sleeper_api,
            standings_scraper=self.nfl_standings
        )
    
    # ==================== Sleeper API Methods ====================
    
    def get_sleeper_user(self, username: str = None, user_id: str = None) -> Dict[str, Any]:
        """Get Sleeper user information"""
        return self.sleeper_api.get_sleeper_user(username, user_id)
    
    def get_sleeper_leagues(self, user_id: str, season: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get leagues for a Sleeper user"""
        return self.sleeper_api.get_sleeper_leagues(user_id, season)
    
    def get_sleeper_league(self, league_id: str) -> Dict[str, Any]:
        """Get Sleeper league information"""
        return self.sleeper_api.get_sleeper_league(league_id)
    
    def get_sleeper_rosters(self, league_id: str) -> List[Dict[str, Any]]:
        """Get rosters for a Sleeper league"""
        return self.sleeper_api.get_sleeper_rosters(league_id)
    
    def get_sleeper_players(self, sport: str = "nfl") -> Dict[str, Any]:
        """Get all players for a sport from Sleeper"""
        return self.sleeper_api.get_sleeper_players(sport)
    
    def get_sleeper_trending_players(
        self, 
        sport: str = "nfl", 
        trend_type: str = "add", 
        lookback_hours: int = 24, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get trending players from Sleeper"""
        return self.sleeper_api.get_sleeper_trending_players(sport, trend_type, lookback_hours, limit)
    
    def get_sleeper_player_stats(
        self,
        sport: str = "nfl",
        season: str = None,
        season_type: str = "regular"
    ) -> Dict[str, Any]:
        """Get player statistics from Sleeper"""
        if season is None:
            season = CURRENT_YEAR
        return self.sleeper_api.get_sleeper_player_stats(sport, season, season_type)
    
    def get_sleeper_top_players_by_stats(
        self,
        sport: str = "nfl",
        position: Optional[str] = None,
        stat_key: str = "pts_half_ppr",
        limit: int = 100,
        season: str = None,
        season_type: str = "regular"
    ) -> List[Dict[str, Any]]:
        """Get top NFL players from Sleeper sorted by statistics"""
        if season is None:
            season = CURRENT_YEAR
        return self.sleeper_api.get_sleeper_top_players_by_stats(
            sport, position, stat_key, limit, season, season_type
        )
    
    def get_sleeper_draft(self, draft_id: str) -> Dict[str, Any]:
        """Get draft information from Sleeper"""
        return self.sleeper_api.get_sleeper_draft(draft_id)
    
    def get_sleeper_matchups(self, league_id: str, week: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get matchups for a Sleeper league"""
        return self.sleeper_api.get_sleeper_matchups(league_id, week)
    
    def get_sleeper_transactions(self, league_id: str, round_num: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get transactions for a Sleeper league"""
        return self.sleeper_api.get_sleeper_transactions(league_id, round_num)
    
    def get_sleeper_injured_players(
        self,
        sport: str = "nfl",
        injury_status: Optional[str] = None,
        status: Optional[str] = None,
        has_team: bool = True
    ) -> List[Dict[str, Any]]:
        """Get injured/out players from Sleeper"""
        return self.sleeper_api.get_sleeper_injured_players(sport, injury_status, status, has_team)
    
    # ==================== NFL Standings Methods ====================
    
    def get_sleeper_nfl_standings(
        self,
        season: str = None,
        season_type: str = "regular",
        grouping: str = "league"
    ) -> List[Dict[str, Any]]:
        """Get NFL standings from Sleeper webpage"""
        if season is None:
            season = CURRENT_YEAR
        return self.nfl_standings.get_sleeper_nfl_standings(season, season_type, grouping)
    
    # ==================== NFL News Methods ====================
    
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
    
    # ==================== NFL Schedule Methods ====================
    
    def get_nfl_schedule(
        self,
        season: str = None,
        season_type: str = "regular",
        week: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get NFL schedule/matchups from ESPN API"""
        if season is None:
            season = CURRENT_YEAR
        return self.nfl_schedule.get_nfl_schedule(season, season_type, week)
    
    # ==================== NFL Rankings Methods ====================
    
    def get_nfl_team_rankings(
        self,
        season: str = None,
        season_type: str = "regular",
        ranking_type: str = "offense"
    ) -> List[Dict[str, Any]]:
        """Get NFL team rankings by offense, defense, etc."""
        if season is None:
            season = CURRENT_YEAR
        return self.nfl_rankings.get_nfl_team_rankings(season, season_type, ranking_type)
    
    # ==================== Utility Methods ====================
    
    def save_to_document_format(self, data: Dict[str, Any], source: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Convert scraped data to document format for MongoDB storage"""
        return self.sleeper_api.save_to_document_format(data, source, title)
    
    def batch_fetch(self, urls: List[str], source: str = "sleeper") -> List[Dict[str, Any]]:
        """Batch fetch multiple URLs"""
        return self.sleeper_api.batch_fetch(urls, source)
