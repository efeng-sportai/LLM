"""
Data Population Service
Automatically scrapes Sleeper data and saves to MongoDB as Training Data
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from app.services.sports_scraper import SportsScraper
from app.database import get_training_data_collection
from app.config import settings
from app.utils.season_utils import get_smart_season_defaults, SeasonDetector
import json

# Smart season detection
season_defaults = get_smart_season_defaults()
CURRENT_YEAR = season_defaults["season"]

class DataPopulator:
    """Service for populating MongoDB with sports data from Sleeper as Training Data"""
    
    def __init__(self):
        self.scraper = SportsScraper()
        self.training_collection = None
    
    def _get_training_collection(self):
        """Get MongoDB training data collection"""
        if self.training_collection is None:
            self.training_collection = get_training_data_collection()
        return self.training_collection
    
    def _convert_to_training_data(
        self,
        data: Dict[str, Any],
        prompt: str,
        response: str,
        context: Optional[str] = None,
        category: Optional[str] = None,
        source_type: str = "sports_scraper",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convert scraped data to training data format"""
        return {
            "prompt": prompt,
            "response": response,
            "context": context or f"Sports data from {source_type}",
            "category": category or "sports",
            "difficulty_level": "medium",
            "source_type": source_type,
            "metadata": {
                "scraped_at": datetime.utcnow().isoformat(),
                "raw_data": json.dumps(data) if isinstance(data, dict) else str(data),
                **(metadata or {})
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
    
    async def save_training_data(
        self,
        prompt: str,
        response: str,
        context: Optional[str] = None,
        category: Optional[str] = None,
        source_type: str = "sports_scraper",
        metadata: Optional[Dict[str, Any]] = None,
        update_existing: bool = True
    ) -> str:
        """
        Save data as training data
        By default, updates existing entries with same prompt/category/source_type instead of creating duplicates
        """
        training_entry = self._convert_to_training_data(
            {},  # Empty raw data, metadata has the actual data
            prompt,
            response,
            context,
            category,
            source_type,
            metadata
        )
        collection = self._get_training_collection()
        
        if update_existing:
            # Check if entry with same prompt/category/source_type exists
            existing = await collection.find_one({
                "prompt": prompt,
                "category": category or "sports",
                "source_type": source_type
            })
            
            if existing:
                # Update existing entry
                training_entry["updated_at"] = datetime.utcnow()
                await collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": training_entry}
                )
                return str(existing["_id"])
        
        # Insert new entry
        result = await collection.insert_one(training_entry)
        return str(result.inserted_id)
    
    async def save_batch_training_data(self, training_entries: List[Dict[str, Any]]) -> List[str]:
        """Save multiple training data entries"""
        collection = self._get_training_collection()
        result = await collection.insert_many(training_entries)
        return [str(id) for id in result.inserted_ids]
    
    # ==================== Sleeper Population Methods ====================
    
    async def populate_sleeper_user(self, username: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Populate database with Sleeper user data and their leagues as training data"""
        results = {
            "user_id": None,
            "leagues": [],
            "errors": []
        }
        
        try:
            # Get user
            user_data = self.scraper.get_sleeper_user(username, user_id)
            user_id = user_data.get("user_id") or user_data.get("_id")
            username = user_data.get("username", username or str(user_id))
            results["user_id"] = user_id
            
            # Save user as training data
            user_prompt = f"Who is the Sleeper user {username}?"
            user_response = f"User: {username} (ID: {user_id})\nDisplay Name: {user_data.get('display_name', 'N/A')}"
            
            user_training_id = await self.save_training_data(
                prompt=user_prompt,
                response=user_response,
                context=f"Sleeper user {username}",
                category="user_info",
                source_type="sleeper_scraper",
                metadata={"user_data": user_data, "user_id": user_id}
            )
            
            # Get and save leagues
            try:
                leagues = self.scraper.get_sleeper_leagues(user_id)
                for league in leagues:
                    league_id = league.get("league_id")
                    if league_id:
                        try:
                            league_data = self.scraper.get_sleeper_league(league_id)
                            league_name = league_data.get("name", "Unknown League")
                            
                            # Create training data for league
                            league_prompt = f"What is the {league_name} Sleeper league?"
                            league_response = f"League: {league_name}\nSeason: {league_data.get('season', 'N/A')}\nTotal Rosters: {league_data.get('total_rosters', 'N/A')}"
                            
                            league_training_id = await self.save_training_data(
                                prompt=league_prompt,
                                response=league_response,
                                context=f"Sleeper league {league_name}",
                                category="league_info",
                                source_type="sleeper_scraper",
                                metadata={
                                    "league_id": league_id,
                                    "user_id": user_id,
                                    "raw_league_data": league_data
                                }
                            )
                            results["leagues"].append({
                                "league_id": league_id,
                                "training_data_id": league_training_id,
                                "name": league_name
                            })
                        except Exception as e:
                            results["errors"].append(f"Failed to fetch league {league_id}: {str(e)}")
            except Exception as e:
                results["errors"].append(f"Failed to fetch leagues: {str(e)}")
            
            return results
        except Exception as e:
            raise Exception(f"Failed to populate Sleeper user: {str(e)}")
    
    async def populate_sleeper_league(self, league_id: str, include_rosters: bool = True, include_matchups: bool = True) -> Dict[str, Any]:
        """Populate database with complete Sleeper league data as training data"""
        results = {
            "league_id": league_id,
            "league_training_id": None,
            "rosters": [],
            "matchups": [],
            "transactions": [],
            "errors": []
        }
        
        try:
            # Get league
            league_data = self.scraper.get_sleeper_league(league_id)
            league_name = league_data.get("name", "Unknown League")
            
            # Save league as training data
            league_prompt = f"Tell me about the {league_name} Sleeper league?"
            league_response = f"League: {league_name}\nSeason: {league_data.get('season', 'N/A')}\nTotal Rosters: {league_data.get('total_rosters', 'N/A')}\nSettings: {json.dumps(league_data.get('settings', {}), indent=2)}"
            
            league_training_id = await self.save_training_data(
                prompt=league_prompt,
                response=league_response,
                context=f"Sleeper league {league_name}",
                category="league_info",
                source_type="sleeper_scraper",
                metadata={"league_id": league_id, "raw_league_data": league_data}
            )
            results["league_training_id"] = league_training_id
            
            # Get rosters
            if include_rosters:
                try:
                    rosters = self.scraper.get_sleeper_rosters(league_id)
                    roster_prompt = f"What are the rosters for the {league_name} Sleeper league?"
                    roster_response = f"{league_name} has {len(rosters)} rosters.\nRoster data available for analysis."
                    
                    roster_training_id = await self.save_training_data(
                        prompt=roster_prompt,
                        response=roster_response,
                        context=f"Sleeper rosters for {league_name}",
                        category="rosters",
                        source_type="sleeper_scraper",
                        metadata={"league_id": league_id, "roster_count": len(rosters), "raw_rosters": rosters}
                    )
                    results["rosters"].append({
                        "training_data_id": roster_training_id,
                        "roster_count": len(rosters)
                    })
                except Exception as e:
                    results["errors"].append(f"Failed to fetch rosters: {str(e)}")
            
            # Get matchups
            if include_matchups:
                try:
                    matchups = self.scraper.get_sleeper_matchups(league_id)
                    matchup_prompt = f"What are the current matchups for the {league_name} Sleeper league?"
                    matchup_response = f"{league_name} has {len(matchups)} active matchups this week."
                    
                    matchup_training_id = await self.save_training_data(
                        prompt=matchup_prompt,
                        response=matchup_response,
                        context=f"Sleeper matchups for {league_name}",
                        category="matchups",
                        source_type="sleeper_scraper",
                        metadata={"league_id": league_id, "matchup_count": len(matchups), "raw_matchups": matchups}
                    )
                    results["matchups"].append({
                        "training_data_id": matchup_training_id,
                        "matchup_count": len(matchups)
                    })
                except Exception as e:
                    results["errors"].append(f"Failed to fetch matchups: {str(e)}")
            
            # Get transactions
            try:
                transactions = self.scraper.get_sleeper_transactions(league_id)
                if transactions:
                    trans_prompt = f"What are the recent transactions for the {league_name} Sleeper league?"
                    trans_response = f"{league_name} has {len(transactions)} recent transactions."
                    
                    trans_training_id = await self.save_training_data(
                        prompt=trans_prompt,
                        response=trans_response,
                        context=f"Sleeper transactions for {league_name}",
                        category="transactions",
                        source_type="sleeper_scraper",
                        metadata={"league_id": league_id, "transaction_count": len(transactions), "raw_transactions": transactions}
                    )
                    results["transactions"].append({
                        "training_data_id": trans_training_id,
                        "transaction_count": len(transactions)
                    })
            except Exception as e:
                results["errors"].append(f"Failed to fetch transactions: {str(e)}")
            
            return results
        except Exception as e:
            raise Exception(f"Failed to populate Sleeper league: {str(e)}")
    
    def _format_players_response(self, players_list: List[Dict[str, Any]], sport: str = "nfl", top_n: int = 100, by_stats: bool = False, ppr_type: Optional[str] = None) -> str:
        """
        Format NFL players into a readable response
        
        Args:
            players_list: List of player dictionaries
            sport: Sport abbreviation (default: 'nfl')
            top_n: Number of top players to include (default: 100)
            by_stats: If True, format as stats-based top players (default: False for trending)
            ppr_type: PPR type if by_stats=True - 'std', 'half_ppr', or 'ppr' (default: None)
        """
        if not players_list:
            return f"No NFL players found."
        
        # Filter to only include Active players with teams
        filtered_players = []
        for player in players_list:
            name = player.get("full_name")
            
            # Filter out invalid entries
            if not name or name == "Unknown Player" or "DUPLICATE" in name.upper():
                continue
            
            # Get basic info
            position = player.get("position", "N/A")
            team = player.get("team")
            status = player.get("status") or ""
            
            # CRITICAL: Only include Active status players with valid teams
            has_team = team and team != "None" and team != "N/A" and str(team) != "None" and team is not None
            
            # For NFL: Only Active players with teams
            status_upper = status.upper()
            if status_upper != "ACTIVE" or not has_team:
                continue
                
            player_info = {
                "name": name,
                "position": position,
                "team": team,
                "player_id": player.get("player_id"),
                "data": player
            }
            
            if by_stats:
                # Get stat value for stats-based sorting
                stat_value = player.get("stat_value", 0)
                player_info["stat_value"] = stat_value
                player_info["stats"] = player.get("stats", {})
            else:
                # Get trend count (from trending endpoint)
                trend_count = player.get("trend_count", 0)
                trend_type = player.get("trend_type", "add")
                player_info["trend_count"] = trend_count
                player_info["trend_type"] = trend_type
            
            filtered_players.append(player_info)
        
        # Sort by stat_value (descending) if by_stats, otherwise by trend_count
        if by_stats:
            # Get all PPR scores from stats and determine which one to use for sorting
            # Handle None values and ensure proper numeric conversion
            for player in filtered_players:
                stats = player.get("stats", {})
                if not stats:
                    stats = {}
                
                # Extract PPR scores with proper None handling
                def safe_get_float(stats_dict, key, default=0.0):
                    value = stats_dict.get(key)
                    if value is None:
                        return default
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                player["pts_std"] = safe_get_float(stats, "pts_std", 0.0)
                player["pts_half_ppr"] = safe_get_float(stats, "pts_half_ppr", 0.0)
                player["pts_ppr"] = safe_get_float(stats, "pts_ppr", 0.0)
            
            # Determine PPR type for sorting and display
            if ppr_type == "std":
                sort_key = "pts_std"
                ppr_label = "Standard"
            elif ppr_type == "half_ppr":
                sort_key = "pts_half_ppr"
                ppr_label = "Half PPR"
            elif ppr_type == "ppr":
                sort_key = "pts_ppr"
                ppr_label = "Full PPR"
            else:
                # Default to half PPR if not specified
                sort_key = "pts_half_ppr"
                ppr_label = "Half PPR"
            
            # Sort by the specified PPR type (descending order - highest first)
            # Use a safe sort function that handles None/0 values properly
            def safe_sort_key(player_dict):
                value = player_dict.get(sort_key, 0.0)
                if value is None:
                    return 0.0
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0
            
            filtered_players.sort(key=safe_sort_key, reverse=True)
            response = f"Top {min(top_n, len(filtered_players))} NFL Players (sorted by {ppr_label} fantasy points) from Sleeper:\n\n"
            response += f"Note: These are the top players based on statistical performance sorted by {ppr_label} scoring. "
            response += "Players are filtered to Active status with teams.\n\n"
            
            for i, player in enumerate(filtered_players[:top_n], 1):
                name = player["name"]
                position = player["position"]
                team = player["team"]
                # Get fantasy points value - use the sort_key we just set
                fp_value = player.get(sort_key, 0.0)
                if fp_value is None:
                    fp_value = 0.0
                try:
                    fp_value = float(fp_value)
                except (ValueError, TypeError):
                    fp_value = 0.0
                stats = player.get("stats", {})
                
                # Get key stats to display
                stat_str = ""
                if stats:
                    pass_td = stats.get("pass_td", 0)
                    rush_td = stats.get("rush_td", 0)
                    rec_td = stats.get("rec_td", 0)
                    pass_yd = stats.get("pass_yd", 0)
                    rush_yd = stats.get("rush_yd", 0)
                    rec_yd = stats.get("rec_yd", 0)
                    
                    # Build stat display based on position
                    stat_parts = []
                    if pass_td > 0:
                        stat_parts.append(f"{int(pass_td)} Pass TD")
                    if rush_td > 0:
                        stat_parts.append(f"{int(rush_td)} Rush TD")
                    if rec_td > 0:
                        stat_parts.append(f"{int(rec_td)} Rec TD")
                    if pass_yd > 0:
                        stat_parts.append(f"{int(pass_yd)} Pass Yds")
                    if rush_yd > 0:
                        stat_parts.append(f"{int(rush_yd)} Rush Yds")
                    if rec_yd > 0:
                        stat_parts.append(f"{int(rec_yd)} Rec Yds")
                    
                    if stat_parts:
                        stat_str = f" - {', '.join(stat_parts[:3])}"  # Show top 3 stats
                
                response += f"{i}. {name} ({position}) - {team} - {fp_value:.1f} FP{stat_str}\n"
        else:
            # Sort by trend_count descending (most trending first)
            filtered_players.sort(key=lambda x: x.get("trend_count", 0), reverse=True)
            trend_type_display = filtered_players[0].get('trend_type', 'add') if filtered_players else 'added'
            response = f"Top {min(top_n, len(filtered_players))} Trending NFL Players (being {trend_type_display}ed) from Sleeper:\n\n"
            response += "Note: These are the most trending players based on fantasy league activity. "
            response += "Players are filtered to Active status with teams and sorted by trending count.\n\n"
            
            for i, player in enumerate(filtered_players[:top_n], 1):
                name = player["name"]
                position = player["position"]
                team = player["team"]
                trend_count = player.get("trend_count", 0)
                player_trend_type = player.get("trend_type", "add")
                
                action = "adds" if player_trend_type == "add" else "drops"
                response += f"{i}. {name} ({position}) - {team} - {trend_count:,} {action}\n"
        
        response += f"\nTotal players: {len(filtered_players)}"
        return response
    
    async def populate_sleeper_players(
        self, 
        sport: str = "nfl", 
        top_n: int = 100,
        trend_type: str = "add",
        lookback_hours: int = 24,
        use_stats: bool = True,
        position: Optional[str] = None,
        stat_key: str = "pts_half_ppr",
        season: str = None,
        season_type: str = "regular"
    ) -> Union[str, List[str]]:
        """
        Populate database with top NFL players from Sleeper as training data
        
        Args:
            sport: Sport abbreviation (default: 'nfl')
            top_n: Number of top players to include (default: 100)
            trend_type: Type of trend if use_stats=False (default: 'add')
            lookback_hours: Hours to look back if use_stats=False (default: 24)
            use_stats: If True, use stats-based top players (default: True)
            position: Filter by position if use_stats=True (optional)
            stat_key: Stat to sort by if use_stats=True (default: 'pts_half_ppr')
            season: Season year if use_stats=True (default: current year)
            season_type: Season type if use_stats=True (default: 'regular')
        """
        if season is None:
            season = CURRENT_YEAR
        try:
            # Only support NFL
            if sport.lower() != "nfl":
                raise ValueError(f"Only NFL is supported. Received: {sport}")
            
            if use_stats:
                # Get ALL players with stats (not pre-sorted) so we can sort properly by each PPR type
                # Fetch with a large limit to ensure we get all active players
                all_players_with_stats = self.scraper.get_sleeper_top_players_by_stats(
                    sport="nfl",
                    position=position,
                    stat_key="pts_half_ppr",  # Use any stat key to fetch players, we'll re-sort later
                    limit=10000,  # Get large set to ensure we don't miss players
                    season=season,
                    season_type=season_type
                )
                
                # Create three separate documents - one for each PPR type
                training_ids = []
                ppr_types = [
                    ("std", "Standard"),
                    ("half_ppr", "Half PPR"),
                    ("ppr", "Full PPR")
                ]
                
                position_str = f" ({position})" if position else ""
                
                for ppr_type, ppr_label in ppr_types:
                    # For each PPR type, create a fresh copy and sort by that specific PPR type
                    players_for_ppr = [player.copy() for player in all_players_with_stats]
                    
                    prompt = f"What are the top NFL players{position_str} from Sleeper (sorted by {ppr_label} fantasy points)?"
                    response = self._format_players_response(
                        players_for_ppr, 
                        "nfl", 
                        top_n=top_n, 
                        by_stats=True, 
                        ppr_type=ppr_type
                    )
                    
                    training_id = await self.save_training_data(
                        prompt=prompt,
                        response=response,
                        context=f"NFL Top {top_n} Players - {ppr_label} Scoring (Sorted by {ppr_label} fantasy points)",
                        category="player_list",
                        source_type="sleeper_scraper",
                        metadata={
                            "sport": "nfl",
                            "total_players": len(all_players_with_stats),
                            "top_n": top_n,
                            "position": position,
                            "stat_key": f"pts_{ppr_type}",
                            "ppr_type": ppr_type,
                            "ppr_label": ppr_label,
                            "scoring_type": ppr_label,  # Add clear scoring type
                            "season": season,
                            "season_type": season_type,
                            "raw_players_data": players_for_ppr[:top_n]  # Store only top N for this PPR type
                        }
                    )
                    training_ids.append(training_id)
                
                # Also create a trending players document
                trending_players = self.scraper.get_sleeper_trending_players(
                    sport="nfl",
                    trend_type=trend_type,
                    lookback_hours=lookback_hours,
                    limit=top_n * 2  # Get more than needed to filter down
                )
                
                prompt = f"What are the trending NFL players on Sleeper (being {trend_type}ed)?"
                response = self._format_players_response(trending_players, "nfl", top_n=top_n, by_stats=False)
                
                trending_training_id = await self.save_training_data(
                    prompt=prompt,
                    response=response,
                    context=f"NFL Top {top_n} Trending Players (being {trend_type}ed) from Sleeper",
                    category="player_list",
                    source_type="sleeper_scraper",
                    metadata={
                        "sport": "nfl",
                        "total_trending_players": len(trending_players),
                        "top_n": top_n,
                        "trend_type": trend_type,
                        "lookback_hours": lookback_hours,
                        "scoring_type": "Trending",  # Mark as trending
                        "raw_trending_players": trending_players
                    }
                )
                training_ids.append(trending_training_id)
                
                # Now create position-specific rankings (QB, RB, WR, TE, K) - each with 3 PPR types
                # Note: DEF/team defenses are not included as Sleeper doesn't provide reliable defense data
                positions = ["QB", "RB", "WR", "TE", "K"]
                
                for position in positions:
                    # Get all players with stats for this position
                    position_players = self.scraper.get_sleeper_top_players_by_stats(
                        sport="nfl",
                        position=position,
                        stat_key="pts_half_ppr",  # Use any stat key to fetch players, we'll re-sort later
                        limit=10000,  # Get large set to ensure we don't miss players
                        season=season,
                        season_type=season_type
                    )
                    
                    # If no players found, skip creating documents for this position
                    if not position_players:
                        print(f"   [WARNING] No {position} players found, skipping {position} position rankings...")
                        continue
                    
                    # Create 3 documents for this position (one per PPR type)
                    for ppr_type, ppr_label in ppr_types:
                        # Create a fresh copy and sort by this specific PPR type
                        players_for_position_ppr = [player.copy() for player in position_players]
                        
                        prompt = f"What are the top NFL {position} players from Sleeper (sorted by {ppr_label} fantasy points)?"
                        
                        response = self._format_players_response(
                            players_for_position_ppr, 
                            "nfl", 
                            top_n=top_n, 
                            by_stats=True, 
                            ppr_type=ppr_type
                        )
                        
                        position_training_id = await self.save_training_data(
                            prompt=prompt,
                            response=response,
                            context=f"NFL Top {top_n} {position} Players - {ppr_label} Scoring (Sorted by {ppr_label} fantasy points)",
                            category="player_list",
                            source_type="sleeper_scraper",
                            metadata={
                                "sport": "nfl",
                                "total_players": len(position_players),
                                "top_n": top_n,
                                "position": position,
                                "stat_key": f"pts_{ppr_type}",
                                "ppr_type": ppr_type,
                                "ppr_label": ppr_label,
                                "scoring_type": ppr_label,
                                "season": season,
                                "season_type": season_type,
                                "raw_players_data": players_for_position_ppr[:top_n]
                            }
                        )
                        training_ids.append(position_training_id)
                
                # Return the list of IDs: 4 general (3 PPR + 1 trending) + 15 position-specific (5 positions × 3 PPR types) = 19 total
                return training_ids
            else:
                # Get trending players (this returns enriched player data as a list)
                trending_players = self.scraper.get_sleeper_trending_players(
                    sport="nfl",
                    trend_type=trend_type,
                    lookback_hours=lookback_hours,
                    limit=top_n * 2  # Get more than needed to filter down
                )
                
                prompt = f"What are the trending NFL players on Sleeper (being {trend_type}ed)?"
                response = self._format_players_response(trending_players, "nfl", top_n=top_n, by_stats=False)
                
                training_id = await self.save_training_data(
                    prompt=prompt,
                    response=response,
                    context=f"NFL trending players from Sleeper (Top {top_n}, {trend_type})",
                    category="player_list",
                    source_type="sleeper_scraper",
                    metadata={
                        "sport": "nfl",
                        "total_trending_players": len(trending_players),
                        "top_n": top_n,
                        "trend_type": trend_type,
                        "lookback_hours": lookback_hours,
                        "raw_trending_players": trending_players
                    }
                )
            
            return training_id
        except Exception as e:
            raise Exception(f"Failed to populate Sleeper players: {str(e)}")
    
    async def populate_sleeper_nfl_standings(
        self,
        season: str = None,
        season_type: str = "regular",
        grouping: str = "league"
    ) -> str:
        """
        Populate database with NFL standings from Sleeper as training data
        
        Args:
            season: Season year (default: current year)
            season_type: Season type - 'regular', 'pre', 'post' (default: 'regular')
            grouping: Grouping type - 'league', 'conference', 'division' (default: 'league')
        """
        if season is None:
            season = CURRENT_YEAR
        try:
            # Get standings from scraper
            standings = self.scraper.get_sleeper_nfl_standings(
                season=season,
                season_type=season_type,
                grouping=grouping
            )
            
            # Format the standings response
            response = self._format_standings_response(standings, grouping, season)
            
            # Create prompt
            prompt = f"What are the current NFL standings from Sleeper ({grouping} grouping)?"
            
            # Save as training data
            training_id = await self.save_training_data(
                prompt=prompt,
                response=response,
                context=f"NFL Standings - {grouping.title()} ({season})",
                category="standings",
                source_type="sleeper_scraper",
                metadata={
                    "sport": "nfl",
                    "season": season,
                    "season_type": season_type,
                    "grouping": grouping,
                    "total_teams": len(standings),
                    "raw_standings_data": standings
                }
            )
            
            return training_id
        except Exception as e:
            raise Exception(f"Failed to populate Sleeper NFL standings: {str(e)}")
    
    def _format_standings_response(
        self,
        standings: List[Dict[str, Any]],
        grouping: str = "league",
        season: str = None
    ) -> str:
        """
        Format NFL standings into a readable response
        
        Args:
            standings: List of team standings dictionaries
            grouping: Grouping type - 'league', 'conference', 'division'
            season: Season year (optional)
        """
        if not standings:
            return f"No NFL standings found."
        
        if season is None:
            season = CURRENT_YEAR
        
        # Sort by wins (descending), then by losses (ascending)
        sorted_standings = sorted(
            standings,
            key=lambda x: (x.get("wins", 0), -x.get("losses", 0), -x.get("ties", 0)),
            reverse=True
        )
        
        response = f"{season} NFL Standings ({grouping.title()}):\n\n"
        response += f"Note: Teams are sorted by wins, then by losses (ascending).\n\n"
        
        for i, team_standings in enumerate(sorted_standings, 1):
            # Handle both old and new scraper formats
            if isinstance(team_standings, str):
                continue
                
            # New scraper format: team is directly in the dict
            team_name = team_standings.get("team", "Unknown")
            wins = team_standings.get("wins", 0)
            losses = team_standings.get("losses", 0)
            ties = team_standings.get("ties", 0)
            win_pct = team_standings.get("win_pct", 0)
            
            # Format record
            if ties > 0:
                record = f"{wins}-{losses}-{ties}"
            else:
                record = f"{wins}-{losses}"
            
            # Add win percentage
            win_pct_str = f" ({win_pct:.3f})" if win_pct > 0 else ""
            
            # Get conference/division if available
            conf_div = ""
            if "conference" in team_standings and "division" in team_standings:
                conf_div = f" [{team_standings['conference']} {team_standings['division']}]"
            
            response += f"{i}. {team_name} - {record}{win_pct_str}{conf_div}\n"
        
        response += f"\nTotal teams: {len(standings)}"
        return response
    
    async def populate_sleeper_injured_players(
        self,
        sport: str = "nfl",
        injury_status: Optional[str] = None,
        status: Optional[str] = None,
        has_team: bool = True,
        separate_by_status: bool = False
    ) -> Union[str, List[str]]:
        """
        Populate database with injured/out players from Sleeper as training data
        
        Args:
            sport: Sport abbreviation (default: 'nfl')
            injury_status: Filter by injury status - 'Out', 'Questionable', 'Doubtful', etc. (optional)
            status: Filter by player status - 'Injured Reserve', 'Inactive', etc. (optional)
            has_team: Only include players with teams (default: True)
            separate_by_status: If True, create separate documents for each injury status (Out, Questionable, Doubtful, etc.)
        """
        try:
            # If separate_by_status, fetch all injured players and create separate docs
            if separate_by_status and not injury_status and not status:
                # Get ALL injured players (not filtered by specific status)
                all_injured_players = self.scraper.get_sleeper_injured_players(
                    sport=sport,
                    injury_status=None,
                    status=None,
                    has_team=has_team
                )
                
                # Group by injury status
                by_status = {}
                for player in all_injured_players:
                    player_injury_status = player.get("injury_status")
                    # Handle None/null injury status - use "None" as key
                    if not player_injury_status or player_injury_status == "None":
                        player_injury_status = "None"
                    if player_injury_status not in by_status:
                        by_status[player_injury_status] = []
                    by_status[player_injury_status].append(player)
                
                # Create separate documents for key injury statuses
                training_ids = []
                key_statuses = ["Out", "Questionable", "Doubtful", "IR", "PUP"]
                
                for status_key in key_statuses:
                    if status_key in by_status:
                        players_for_status = by_status[status_key]
                        response = self._format_injured_players_response(
                            players_for_status, 
                            injury_status=status_key, 
                            status=None
                        )
                        
                        prompt = f"What NFL players are {status_key.lower()} (injured/out) from Sleeper?"
                        
                        training_id = await self.save_training_data(
                            prompt=prompt,
                            response=response,
                            context=f"NFL Injured Players - {status_key} Status",
                            category="player_injuries",
                            source_type="sleeper_scraper",
                            metadata={
                                "sport": "nfl",
                                "injury_status": status_key,
                                "player_status": None,
                                "has_team": has_team,
                                "total_injured_players": len(players_for_status),
                                "raw_injured_players_data": players_for_status[:100]
                            }
                        )
                        training_ids.append(training_id)
                
                # Return list of IDs if multiple documents created
                return training_ids if len(training_ids) > 1 else training_ids[0] if training_ids else None
            
            # Otherwise, create a single document
            # Get injured players from scraper
            injured_players = self.scraper.get_sleeper_injured_players(
                sport=sport,
                injury_status=injury_status,
                status=status,
                has_team=has_team
            )
            
            # Format the response
            response = self._format_injured_players_response(injured_players, injury_status, status)
            
            # Create prompt based on filters
            if injury_status:
                prompt = f"What NFL players are {injury_status.lower()} (injured/out) from Sleeper?"
            elif status:
                prompt = f"What NFL players have status {status} from Sleeper?"
            else:
                prompt = "What NFL players are injured or out from Sleeper?"
            
            # Create context
            context_parts = ["NFL Injured Players"]
            if injury_status:
                context_parts.append(f"Injury Status: {injury_status}")
            if status:
                context_parts.append(f"Status: {status}")
            context = " - ".join(context_parts)
            
            # Save as training data
            training_id = await self.save_training_data(
                prompt=prompt,
                response=response,
                context=context,
                category="player_injuries",
                source_type="sleeper_scraper",
                metadata={
                    "sport": "nfl",
                    "injury_status": injury_status,
                    "player_status": status,
                    "has_team": has_team,
                    "total_injured_players": len(injured_players),
                    "raw_injured_players_data": injured_players[:100]  # Store first 100 for reference
                }
            )
            
            return training_id
        except Exception as e:
            raise Exception(f"Failed to populate Sleeper injured players: {str(e)}")
    
    def _format_injured_players_response(
        self,
        injured_players: List[Dict[str, Any]],
        injury_status: Optional[str] = None,
        status: Optional[str] = None
    ) -> str:
        """
        Format injured players into a readable response
        
        Args:
            injured_players: List of injured player dictionaries
            injury_status: Injury status filter (if any)
            status: Player status filter (if any)
        """
        if not injured_players:
            filter_str = ""
            if injury_status:
                filter_str = f" with injury status '{injury_status}'"
            elif status:
                filter_str = f" with status '{status}'"
            return f"No injured NFL players found{filter_str}."
        
        # Sort by injury status priority, then by name
        status_priority = {
            "Out": 1,
            "Doubtful": 2,
            "Questionable": 3,
            "IR": 4,
            "PUP": 5,
            "Sus": 6,
            "DNR": 7,
            "COV": 8,
            "NA": 9
        }
        
        def sort_key(player):
            injury_stat = player.get("injury_status", "") or ""
            return (
                status_priority.get(injury_stat, 99),
                player.get("full_name", "").lower()
            )
        
        sorted_players = sorted(injured_players, key=sort_key)
        
        # Build response
        filter_str = ""
        if injury_status:
            filter_str = f" (Injury Status: {injury_status})"
        elif status:
            filter_str = f" (Status: {status})"
        
        response = f"NFL Injured/Out Players{filter_str}:\n\n"
        response += "Note: Players are sorted by injury severity, then alphabetically.\n\n"
        
        # Group by injury status for better organization
        current_status = None
        for player in sorted_players:
            player_injury_status = player.get("injury_status") or "Unknown"
            player_status = player.get("status", "")
            team = player.get("team", "N/A")
            position = player.get("position", "N/A")
            name = player.get("full_name", "Unknown")
            
            # Group by injury status
            if current_status != player_injury_status:
                if current_status is not None:
                    response += "\n"
                current_status = player_injury_status
                response += f"**{player_injury_status or 'No Injury Status'}** ({player_status}):\n"
            
            # Build player line
            player_line = f"  • {name} ({position}) - {team}"
            
            # Add injury details if available
            injury_notes = player.get("injury_notes")
            injury_body = player.get("injury_body_part")
            if injury_notes or injury_body:
                details = []
                if injury_body:
                    details.append(injury_body)
                if injury_notes:
                    details.append(injury_notes)
                player_line += f" - {', '.join(details)}"
            
            response += player_line + "\n"
        
        response += f"\nTotal injured/out players: {len(injured_players)}"
        return response
    
    async def populate_nfl_player_news(
        self,
        source: str = "espn",
        limit: int = 50,
        match_to_players: bool = True,
        max_age_hours: int = 168
    ) -> Union[str, List[str]]:
        """
        Populate database with NFL player news from RSS feeds as training data (most recent articles only)
        
        Args:
            source: News source - 'espn' or 'nfl' (default: 'espn')
            limit: Maximum number of news items to fetch (default: 50)
            match_to_players: If True, match news to players and create separate documents per player (default: True)
            max_age_hours: Only include articles published within this many hours (default: 168 = 7 days = 1 week)
        """
        try:
            # Get news from RSS feed (only most recent articles)
            news_items = self.scraper.get_nfl_news_from_rss(source=source, limit=limit, max_age_hours=max_age_hours)
            
            if not news_items:
                raise Exception(f"No news items found from {source}")
            
            if match_to_players:
                # Match news to players
                player_news = self.scraper.match_news_to_players(news_items, sport="nfl")
                
                # Get all players ONCE (not inside the loop!)
                all_players = self.scraper.get_sleeper_players("nfl")
                
                # Create separate documents for players with news
                training_ids = []
                
                for player_id, matched_news in player_news.items():
                    if not matched_news:
                        continue
                    
                    # Get player info from already-fetched players dict
                    player_data = all_players.get(player_id)
                    if not player_data:
                        continue
                    
                    player_name = player_data.get("full_name", "Unknown Player")
                    team = player_data.get("team", "N/A")
                    position = player_data.get("position", "N/A")
                    
                    # Format news response
                    response = self._format_player_news_response(matched_news, player_name, team, position, source)
                    
                    # Create prompt
                    prompt = f"What is the latest news about {player_name} ({position}, {team}) from {source.upper()}?"
                    
                    # Save as training data
                    training_id = await self.save_training_data(
                        prompt=prompt,
                        response=response,
                        context=f"NFL Player News - {player_name} ({source.upper()})",
                        category="player_news",
                        source_type="sleeper_scraper",
                        metadata={
                            "sport": "nfl",
                            "player_id": player_id,
                            "player_name": player_name,
                            "team": team,
                            "position": position,
                            "news_source": source,
                            "total_news_items": len(matched_news),
                            "raw_news_data": matched_news
                        }
                    )
                    training_ids.append(training_id)
                
                # Also create a general news document
                general_response = self._format_general_news_response(news_items, source)
                general_prompt = f"What is the latest NFL news from {source.upper()}?"
                
                general_training_id = await self.save_training_data(
                    prompt=general_prompt,
                    response=general_response,
                    context=f"NFL News - {source.upper()} (General)",
                    category="player_news",
                    source_type="sleeper_scraper",
                    metadata={
                        "sport": "nfl",
                        "news_source": source,
                        "total_news_items": len(news_items),
                        "matched_players": len(player_news),
                        "raw_news_data": news_items
                    }
                )
                training_ids.append(general_training_id)
                
                return training_ids
            else:
                # Create a single general news document
                response = self._format_general_news_response(news_items, source)
                prompt = f"What is the latest NFL news from {source.upper()}?"
                
                training_id = await self.save_training_data(
                    prompt=prompt,
                    response=response,
                    context=f"NFL News - {source.upper()}",
                    category="player_news",
                    source_type="sleeper_scraper",
                    metadata={
                        "sport": "nfl",
                        "news_source": source,
                        "total_news_items": len(news_items),
                        "raw_news_data": news_items
                    }
                )
                
                return training_id
        except Exception as e:
            raise Exception(f"Failed to populate NFL player news: {str(e)}")
    
    def _format_player_news_response(
        self,
        news_items: List[Dict[str, Any]],
        player_name: str,
        team: str,
        position: str,
        source: str
    ) -> str:
        """
        Format news items for a specific player
        """
        if not news_items:
            return f"No recent news found for {player_name} from {source.upper()}."
        
        response = f"Latest news about {player_name} ({position}, {team}) from {source.upper()}:\n\n"
        
        for i, news in enumerate(news_items, 1):
            title = news.get("title", "No title")
            description = news.get("description", "")
            link = news.get("link", "")
            pubdate = news.get("pubDate", "")
            creator = news.get("creator", "")
            
            response += f"{i}. {title}\n"
            if description:
                # Truncate long descriptions
                desc = description[:200] + "..." if len(description) > 200 else description
                response += f"   {desc}\n"
            if pubdate:
                response += f"   Published: {pubdate}\n"
            if creator:
                response += f"   Author: {creator}\n"
            if link:
                response += f"   Link: {link}\n"
            response += "\n"
        
        response += f"\nTotal news items: {len(news_items)}"
        return response
    
    def _format_general_news_response(
        self,
        news_items: List[Dict[str, Any]],
        source: str
    ) -> str:
        """
        Format general NFL news items
        """
        if not news_items:
            return f"No recent news found from {source.upper()}."
        
        response = f"Latest NFL News from {source.upper()}:\n\n"
        
        for i, news in enumerate(news_items, 1):
            title = news.get("title", "No title")
            description = news.get("description", "")
            link = news.get("link", "")
            pubdate = news.get("pubDate", "")
            creator = news.get("creator", "")
            
            response += f"{i}. {title}\n"
            if description:
                # Truncate long descriptions
                desc = description[:150] + "..." if len(description) > 150 else description
                response += f"   {desc}\n"
            if pubdate:
                response += f"   Published: {pubdate}\n"
            if link:
                response += f"   Link: {link}\n"
            response += "\n"
        
        response += f"\nTotal news items: {len(news_items)}"
        return response
    
    async def populate_nfl_schedule(
        self,
        season: str = None,
        season_type: str = "regular",
        week: Optional[int] = None
    ) -> str:
        """
        Populate database with NFL schedule/matchups as training data
        
        Args:
            season: Season year (default: current year)
            season_type: Season type - 'regular', 'pre', 'post' (default: 'regular')
            week: Optional week number (default: None = all weeks)
        """
        if season is None:
            season = CURRENT_YEAR
        try:
            # Get schedule from scraper
            games = self.scraper.get_nfl_schedule(season, season_type, week)
            
            if not games:
                raise Exception("No schedule data found")
            
            # Format schedule response
            response = self._format_schedule_response(games, season, season_type, week)
            
            # Create prompt
            if week:
                prompt = f"What is the NFL schedule for {season} {season_type} season, Week {week}?"
                context = f"NFL Schedule - {season} {season_type} Week {week}"
            else:
                prompt = f"What is the NFL schedule for the {season} {season_type} season?"
                context = f"NFL Schedule - {season} {season_type} Season (All Weeks)"
            
            # Save as training data
            training_id = await self.save_training_data(
                prompt=prompt,
                response=response,
                context=context,
                category="schedule",
                source_type="sleeper_scraper",
                metadata={
                    "sport": "nfl",
                    "season": season,
                    "season_type": season_type,
                    "week": week,
                    "total_games": len(games),
                    "raw_schedule_data": games
                }
            )
            
            return training_id
        except Exception as e:
            raise Exception(f"Failed to populate NFL schedule: {str(e)}")
    
    def _format_schedule_response(
        self,
        games: List[Dict[str, Any]],
        season: str,
        season_type: str,
        week: Optional[int]
    ) -> str:
        """
        Format schedule data into human-readable response
        
        Args:
            games: List of game dictionaries
            season: Season year
            season_type: Season type
            week: Optional week number
        """
        if not games:
            return f"No games found for {season} {season_type} season" + (f", Week {week}" if week else "")
        
        # Group games by week if week is None
        if week is None:
            # Try to group by week from game data
            games_by_week = {}
            for game in games:
                game_week = game.get('week') or 'Unknown'
                if game_week not in games_by_week:
                    games_by_week[game_week] = []
                games_by_week[game_week].append(game)
            
            response_parts = []
            response_parts.append(f"NFL Schedule - {season} {season_type} Season\n")
            response_parts.append(f"Total games: {len(games)}\n\n")
            
            for game_week in sorted(games_by_week.keys(), key=lambda x: (x == 'Unknown', int(x) if isinstance(x, int) or (isinstance(x, str) and x.isdigit()) else 999)):
                week_games = games_by_week[game_week]
                response_parts.append(f"Week {game_week}:\n")
                for game in week_games:
                    away = game.get('away_team', 'TBD')
                    home = game.get('home_team', 'TBD')
                    date = game.get('date', 'TBD')
                    score = ""
                    if 'away_score' in game and 'home_score' in game:
                        score = f" ({game['away_score']}-{game['home_score']})"
                    response_parts.append(f"  {away} @ {home}{score} - {date}\n")
                response_parts.append("\n")
            
            return "".join(response_parts)
        else:
            # Single week schedule
            response_parts = []
            response_parts.append(f"NFL Schedule - {season} {season_type} Season, Week {week}\n\n")
            
            for game in games:
                away = game.get('away_team', 'TBD')
                home = game.get('home_team', 'TBD')
                date = game.get('date', 'TBD')
                score = ""
                if 'away_score' in game and 'home_score' in game:
                    score = f" ({game['away_score']}-{game['home_score']})"
                response_parts.append(f"{away} @ {home}{score} - {date}\n")
            
            return "".join(response_parts)
    
    async def populate_nfl_team_rankings(
        self,
        season: str = None,
        season_type: str = "regular",
        ranking_types: Optional[List[str]] = None
    ) -> Union[str, List[str]]:
        """
        Populate database with NFL team rankings by offense, defense, etc. as training data
        
        Args:
            season: Season year (default: current year)
            season_type: Season type - 'regular', 'pre', 'post' (default: 'regular')
            ranking_types: List of ranking types - ['offense', 'defense', 'total'] (default: all)
        """
        if season is None:
            season = CURRENT_YEAR
        if ranking_types is None:
            ranking_types = ['offense', 'defense', 'total']
        
        try:
            training_ids = []
            
            for ranking_type in ranking_types:
                try:
                    # Get team rankings from scraper (new scraper expects a list)
                    rankings_dict = self.scraper.get_nfl_team_rankings(season, season_type, [ranking_type])
                    
                    # Extract the specific ranking type from the dict
                    rankings = rankings_dict.get(ranking_type, [])
                    
                    if not rankings:
                        print(f"   [WARNING] No {ranking_type} rankings found, skipping...")
                        continue
                    
                    
                    # Format rankings response
                    response = self._format_team_rankings_response(rankings, ranking_type, season, season_type)
                    
                    if not response or "No team rankings found" in response:
                        print(f"   [WARNING] {ranking_type} rankings formatting failed, skipping...")
                        continue
                    
                    # Create prompt
                    prompt = f"What are the NFL team rankings by {ranking_type} for the {season} {season_type} season?"
                    context = f"NFL Team Rankings - {ranking_type.title()} ({season} {season_type})"
                    
                    # Save as training data
                    training_id = await self.save_training_data(
                        prompt=prompt,
                        response=response,
                        context=context,
                        category="team_rankings",
                        source_type="sleeper_scraper",
                        metadata={
                            "sport": "nfl",
                            "season": season,
                            "season_type": season_type,
                            "ranking_type": ranking_type,
                            "total_teams": len(rankings),
                            "raw_rankings_data": rankings
                        }
                    )
                    print(f"   [OK] Saved {ranking_type.title()} rankings with ID: {training_id}")
                    training_ids.append(training_id)
                except Exception as e:
                    print(f"   [ERROR] Failed to save {ranking_type} rankings: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Return single ID if only one ranking type, otherwise return list
            return training_ids if len(training_ids) > 1 else (training_ids[0] if training_ids else "")
            
        except Exception as e:
            raise Exception(f"Failed to populate NFL team rankings: {str(e)}")
    
    def _format_team_rankings_response(
        self,
        rankings: List[Dict[str, Any]],
        ranking_type: str,
        season: str,
        season_type: str
    ) -> str:
        """
        Format team rankings data into human-readable response
        
        Args:
            rankings: List of team ranking dictionaries
            ranking_type: Type of ranking ('offense', 'defense', 'total')
            season: Season year
            season_type: Season type
        """
        if not rankings:
            return f"No team rankings found for {ranking_type} in {season} {season_type} season"
        
        response_parts = []
        response_parts.append(f"NFL Team Rankings - {ranking_type.title()} ({season} {season_type})\n\n")
        
        for i, team in enumerate(rankings, 1):
            # Handle both old and new scraper formats
            if isinstance(team, str):
                # If team is a string, skip it
                continue
                
            team_name = team.get('team', 'Unknown')
            rank = team.get('rank', i)
            
            response_parts.append(f"{rank}. {team_name}")
            
            # Add specific stats based on ranking type
            if ranking_type == 'offense':
                total_yards = team.get('total_offensive_yards', 0)
                total_tds = team.get('total_offensive_tds', 0)
                response_parts.append(f"   Total Yards: {total_yards:,}, TDs: {total_tds}")
            elif ranking_type == 'defense':
                def_points = team.get('total_defensive_points', 0)
                sacks = team.get('total_sacks', 0)
                ints = team.get('total_int', 0)
                response_parts.append(f"   Defensive Points: {def_points:.1f}, Sacks: {sacks:.1f}, INTs: {ints}")
            elif ranking_type == 'total':
                wins = team.get('wins', 0)
                losses = team.get('losses', 0)
                win_pct = team.get('win_pct', 0)
                response_parts.append(f"   Record: {wins}-{losses}, Win %: {win_pct:.3f}")
            
            response_parts.append("")  # Empty line between teams
        
        return "\n".join(response_parts)
    
    async def get_population_stats(self) -> Dict[str, Any]:
        """Get statistics about populated training data"""
        collection = self._get_training_collection()
        
        stats = {
            "total_training_data": await collection.count_documents({}),
            "sleeper_training_data": await collection.count_documents({"source_type": "sleeper_scraper"}),
            "by_source": {},
            "by_category": {}
        }
        
        # Get breakdown by source
        try:
            pipeline = [
                {"$match": {"source_type": "sleeper_scraper"}},
                {"$group": {
                    "_id": "$source_type",
                    "count": {"$sum": 1}
                }}
            ]
            
            async for doc in collection.aggregate(pipeline):
                stats["by_source"][doc["_id"]] = doc["count"]
        except Exception:
            pass
        
        # Get breakdown by category
        try:
            pipeline_category = [
                {"$match": {"source_type": "sleeper_scraper"}},
                {"$group": {
                    "_id": "$category",
                    "count": {"$sum": 1}
                }}
            ]
            
            async for doc in collection.aggregate(pipeline_category):
                if doc.get("_id"):
                    stats["by_category"][doc["_id"]] = doc["count"]
        except Exception:
            pass
        
        return stats
