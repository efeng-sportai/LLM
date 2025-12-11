"""
Base scraper class with shared functionality
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class BaseScraper:
    """Base class for all scrapers with shared session and utilities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def save_to_document_format(self, data: Dict[str, Any], source: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert scraped data to document format for MongoDB storage
        
        Args:
            data: Scraped data dictionary
            source: Source identifier ('sleeper')
            title: Optional title override
            
        Returns:
            Dictionary in document format
        """
        return {
            "title": title or data.get("title", f"{source.title()} Data"),
            "content": json.dumps(data, indent=2) if isinstance(data, dict) else str(data),
            "source_type": f"{source}_scraper",
            "source_url": data.get("url", ""),
            "doc_metadata": {
                "source": source,
                "scraped_at": datetime.utcnow().isoformat(),
                "data_type": data.get("type", "unknown"),
                **data.get("metadata", {})
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
    
    def batch_fetch(self, urls: List[str], source: str = "sleeper") -> List[Dict[str, Any]]:
        """
        Batch fetch multiple URLs
        
        Args:
            urls: List of URLs to fetch
            source: Source identifier (default: 'sleeper')
            
        Returns:
            List of fetched data dictionaries
        """
        results = []
        for url in urls:
            try:
                # Generic scraping
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                data = {
                    "title": "Scraped Content",
                    "content": response.text[:5000],  # Limit content size
                    "url": url,
                    "scraped_at": datetime.utcnow().isoformat(),
                    "source": source
                }
                results.append(data)
            except Exception as e:
                results.append({
                    "url": url,
                    "error": str(e),
                    "scraped_at": datetime.utcnow().isoformat()
                })
        return results

