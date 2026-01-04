"""
Scrapers Package
Data-specific scrapers that use API clients to get structured data

Architecture:
- Each scraper focuses on specific data (schedule, players, rankings)
- Scrapers use API clients from the apis/ package
- Clear separation between API calls and data processing
"""

from .base_scraper import BaseScraper
from .nfl_schedule_scraper import NFLScheduleScraper
from .nfl_players_scraper import NFLPlayersScraper
from .nfl_rankings_scraper import NFLRankingsScraper
from .nfl_news import NFLNewsScraper

__all__ = [
    "BaseScraper",
    "NFLScheduleScraper",
    "NFLPlayersScraper", 
    "NFLRankingsScraper",
    "NFLNewsScraper",
]

