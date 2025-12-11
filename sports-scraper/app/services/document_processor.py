from bs4 import BeautifulSoup
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

class DocumentProcessor:
    """Service for processing and converting documents"""
    
    def __init__(self):
        self.supported_formats = ['html', 'xml', 'txt', 'json']
    
    def html_to_json(self, html_content: str, url: Optional[str] = None) -> Dict[str, Any]:
        """Convert HTML content to structured JSON"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract structured data
        document_data = {
            "title": self._extract_title(soup),
            "content": self._extract_main_content(soup),
            "headings": self._extract_headings(soup),
            "links": self._extract_links(soup),
            "images": self._extract_images(soup),
            "metadata": {
                "url": url,
                "processed_at": datetime.utcnow().isoformat(),
                "word_count": len(self._extract_main_content(soup).split()),
                "heading_count": len(self._extract_headings(soup))
            }
        }
        
        return document_data
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract document title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "Untitled Document"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML"""
        # Try to find main content areas
        main_content_selectors = [
            'main', 'article', '.content', '#content', 
            '.main-content', '.post-content', '.entry-content'
        ]
        
        for selector in main_content_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        # Fallback: extract all paragraph text
        paragraphs = soup.find_all('p')
        if paragraphs:
            return ' '.join([p.get_text().strip() for p in paragraphs])
        
        # Last resort: get all text
        return soup.get_text().strip()
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all headings with their levels"""
        headings = []
        for i in range(1, 7):  # h1 to h6
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    "level": i,
                    "text": heading.get_text().strip(),
                    "id": heading.get('id', '')
                })
        return headings
    
    def _extract_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all links"""
        links = []
        for link in soup.find_all('a', href=True):
            links.append({
                "text": link.get_text().strip(),
                "url": link['href'],
                "title": link.get('title', '')
            })
        return links
    
    def _extract_images(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all images"""
        images = []
        for img in soup.find_all('img'):
            images.append({
                "src": img.get('src', ''),
                "alt": img.get('alt', ''),
                "title": img.get('title', '')
            })
        return images
    
    def process_url(self, url: str) -> Dict[str, Any]:
        """Fetch and process content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Determine content type
            content_type = response.headers.get('content-type', '').lower()
            
            if 'html' in content_type:
                return self.html_to_json(response.text, url)
            elif 'json' in content_type:
                return {
                    "title": url.split('/')[-1],
                    "content": json.dumps(response.json(), indent=2),
                    "source_type": "json",
                    "metadata": {
                        "url": url,
                        "processed_at": datetime.utcnow().isoformat()
                    }
                }
            else:
                return {
                    "title": url.split('/')[-1],
                    "content": response.text,
                    "source_type": "text",
                    "metadata": {
                        "url": url,
                        "processed_at": datetime.utcnow().isoformat()
                    }
                }
                
        except Exception as e:
            raise Exception(f"Failed to process URL {url}: {str(e)}")
    
    def create_document_from_text(self, title: str, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a document from plain text"""
        return {
            "title": title,
            "content": content,
            "source_type": "user_created",
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "word_count": len(content.split()),
                **(metadata or {})
            }
        }
    
    def process_user_interaction(self, query: str, response: str, session_id: str, 
                                document_id: Optional[int] = None, 
                                metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Process and format user interaction data for back-feeding"""
        return {
            "session_id": session_id,
            "user_query": query,
            "ai_response": response,
            "document_id": document_id,
            "interaction_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "query_length": len(query.split()),
                "response_length": len(response.split()),
                **(metadata or {})
            }
        }
