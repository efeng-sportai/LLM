"""
Pro Football Reference Web API Client
Web scraping client for Pro-Football-Reference.com data (advanced stats, game logs)
Implements respectful scraping with rate limiting and browser-like behavior
"""

import requests
import json
import re
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser


class ProFootballReferenceAPI:
    """Web scraping client for Pro-Football-Reference.com with respectful rate limiting"""
    
    def __init__(self, rate_limit_delay: float = 2.0, randomize_delay: bool = True):
        self.base_url = "https://www.pro-football-reference.com"
        self.rate_limit_delay = rate_limit_delay  # Base delay between requests
        self.randomize_delay = randomize_delay    # Add randomization to delays
        self.last_request_time = 0
        
        # Create session with browser-like headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Check robots.txt on initialization
        self._check_robots_txt()
    
    def _check_robots_txt(self):
        """Check robots.txt for scraping guidelines"""
        try:
            rp = RobotFileParser()
            rp.set_url(f"{self.base_url}/robots.txt")
            rp.read()
            
            # Check if we can fetch the main pages we need
            test_urls = [
                f"{self.base_url}/years/2025/passing.htm",
                f"{self.base_url}/years/2025/receiving.htm"
            ]
            
            for url in test_urls:
                if not rp.can_fetch('*', url):
                    print(f"   [WARNING] robots.txt disallows: {url}")
                else:
                    print(f"   [OK] robots.txt allows: {url}")
                    
            # Look for crawl delay
            crawl_delay = rp.crawl_delay('*')
            if crawl_delay:
                self.rate_limit_delay = max(self.rate_limit_delay, crawl_delay)
                print(f"   [INFO] robots.txt suggests crawl delay: {crawl_delay}s")
                
        except Exception as e:
            print(f"   [WARNING] Could not check robots.txt: {e}")
    
    def _rate_limit(self):
        """Implement respectful rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Calculate delay
        delay = self.rate_limit_delay
        if self.randomize_delay:
            # Add 0-50% randomization to avoid predictable patterns
            delay += random.uniform(0, self.rate_limit_delay * 0.5)
        
        if time_since_last < delay:
            sleep_time = delay - time_since_last
            print(f"   [RATE LIMIT] Waiting {sleep_time:.1f}s before next request...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """Make a rate-limited request with error handling"""
        self._rate_limit()
        
        try:
            response = self.session.get(url, timeout=30, **kwargs)
            
            # Handle rate limiting responses
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After', 60)
                print(f"   [RATE LIMITED] 429 error, waiting {retry_after}s...")
                time.sleep(int(retry_after))
                return self._make_request(url, **kwargs)  # Retry once
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed for {url}: {str(e)}")
    
    # ==================== Enhanced Player Data Methods ====================
    
    def get_enhanced_player_stats(self, position: str = "QB", season: str = None, include_game_logs: bool = True, max_players: int = None) -> List[Dict[str, Any]]:
        """
        Get enhanced player statistics with optional game logs for ALL players
        
        Args:
            position: Player position (QB, RB, WR, TE, K)
            season: Season year (default: current year)
            include_game_logs: Whether to fetch individual game logs (slower but more detailed)
            max_players: Maximum number of players (None = all players)
        """
        if season is None:
            season = str(datetime.now().year)
        
        print(f"   [INFO] Getting enhanced {position} stats for {season} season (ALL PLAYERS)...")
        
        # First get basic season stats for ALL players
        basic_stats = self.get_player_season_stats(position, season)
        
        if not basic_stats:
            return []
        
        # Process ALL players unless max_players is specified
        players_to_process = basic_stats if max_players is None else basic_stats[:max_players]
        total_players = len(players_to_process)
        
        print(f"   [INFO] Processing detailed stats for ALL {total_players} {position} players...")
        print(f"   [INFO] This will take approximately {(total_players * 2.5) / 60:.1f} minutes with rate limiting...")
        
        enhanced_players = []
        
        for i, player in enumerate(players_to_process):
            try:
                enhanced_player = player.copy()
                player_name = player.get('player', 'Unknown')
                
                if i % 10 == 0 or i == total_players - 1:  # Progress every 10 players
                    print(f"   [PROGRESS] Processing {i+1}/{total_players}: {player_name}")
                
                # Add calculated advanced stats
                enhanced_player.update(self._calculate_advanced_stats(player, position))
                
                # Add efficiency metrics
                enhanced_player.update(self._calculate_efficiency_metrics(player, position))
                
                # Get game logs if requested (this is the detailed per-game data)
                if include_game_logs:
                    game_logs = self._get_player_game_logs_from_season_page(player, season)
                    if game_logs:
                        enhanced_player['game_logs'] = game_logs
                        enhanced_player['total_games_with_logs'] = len(game_logs)
                        
                        # Calculate per-game averages from actual game logs
                        enhanced_player.update(self._calculate_per_game_stats_from_logs(game_logs, position))
                
                enhanced_players.append(enhanced_player)
                
            except Exception as e:
                print(f"   [WARNING] Failed to enhance data for {player.get('player', 'Unknown')}: {e}")
                enhanced_players.append(player)  # Use basic stats as fallback
        
        print(f"   [COMPLETE] Processed {len(enhanced_players)} {position} players with enhanced data")
        return enhanced_players
    
    def _get_player_game_logs_from_season_page(self, player: Dict[str, Any], season: str) -> List[Dict[str, Any]]:
        """
        Extract player ID from season stats page and get their actual game logs
        This will scrape the actual game-by-game performance data
        """
        try:
            player_name = player.get('player', '')
            
            # For now, we need to extract the player ID from the season stats page
            # This is a simplified approach - we'll need to parse the HTML to get player links
            # Let's implement a method to get player IDs first
            
            player_id = self._extract_player_id_from_name(player_name)
            if not player_id:
                print(f"   [WARNING] Could not extract player ID for {player_name}")
                return []
            
            # Get actual game logs using the player ID
            game_logs = self.get_player_game_log(player_id, season)
            
            return game_logs
            
        except Exception as e:
            print(f"   [WARNING] Could not get game logs for {player.get('player', 'Unknown')}: {e}")
            return []
    
    def _extract_player_id_from_name(self, player_name: str) -> Optional[str]:
        """
        Convert player name to Pro Football Reference player ID format
        PFR uses format: LastnameFirstname00 (with numbers for duplicates)
        """
        try:
            if not player_name or player_name == "League Average":
                return None
            
            # Clean the name
            name_parts = player_name.replace("'", "").replace(".", "").replace("-", "").split()
            if len(name_parts) < 2:
                return None
            
            first_name = name_parts[0]
            last_name = name_parts[-1]  # Handle middle names
            
            # PFR format: first 4 chars of last name + first 2 chars of first name + 00
            last_part = last_name[:4].lower()
            first_part = first_name[:2].lower()
            
            # Most players use 00, some use 01, 02 for duplicates
            player_id = f"{last_part}{first_part}00"
            
            return player_id
            
        except Exception as e:
            print(f"   [WARNING] Error extracting player ID from {player_name}: {e}")
            return None
    
    def get_enhanced_player_with_game_logs(self, position: str = "QB", season: str = None, max_players: int = None) -> List[Dict[str, Any]]:
        """
        Get enhanced player statistics with ACTUAL game-by-game logs
        
        Args:
            position: Player position (QB, RB, WR, TE, K)
            season: Season year (default: current year)
            max_players: Maximum number of players (None = all players)
        """
        if season is None:
            season = str(datetime.now().year)
        
        print(f"   [INFO] Getting {position} players with ACTUAL game logs for {season} season...")
        
        # First get basic season stats for ALL players
        basic_stats = self.get_player_season_stats(position, season)
        
        if not basic_stats:
            return []
        
        # Process players
        players_to_process = basic_stats if max_players is None else basic_stats[:max_players]
        total_players = len(players_to_process)
        
        print(f"   [INFO] Processing ACTUAL game logs for {total_players} {position} players...")
        print(f"   [INFO] This will take approximately {(total_players * 3.0) / 60:.1f} minutes with rate limiting...")
        
        enhanced_players = []
        
        for i, player in enumerate(players_to_process):
            try:
                enhanced_player = player.copy()
                player_name = player.get('player', 'Unknown')
                
                if i % 5 == 0 or i == total_players - 1:  # Progress every 5 players for game logs
                    print(f"   [PROGRESS] Processing game logs {i+1}/{total_players}: {player_name}")
                
                # Add calculated advanced stats from season totals
                enhanced_player.update(self._calculate_advanced_stats(player, position))
                enhanced_player.update(self._calculate_efficiency_metrics(player, position))
                
                # Get ACTUAL game logs
                player_id = self._extract_player_id_from_name(player_name)
                if player_id:
                    try:
                        game_logs = self.get_player_game_log(player_id, season)
                        if game_logs:
                            enhanced_player['game_logs'] = game_logs
                            enhanced_player['total_games_logged'] = len(game_logs)
                            
                            # Calculate detailed per-game stats from actual logs
                            enhanced_player.update(self._calculate_detailed_per_game_stats(game_logs, position))
                            
                            print(f"   [SUCCESS] Got {len(game_logs)} game logs for {player_name}")
                        else:
                            print(f"   [WARNING] No game logs found for {player_name} (ID: {player_id})")
                    except Exception as e:
                        print(f"   [WARNING] Failed to get game logs for {player_name}: {e}")
                else:
                    print(f"   [WARNING] Could not generate player ID for {player_name}")
                
                enhanced_players.append(enhanced_player)
                
            except Exception as e:
                print(f"   [ERROR] Failed to process {player.get('player', 'Unknown')}: {e}")
                enhanced_players.append(player)  # Use basic stats as fallback
        
        print(f"   [COMPLETE] Processed {len(enhanced_players)} {position} players with game log attempts")
        return enhanced_players
    
    def _calculate_detailed_per_game_stats(self, game_logs: List[Dict[str, Any]], position: str) -> Dict[str, Any]:
        """Calculate detailed per-game statistics from actual game logs"""
        detailed_stats = {}
        
        if not game_logs:
            return detailed_stats
        
        try:
            games_count = len(game_logs)
            
            # Aggregate all numeric stats from game logs
            stat_totals = {}
            stat_counts = {}
            
            for game in game_logs:
                for key, value in game.items():
                    if isinstance(value, (int, float)) and key not in ['game_number', 'player_id']:
                        if key not in stat_totals:
                            stat_totals[key] = 0
                            stat_counts[key] = 0
                        
                        stat_totals[key] += value
                        stat_counts[key] += 1
            
            # Calculate averages for all stats
            for stat, total in stat_totals.items():
                count = stat_counts[stat]
                if count > 0:
                    detailed_stats[f'avg_{stat}_per_game'] = round(total / count, 2)
            
            # Calculate game-by-game consistency
            for stat in ['yds', 'td', 'att', 'cmp', 'rec']:
                if stat in stat_totals:
                    values = [game.get(stat, 0) for game in game_logs if game.get(stat) is not None]
                    if len(values) > 1:
                        consistency = self._calculate_consistency_score_from_values(values)
                        detailed_stats[f'{stat}_consistency'] = consistency
            
            # Add game log metadata
            detailed_stats['games_with_logs'] = games_count
            detailed_stats['has_actual_game_logs'] = True
            
            # Position-specific calculations
            if position == "QB":
                # QB-specific game log analysis
                passing_games = [g for g in game_logs if g.get('att', 0) > 0]
                if passing_games:
                    detailed_stats['games_with_passing'] = len(passing_games)
                    
                    # Calculate best/worst games
                    if len(passing_games) > 0:
                        best_yds_game = max(passing_games, key=lambda x: x.get('yds', 0))
                        detailed_stats['best_passing_yards_game'] = best_yds_game.get('yds', 0)
                        
                        worst_yds_game = min(passing_games, key=lambda x: x.get('yds', 0))
                        detailed_stats['worst_passing_yards_game'] = worst_yds_game.get('yds', 0)
            
            elif position == "RB":
                # RB-specific game log analysis
                rushing_games = [g for g in game_logs if g.get('att', 0) > 0]
                if rushing_games:
                    detailed_stats['games_with_rushing'] = len(rushing_games)
                    
                    if len(rushing_games) > 0:
                        best_yds_game = max(rushing_games, key=lambda x: x.get('yds', 0))
                        detailed_stats['best_rushing_yards_game'] = best_yds_game.get('yds', 0)
            
            elif position in ["WR", "TE"]:
                # WR/TE-specific game log analysis
                receiving_games = [g for g in game_logs if g.get('rec', 0) > 0]
                if receiving_games:
                    detailed_stats['games_with_receptions'] = len(receiving_games)
                    
                    if len(receiving_games) > 0:
                        best_yds_game = max(receiving_games, key=lambda x: x.get('yds', 0))
                        detailed_stats['best_receiving_yards_game'] = best_yds_game.get('yds', 0)
        
        except Exception as e:
            print(f"   [WARNING] Error calculating detailed per-game stats: {e}")
        
        return detailed_stats
    
    def _calculate_consistency_score_from_values(self, values: List[float]) -> float:
        """Calculate consistency score from a list of values"""
        try:
            if len(values) < 2:
                return 0.0
            
            mean_val = sum(values) / len(values)
            if mean_val == 0:
                return 0.0
            
            # Calculate coefficient of variation
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            cv = std_dev / mean_val
            
            # Convert to consistency score (higher = more consistent)
            consistency_score = max(0, 1 - cv)
            return round(consistency_score, 3)
            
        except Exception:
            return 0.0
    
    def _calculate_per_game_stats_from_logs(self, game_logs: List[Dict[str, Any]], position: str) -> Dict[str, Any]:
        """Calculate detailed per-game statistics from game logs"""
        per_game_stats = {}
        
        if not game_logs:
            return per_game_stats
        
        try:
            games_count = len(game_logs)
            
            # Aggregate stats from all games
            total_stats = {}
            for game in game_logs:
                for key, value in game.items():
                    if key.startswith('game_') and isinstance(value, (int, float)):
                        stat_name = key.replace('game_', '')
                        total_stats[stat_name] = total_stats.get(stat_name, 0) + value
            
            # Calculate averages
            for stat, total in total_stats.items():
                per_game_stats[f'avg_{stat}_per_game'] = round(total / games_count, 2)
            
            # Position-specific per-game calculations
            if position == "QB" and 'att' in total_stats:
                per_game_stats['avg_attempts_per_game'] = round(total_stats['att'] / games_count, 1)
                if 'cmp' in total_stats:
                    per_game_stats['avg_completions_per_game'] = round(total_stats['cmp'] / games_count, 1)
            
            elif position == "RB" and 'att' in total_stats:
                per_game_stats['avg_carries_per_game'] = round(total_stats['att'] / games_count, 1)
            
            elif position in ["WR", "TE"] and 'rec' in total_stats:
                per_game_stats['avg_receptions_per_game'] = round(total_stats['rec'] / games_count, 1)
            
            # Add consistency metrics
            if 'yds' in total_stats:
                per_game_stats['total_games_analyzed'] = games_count
                per_game_stats['season_consistency_score'] = self._calculate_consistency_score(game_logs, 'game_yds')
        
        except Exception as e:
            print(f"   [WARNING] Error calculating per-game stats: {e}")
        
        return per_game_stats
    
    def _calculate_consistency_score(self, game_logs: List[Dict[str, Any]], stat_key: str) -> float:
        """Calculate a consistency score based on game-to-game variance"""
        try:
            values = [game.get(stat_key, 0) for game in game_logs if game.get(stat_key) is not None]
            
            if len(values) < 2:
                return 0.0
            
            mean_val = sum(values) / len(values)
            if mean_val == 0:
                return 0.0
            
            # Calculate coefficient of variation (lower = more consistent)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            cv = std_dev / mean_val
            
            # Convert to consistency score (higher = more consistent)
            consistency_score = max(0, 1 - cv)
            return round(consistency_score, 3)
            
        except Exception:
            return 0.0
    
    def _calculate_advanced_stats(self, player: Dict[str, Any], position: str) -> Dict[str, Any]:
        """Calculate advanced statistics from basic stats"""
        advanced = {}
        
        try:
            if position == "QB":
                # QB advanced stats
                att = player.get('att', 0)
                cmp = player.get('cmp', 0)
                yds = player.get('yds', 0)
                td = player.get('td', 0)
                int_thrown = player.get('int', 0)
                
                if att > 0:
                    advanced['completion_pct'] = round((cmp / att) * 100, 1)
                    advanced['yards_per_attempt'] = round(yds / att, 2)
                    advanced['td_pct'] = round((td / att) * 100, 2)
                    advanced['int_pct'] = round((int_thrown / att) * 100, 2)
                
                if cmp > 0:
                    advanced['yards_per_completion'] = round(yds / cmp, 2)
            
            elif position == "RB":
                # RB advanced stats
                att = player.get('att', 0)
                yds = player.get('yds', 0)
                td = player.get('td', 0)
                
                if att > 0:
                    advanced['yards_per_carry'] = round(yds / att, 2)
                    advanced['td_per_carry'] = round(td / att, 4)
                
                # Add receiving stats if available
                rec = player.get('rec', 0)
                rec_yds = player.get('rec_yds', 0)
                if rec > 0:
                    advanced['yards_per_reception'] = round(rec_yds / rec, 2)
            
            elif position in ["WR", "TE"]:
                # WR/TE advanced stats
                rec = player.get('rec', 0)
                yds = player.get('yds', 0)
                td = player.get('td', 0)
                tgt = player.get('tgt', 0)  # targets if available
                
                if rec > 0:
                    advanced['yards_per_reception'] = round(yds / rec, 2)
                    advanced['td_per_reception'] = round(td / rec, 4)
                
                if tgt > 0:
                    advanced['catch_pct'] = round((rec / tgt) * 100, 1)
                    advanced['yards_per_target'] = round(yds / tgt, 2)
            
            elif position == "K":
                # Kicker advanced stats
                fgm = player.get('fgm', 0)
                fga = player.get('fga', 0)
                xpm = player.get('xpm', 0)
                xpa = player.get('xpa', 0)
                
                if fga > 0:
                    advanced['fg_pct'] = round((fgm / fga) * 100, 1)
                
                if xpa > 0:
                    advanced['xp_pct'] = round((xpm / xpa) * 100, 1)
        
        except Exception as e:
            print(f"   [WARNING] Error calculating advanced stats: {e}")
        
        return advanced
    
    def _calculate_efficiency_metrics(self, player: Dict[str, Any], position: str) -> Dict[str, Any]:
        """Calculate efficiency and fantasy-relevant metrics"""
        efficiency = {}
        
        try:
            games = player.get('g', 1)  # games played, default to 1 to avoid division by zero
            
            if games > 0:
                # Per-game averages
                if position == "QB":
                    yds = player.get('yds', 0)
                    td = player.get('td', 0)
                    efficiency['yards_per_game'] = round(yds / games, 1)
                    efficiency['td_per_game'] = round(td / games, 2)
                
                elif position == "RB":
                    yds = player.get('yds', 0)
                    td = player.get('td', 0)
                    efficiency['yards_per_game'] = round(yds / games, 1)
                    efficiency['td_per_game'] = round(td / games, 2)
                
                elif position in ["WR", "TE"]:
                    rec = player.get('rec', 0)
                    yds = player.get('yds', 0)
                    td = player.get('td', 0)
                    efficiency['rec_per_game'] = round(rec / games, 1)
                    efficiency['yards_per_game'] = round(yds / games, 1)
                    efficiency['td_per_game'] = round(td / games, 2)
                
                elif position == "K":
                    pts = player.get('pts', 0)
                    efficiency['points_per_game'] = round(pts / games, 1)
        
        except Exception as e:
            print(f"   [WARNING] Error calculating efficiency metrics: {e}")
        
        return efficiency
    
    def get_player_game_log(self, player_id: str, season: str = None) -> List[Dict[str, Any]]:
        """Get detailed game logs for a player"""
        if season is None:
            season = str(datetime.now().year)
        
        url = f"{self.base_url}/players/{player_id[0]}/{player_id}/gamelog/{season}/"
        
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_game_log_table(soup, player_id)
        except Exception as e:
            raise Exception(f"Failed to get game log for player {player_id}: {str(e)}")
    
    def _parse_game_log_table(self, soup: BeautifulSoup, player_id: str) -> List[Dict[str, Any]]:
        """Parse game log table from PFR page with complex multi-level headers"""
        games = []
        
        # Find the game log table (usually has id 'stats')
        table = soup.find('table', {'id': 'stats'})
        if not table:
            return games
        
        # Get headers - PFR has complex multi-level header structure
        thead = table.find('thead')
        if not thead:
            return games
        
        # Parse multi-level headers
        header_rows = thead.find_all('tr')
        if len(header_rows) < 2:
            return games
        
        # Get the main category headers (Passing, Rushing, etc.)
        category_row = header_rows[0] if len(header_rows) > 1 else None
        # Get the specific stat headers
        stat_row = header_rows[-1]  # Last row has the actual stat names
        
        # Build combined headers
        headers = []
        category_headers = []
        
        if category_row:
            for th in category_row.find_all(['th', 'td']):
                colspan = int(th.get('colspan', 1))
                category = th.get_text(strip=True)
                category_headers.extend([category] * colspan)
        
        # Get stat names
        stat_headers = [th.get_text(strip=True) for th in stat_row.find_all(['th', 'td'])]
        
        # Combine category and stat names
        for i, stat in enumerate(stat_headers):
            if i < len(category_headers) and category_headers[i]:
                # Create combined header like 'passing_att', 'rushing_yds', etc.
                category = category_headers[i].lower().replace(' ', '_')
                stat_clean = stat.lower().replace(' ', '_').replace('%', 'pct').replace('/', '_')
                if category and category != stat_clean:
                    combined_header = f"{category}_{stat_clean}"
                else:
                    combined_header = stat_clean
            else:
                combined_header = stat.lower().replace(' ', '_').replace('%', 'pct').replace('/', '_')
            
            headers.append(combined_header)
        
        if not headers:
            return games
        
        # Get data rows
        tbody = table.find('tbody')
        if not tbody:
            return games
        
        for row in tbody.find_all('tr'):
            # Skip header rows within tbody
            if row.get('class') and 'thead' in row.get('class'):
                continue
            
            cells = row.find_all(['td', 'th'])
            if len(cells) == 0:
                continue
            
            game_data = {'player_id': player_id}
            
            # Parse each cell
            for i, cell in enumerate(cells):
                if i < len(headers):
                    header = headers[i]
                    value = cell.get_text(strip=True)
                    
                    # Convert numeric values
                    if value and value != '' and value != '--':
                        # Handle special cases
                        if '/' in value and header not in ['date', 'opp', 'result']:
                            # This might be a fraction like "23/35" for completions/attempts
                            game_data[header] = value
                        elif value.replace('.', '').replace('-', '').replace(',', '').isdigit():
                            try:
                                clean_value = value.replace(',', '')
                                game_data[header] = float(clean_value) if '.' in clean_value else int(clean_value)
                            except ValueError:
                                game_data[header] = value
                        else:
                            game_data[header] = value
            
            # Only add games with meaningful data (has date or opponent)
            if game_data.get('date') or game_data.get('opp') or len(game_data) > 3:
                games.append(game_data)
        
        return games
    
    # ==================== Advanced Team Stats ====================
    
    def get_team_advanced_stats(self, season: str = None) -> List[Dict[str, Any]]:
        """Get advanced team statistics"""
        if season is None:
            season = str(datetime.now().year)
        
        url = f"{self.base_url}/years/{season}/opp.htm"
        
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_team_stats_table(soup)
        except Exception as e:
            raise Exception(f"Failed to get team advanced stats: {str(e)}")
    
    def _parse_team_stats_table(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse team stats table"""
        teams = []
        
        # Find team stats table - it's actually called 'team_stats'
        table = soup.find('table', {'id': 'team_stats'})
        if not table:
            return teams
        
        # Get headers - PFR has complex header structure
        thead = table.find('thead')
        if not thead:
            return teams
        
        # Get the last header row which has the actual column names
        header_rows = thead.find_all('tr')
        headers = []
        if header_rows:
            # Use the last row for headers as it has the most specific column names
            last_row = header_rows[-1]
            headers = [th.get_text(strip=True) for th in last_row.find_all(['th', 'td'])]
        
        if not headers:
            return teams
        
        # Get data rows
        tbody = table.find('tbody')
        if not tbody:
            return teams
        
        for row in tbody.find_all('tr'):
            # Skip header rows within tbody
            if row.get('class') and 'thead' in row.get('class'):
                continue
                
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:  # Need at least rank, team, and one stat
                continue
            
            team_data = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    header = headers[i].lower().replace(' ', '_').replace('%', 'pct').replace('/', '_')
                    # Clean up header names
                    header = header.replace('(', '').replace(')', '').replace('-', '_')
                    value = cell.get_text(strip=True)
                    
                    # Convert numeric values
                    if value and value != '' and value != '--':
                        if value.replace('.', '').replace('-', '').replace(',', '').isdigit():
                            try:
                                clean_value = value.replace(',', '')
                                team_data[header] = float(clean_value) if '.' in clean_value else int(clean_value)
                            except ValueError:
                                team_data[header] = value
                        else:
                            team_data[header] = value
            
            # Look for team name in various possible columns
            team_name = None
            for key, value in team_data.items():
                if isinstance(value, str) and len(value) > 3 and any(word in value.lower() for word in ['texans', 'seahawks', 'eagles', 'cowboys', 'patriots', 'packers', 'steelers', 'ravens', 'chiefs', 'bills']):
                    team_name = value
                    team_data['team'] = team_name
                    break
            
            if team_name or team_data.get('tm') or len(team_data) > 3:
                teams.append(team_data)
        
        return teams
    
    # ==================== Player Season Stats ====================
    
    def get_player_season_stats(self, position: str = "QB", season: str = None) -> List[Dict[str, Any]]:
        """Get season stats for players by position"""
        if season is None:
            season = str(datetime.now().year)
        
        # Map positions to PFR URLs
        position_urls = {
            'QB': f"/years/{season}/passing.htm",
            'RB': f"/years/{season}/rushing.htm", 
            'WR': f"/years/{season}/receiving.htm",
            'TE': f"/years/{season}/receiving.htm",
            'K': f"/years/{season}/kicking.htm",
            'DEF': f"/years/{season}/opp.htm"
        }
        
        url_path = position_urls.get(position.upper())
        if not url_path:
            raise ValueError(f"Unsupported position: {position}")
        
        url = f"{self.base_url}{url_path}"
        
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_player_stats_table(soup, position)
        except Exception as e:
            raise Exception(f"Failed to get {position} stats: {str(e)}")
    
    def _parse_player_stats_table(self, soup: BeautifulSoup, position: str) -> List[Dict[str, Any]]:
        """Parse player stats table"""
        players = []
        
        # Find the main stats table (varies by position)
        table_ids = ['passing', 'rushing', 'receiving', 'kicking', 'team_stats']
        table = None
        
        for table_id in table_ids:
            table = soup.find('table', {'id': table_id})
            if table:
                break
        
        if not table:
            return players
        
        # Get headers
        thead = table.find('thead')
        if not thead:
            return players
        
        header_rows = thead.find_all('tr')
        headers = []
        for row in header_rows:
            row_headers = [th.get_text(strip=True) for th in row.find_all(['th', 'td'])]
            if row_headers and len(row_headers) > len(headers):
                headers = row_headers
        
        # Get data rows
        tbody = table.find('tbody')
        if not tbody:
            return players
        
        for row in tbody.find_all('tr'):
            # Skip header rows within tbody
            if row.get('class') and 'thead' in row.get('class'):
                continue
            
            cells = row.find_all(['td', 'th'])
            if len(cells) != len(headers):
                continue
            
            player_data = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    header = headers[i].lower().replace(' ', '_').replace('%', 'pct')
                    value = cell.get_text(strip=True)
                    
                    # Convert numeric values
                    if value and value != '' and value != '--':
                        if value.replace('.', '').replace('-', '').replace(',', '').isdigit():
                            try:
                                clean_value = value.replace(',', '')
                                player_data[header] = float(clean_value) if '.' in clean_value else int(clean_value)
                            except ValueError:
                                player_data[header] = value
                        else:
                            player_data[header] = value
            
            # Only include players if they have a name/player field
            if not (player_data.get('player') or player_data.get('name')):
                continue
            
            # For receiving stats, filter by actual position from the 'pos' column
            if position in ['WR', 'TE'] and 'pos' in player_data:
                actual_position = str(player_data['pos']).upper().strip()
                # Skip if this player doesn't match the requested position
                if position == 'WR' and actual_position != 'WR':
                    continue
                elif position == 'TE' and actual_position != 'TE':
                    continue
            
            # Set the position for this player
            player_data['position'] = position
            players.append(player_data)
        
        return players
    
    # ==================== Weekly Matchup Data ====================
    
    def get_weekly_matchups(self, season: str = None, week: int = 1) -> List[Dict[str, Any]]:
        """Get weekly matchup data with game details"""
        if season is None:
            season = str(datetime.now().year)
        
        url = f"{self.base_url}/years/{season}/week_{week}.htm"
        
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_weekly_matchups(soup, season, week)
        except Exception as e:
            raise Exception(f"Failed to get week {week} matchups: {str(e)}")
    
    def _parse_weekly_matchups(self, soup: BeautifulSoup, season: str, week: int) -> List[Dict[str, Any]]:
        """Parse weekly matchup data"""
        matchups = []
        
        # Find game summaries
        game_summaries = soup.find_all('div', class_='game_summary')
        
        for game_div in game_summaries:
            matchup = {
                'season': season,
                'week': week,
                'source': 'pro_football_reference'
            }
            
            # Get teams
            teams = game_div.find_all('tr')
            if len(teams) >= 2:
                # Away team (first row)
                away_row = teams[0]
                away_team_cell = away_row.find('td')
                if away_team_cell:
                    matchup['away_team'] = away_team_cell.get_text(strip=True)
                
                # Home team (second row)  
                home_row = teams[1]
                home_team_cell = home_row.find('td')
                if home_team_cell:
                    matchup['home_team'] = home_team_cell.get_text(strip=True)
            
            # Get scores if available
            score_cells = game_div.find_all('td', class_='right')
            if len(score_cells) >= 2:
                try:
                    matchup['away_score'] = int(score_cells[0].get_text(strip=True))
                    matchup['home_score'] = int(score_cells[1].get_text(strip=True))
                except ValueError:
                    pass
            
            # Get game date/time
            date_elem = game_div.find('td', class_='right gamelink')
            if date_elem:
                matchup['game_date'] = date_elem.get_text(strip=True)
            
            if matchup.get('away_team') and matchup.get('home_team'):
                matchups.append(matchup)
        
        return matchups