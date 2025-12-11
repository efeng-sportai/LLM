"""
NFL News Scraper
Fetches NFL news from RSS feeds and matches to players
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Any
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from .base_scraper import BaseScraper


class NFLNewsScraper(BaseScraper):
    """Scraper for NFL news from RSS feeds"""
    
    def __init__(self, sleeper_api_scraper=None):
        """
        Initialize NFL News Scraper
        
        Args:
            sleeper_api_scraper: Optional SleeperAPIScraper instance for player matching
        """
        super().__init__()
        self.sleeper_api_scraper = sleeper_api_scraper
    
    def get_nfl_news_from_rss(
        self,
        source: str = "espn",
        limit: int = 50,
        max_age_hours: int = 168
    ) -> List[Dict[str, Any]]:
        """
        Get NFL news from RSS feeds (most recent articles only)
        
        Args:
            source: News source - 'espn' or 'nfl' (default: 'espn')
            limit: Maximum number of news items to return (default: 50)
            max_age_hours: Only include articles published within this many hours (default: 168 = 7 days = 1 week)
            
        Returns:
            List of news item dictionaries with title, description, link, pubDate, etc., sorted by date (newest first)
        """
        try:
            # Calculate cutoff time for recent articles
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            # RSS feed URLs
            rss_urls = {
                "espn": "https://www.espn.com/espn/rss/nfl/news",
                "nfl": "http://www.nfl.com/rss/rsslanding?searchString=news"
            }
            
            if source.lower() not in rss_urls:
                raise ValueError(f"Unknown source: {source}. Must be 'espn' or 'nfl'")
            
            url = rss_urls[source.lower()]
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse RSS XML
            root = ET.fromstring(response.text)
            
            # Find channel - RSS 2.0 doesn't use namespaces by default
            channel = root.find('channel')
            
            if channel is None:
                raise Exception("Could not parse RSS feed structure")
            
            news_items = []
            items = channel.findall('item')
            
            for item in items[:limit]:
                try:
                    title_elem = item.find('title')
                    desc_elem = item.find('description')
                    link_elem = item.find('link')
                    pubdate_elem = item.find('pubDate')
                    
                    # Get text content - handle CDATA properly
                    title = ""
                    description = ""
                    link = ""
                    pubdate = ""
                    
                    # Extract from elements, handling CDATA
                    if title_elem is not None:
                        # ElementTree should extract CDATA automatically, but check both ways
                        if title_elem.text:
                            title = title_elem.text
                        else:
                            # Try extracting from CDATA manually
                            title_xml = ET.tostring(title_elem, encoding='unicode')
                            if '<![CDATA[' in title_xml:
                                match = re.search(r'<!\[CDATA\[(.*?)\]\]>', title_xml, re.DOTALL)
                                if match:
                                    title = match.group(1)
                    
                    if desc_elem is not None:
                        if desc_elem.text:
                            description = desc_elem.text
                        else:
                            desc_xml = ET.tostring(desc_elem, encoding='unicode')
                            if '<![CDATA[' in desc_xml:
                                match = re.search(r'<!\[CDATA\[(.*?)\]\]>', desc_xml, re.DOTALL)
                                if match:
                                    description = match.group(1)
                    
                    if link_elem is not None:
                        if link_elem.text:
                            link = link_elem.text
                        else:
                            link_xml = ET.tostring(link_elem, encoding='unicode')
                            if '<![CDATA[' in link_xml:
                                match = re.search(r'<!\[CDATA\[(.*?)\]\]>', link_xml, re.DOTALL)
                                if match:
                                    link = match.group(1)
                    
                    if pubdate_elem is not None:
                        pubdate = pubdate_elem.text if pubdate_elem.text else ""
                    
                    # Parse publication date and filter by recency
                    article_date = None
                    if pubdate:
                        try:
                            # Parse RSS date format (RFC 822 format, e.g., "Fri, 31 Oct 2025 20:50:21 EST")
                            article_date = parsedate_to_datetime(pubdate)
                            # Convert to UTC if not already
                            if article_date.tzinfo is None:
                                article_date = article_date.replace(tzinfo=None)
                                # Assume UTC if timezone not specified
                            
                            # Filter: only include articles within max_age_hours
                            article_date_utc = article_date.replace(tzinfo=None) if article_date.tzinfo else article_date
                            if article_date_utc < cutoff_time:
                                # Article is too old, skip it
                                continue
                        except (ValueError, TypeError) as e:
                            # If date parsing fails, include the article anyway (better to include than miss)
                            pass
                    
                    # Clean up any remaining HTML tags
                    title = re.sub(r'<[^>]+>', '', title) if title else ""
                    description = re.sub(r'<[^>]+>', '', description) if description else ""
                    
                    news_item = {
                        "title": title.strip(),
                        "description": description.strip(),
                        "link": link.strip(),
                        "pubDate": pubdate.strip(),
                        "source": source.lower()
                    }
                    
                    # Add parsed date if available
                    if article_date:
                        news_item["pubDate_parsed"] = article_date.isoformat()
                    
                    # Try to extract creator/author if available
                    creator_elem = item.find('{http://purl.org/dc/elements/1.1/}creator') or item.find('dc:creator', {'dc': 'http://purl.org/dc/elements/1.1/'})
                    if creator_elem is not None:
                        news_item["creator"] = creator_elem.text.strip()
                    
                    news_items.append(news_item)
                except Exception as e:
                    continue
            
            # Sort by publication date (newest first)
            # Items with dates come first, then items without dates
            def sort_key(item):
                pub_date_str = item.get("pubDate_parsed")
                if pub_date_str:
                    try:
                        return datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                    except:
                        return datetime.min
                return datetime.min
            
            news_items.sort(key=sort_key, reverse=True)
            
            # Limit to requested number of items
            return news_items[:limit]
        except Exception as e:
            raise Exception(f"Failed to fetch/parse RSS feed: {str(e)}")
    
    def match_news_to_players(
        self,
        news_items: List[Dict[str, Any]],
        sport: str = "nfl"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Match news items to players based on player names in news titles/descriptions
        
        Args:
            news_items: List of news item dictionaries
            sport: Sport abbreviation (default: 'nfl')
            
        Returns:
            Dictionary mapping player IDs to lists of matched news items
        """
        if not self.sleeper_api_scraper:
            raise Exception("SleeperAPIScraper instance required for player matching")
        
        try:
            # Get all players
            all_players = self.sleeper_api_scraper.get_sleeper_players(sport)
            
            # Build player name lookup - ONLY full names to avoid false positives
            player_lookup = {}
            for player_id, player_data in all_players.items():
                if not isinstance(player_data, dict):
                    continue
                
                full_name = player_data.get("full_name", "")
                
                # Only use full names for matching - no first/last name matching
                if full_name and len(full_name) > 3:  # Only meaningful names
                    full_name_lower = full_name.lower()
                    if full_name_lower not in player_lookup:
                        player_lookup[full_name_lower] = []
                    player_lookup[full_name_lower].append({
                        "player_id": player_id,
                        "player_data": player_data,
                        "match_type": "full_name"
                    })
            
            # Match news to players - ONLY match full names
            player_news = {}
            for news_item in news_items:
                title = news_item.get("title", "").lower()
                description = news_item.get("description", "").lower()
                text = f"{title} {description}"
                
                # Check for player full names in news text
                matched_players = set()
                for full_name_lower, players in player_lookup.items():
                    # Skip short names to avoid false positives
                    if len(full_name_lower) < 4:
                        continue
                    
                    # Check for full name match in news text
                    # Match full name as-is (e.g., "patrick mahomes" in "Patrick Mahomes throws TD")
                    if full_name_lower in text:
                        for player_entry in players:
                            player_id = player_entry["player_id"]
                            matched_players.add(player_id)
                    # Also check if full name appears as separate words (e.g., "Patrick Mahomes")
                    elif " " in full_name_lower:
                        name_parts = full_name_lower.split()
                        # Both first and last name must appear (all parts)
                        if len(name_parts) >= 2 and all(part in text for part in name_parts):
                            # Additional check: ensure they appear in reasonable proximity
                            # (not just anywhere in the text, but likely referring to the same person)
                            for player_entry in players:
                                player_id = player_entry["player_id"]
                                matched_players.add(player_id)
                
                # Add news to matched players
                for player_id in matched_players:
                    if player_id not in player_news:
                        player_news[player_id] = []
                    player_news[player_id].append(news_item)
            
            return player_news
        except Exception as e:
            raise Exception(f"Failed to match news to players: {str(e)}")

