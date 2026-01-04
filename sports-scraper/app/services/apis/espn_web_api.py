"""
ESPN Web API Client
Uses ESPN's official JSON APIs for real data (no web scraping needed)
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime


class ESPNWebAPI:
    """ESPN API client using official JSON endpoints"""
    
    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.core_url = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    # ==================== Team Stats ====================
    
    def get_team_stats(self, stat_type: str = "offense") -> List[Dict[str, Any]]:
        """Get team statistics using ESPN's official API"""
        
        try:
            # Get teams data from ESPN API
            url = f"{self.base_url}/teams"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            teams = []
            
            # Extract team data from ESPN API response
            if 'sports' in data and len(data['sports']) > 0:
                sport = data['sports'][0]
                if 'leagues' in sport and len(sport['leagues']) > 0:
                    league = sport['leagues'][0]
                    if 'teams' in league:
                        for team_data in league['teams']:
                            team = team_data.get('team', {})
                            
                            team_stats = {
                                'team': team.get('displayName', team.get('name', 'Unknown')),
                                'abbreviation': team.get('abbreviation', ''),
                                'stat_type': stat_type,
                                'source': 'espn_api',
                                'scraped_at': datetime.now().isoformat()
                            }
                            
                            # Add team record if available
                            if 'record' in team:
                                record = team['record']
                                if 'items' in record and len(record['items']) > 0:
                                    record_item = record['items'][0]
                                    team_stats.update({
                                        'wins': record_item.get('wins', 0),
                                        'losses': record_item.get('losses', 0),
                                        'ties': record_item.get('ties', 0),
                                        'win_percentage': record_item.get('winPercent', 0)
                                    })
                            
                            # Add additional team info
                            if 'logos' in team and len(team['logos']) > 0:
                                team_stats['logo'] = team['logos'][0].get('href', '')
                            
                            teams.append(team_stats)
            
            return teams
            
        except Exception as e:
            raise Exception(f"Failed to get team stats from ESPN API: {str(e)}")
    
    # ==================== News ====================
    
    def get_nfl_news(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get NFL news from ESPN API"""
        
        try:
            url = f"{self.base_url}/news"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            news_items = []
            
            if 'articles' in data:
                for article in data['articles'][:limit]:
                    news_item = {
                        'title': article.get('headline', ''),
                        'description': article.get('description', ''),
                        'link': article.get('links', {}).get('web', {}).get('href', ''),
                        'published': article.get('published', ''),
                        'source': 'espn_api',
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    # Add images if available
                    if 'images' in article and len(article['images']) > 0:
                        news_item['image'] = article['images'][0].get('url', '')
                    
                    # Add categories
                    if 'categories' in article:
                        categories = [cat.get('description', '') for cat in article['categories']]
                        news_item['categories'] = categories
                    
                    news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            raise Exception(f"Failed to get news from ESPN API: {str(e)}")
    
    # ==================== Scoreboard ====================
    
    def get_scoreboard(self) -> List[Dict[str, Any]]:
        """Get current NFL scoreboard from ESPN API"""
        
        try:
            url = f"{self.base_url}/scoreboard"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            games = []
            
            if 'events' in data:
                for event in data['events']:
                    game = {
                        'game_id': event.get('id', ''),
                        'date': event.get('date', ''),
                        'status': event.get('status', {}).get('type', {}).get('description', ''),
                        'source': 'espn_api',
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    # Get teams
                    if 'competitions' in event and len(event['competitions']) > 0:
                        competition = event['competitions'][0]
                        if 'competitors' in competition:
                            for competitor in competition['competitors']:
                                team = competitor.get('team', {})
                                is_home = competitor.get('homeAway') == 'home'
                                
                                team_key = 'home_team' if is_home else 'away_team'
                                score_key = 'home_score' if is_home else 'away_score'
                                
                                game[team_key] = team.get('displayName', team.get('name', ''))
                                game[f"{team_key}_abbr"] = team.get('abbreviation', '')
                                
                                # Get score if available
                                if 'score' in competitor:
                                    try:
                                        game[score_key] = int(competitor['score'])
                                    except (ValueError, TypeError):
                                        game[score_key] = 0
                    
                    games.append(game)
            
            return games
            
        except Exception as e:
            raise Exception(f"Failed to get scoreboard from ESPN API: {str(e)}")
    
    # ==================== Season Stats ====================
    
    def get_season_teams(self, season: str = None) -> List[Dict[str, Any]]:
        """Get detailed team information for a season"""
        if season is None:
            season = str(datetime.now().year)
        
        try:
            url = f"{self.core_url}/seasons/{season}/teams"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            teams = []
            
            if 'items' in data:
                for item in data['items']:
                    # Get detailed team info
                    team_url = item.get('$ref', '')
                    if team_url:
                        try:
                            team_response = self.session.get(team_url, timeout=10)
                            if team_response.status_code == 200:
                                team_data = team_response.json()
                                
                                team_info = {
                                    'id': team_data.get('id', ''),
                                    'name': team_data.get('displayName', team_data.get('name', '')),
                                    'abbreviation': team_data.get('abbreviation', ''),
                                    'location': team_data.get('location', ''),
                                    'season': season,
                                    'source': 'espn_core_api',
                                    'scraped_at': datetime.now().isoformat()
                                }
                                
                                # Add conference/division info
                                if 'groups' in team_data:
                                    group = team_data['groups']
                                    if 'parent' in group:
                                        team_info['conference'] = group['parent'].get('name', '')
                                    team_info['division'] = group.get('name', '')
                                
                                teams.append(team_info)
                        except:
                            continue
            
            return teams
            
        except Exception as e:
            raise Exception(f"Failed to get season teams from ESPN API: {str(e)}")
    
    # ==================== Legacy Methods (for compatibility) ====================
    
    def get_player_game_log(self, player_id: str, season: str = None) -> List[Dict[str, Any]]:
        """Get player game log - ESPN API implementation not available"""
        raise NotImplementedError("ESPN player game log API requires authentication and is not currently implemented. Use Pro Football Reference instead.")
    
    def get_team_depth_chart(self, team_name: str) -> Dict[str, Any]:
        """Get team depth chart - not implemented"""
        raise NotImplementedError("ESPN team depth chart API is not currently implemented.")