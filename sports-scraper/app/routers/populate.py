"""
Data Population API Router
Provides endpoints for automatically populating MongoDB with Sleeper data
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from app.services.data_populator import DataPopulator

# Get current year as default
CURRENT_YEAR = str(datetime.now().year)

router = APIRouter()
populator = DataPopulator()

# ==================== Request Models ====================

class SleeperUserRequest(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None

class SleeperLeagueRequest(BaseModel):
    league_id: str
    include_rosters: bool = True
    include_matchups: bool = True

class SleeperPlayersRequest(BaseModel):
    sport: str = "nfl"
    top_n: int = 100
    trend_type: str = "add"  # "add" or "drop" (only used if use_stats=False)
    lookback_hours: int = 24  # Only used if use_stats=False
    use_stats: bool = True  # If True, use stats-based top players instead of trending
    position: Optional[str] = None  # Filter by position (QB, RB, WR, TE, etc.) - optional
    stat_key: str = "pts_half_ppr"  # Stat to sort by (default: fantasy points half PPR)
    season: Optional[str] = None  # Season year (default: current year)
    season_type: str = "regular"  # Season type: "regular", "pre", "post"

class SleeperStandingsRequest(BaseModel):
    season: Optional[str] = None  # Season year (default: current year)
    season_type: str = "regular"  # Season type: "regular", "pre", "post"
    grouping: str = "league"  # Grouping type: "league", "conference", "division"

class SleeperInjuredPlayersRequest(BaseModel):
    sport: str = "nfl"  # Sport abbreviation
    injury_status: Optional[str] = None  # Filter by injury status: "Out", "Questionable", "Doubtful", "IR", "PUP", etc.
    status: Optional[str] = None  # Filter by player status: "Injured Reserve", "Inactive", "Physically Unable to Perform", etc.
    has_team: bool = True  # Only include players with teams
    separate_by_status: bool = False  # If True, create separate documents for each injury status (Out, Questionable, Doubtful, etc.)

class SleeperPlayerNewsRequest(BaseModel):
    source: str = "espn"  # News source: "espn" or "nfl"
    limit: int = 50  # Maximum number of news items to fetch
    match_to_players: bool = True  # If True, match news to players and create separate documents per player
    max_age_hours: int = 168  # Only include articles published within this many hours (default: 168 hours = 7 days = 1 week)

class SleeperScheduleRequest(BaseModel):
    season: Optional[str] = None  # Season year (default: current year)
    season_type: str = "regular"  # Season type: "regular", "pre", "post"
    week: Optional[int] = None  # Optional week number (default: None = all weeks)

class SleeperTeamRankingsRequest(BaseModel):
    season: Optional[str] = None  # Season year (default: current year)
    season_type: str = "regular"  # Season type: "regular", "pre", "post"
    ranking_types: Optional[List[str]] = None  # List of ranking types: ["offense", "defense", "total"] (default: all)

# ==================== Sleeper Population Endpoints ====================

@router.post("/sleeper/user")
async def populate_sleeper_user(request: SleeperUserRequest):
    """Populate database with Sleeper user data and their leagues"""
    try:
        result = await populator.populate_sleeper_user(request.username, request.user_id)
        return {
            "message": "User populated successfully",
            "status": "completed",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sleeper/league")
async def populate_sleeper_league(request: SleeperLeagueRequest):
    """Populate database with complete Sleeper league data"""
    try:
        result = await populator.populate_sleeper_league(
            request.league_id,
            request.include_rosters,
            request.include_matchups
        )
        return {
            "message": "League populated successfully",
            "status": "completed",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sleeper/players")
async def populate_sleeper_players(request: SleeperPlayersRequest):
    """Populate database with top NFL players from Sleeper (by stats or trending)"""
    try:
        # Only support NFL
        if request.sport.lower() != "nfl":
            raise HTTPException(status_code=400, detail=f"Only NFL is supported. Received: {request.sport}")
        
        season = request.season or CURRENT_YEAR
        doc_ids = await populator.populate_sleeper_players(
            "nfl", 
            request.top_n,
            request.trend_type,
            request.lookback_hours,
            request.use_stats,
            request.position,
            request.stat_key,
            season,
            request.season_type
        )
        
        # If use_stats=True, doc_ids will be a list: 4 general (3 PPR + 1 trending) + 15 position-specific (5 positions × 3 PPR types) = 19 total
        if isinstance(doc_ids, list):
            general_count = 4  # Standard, Half PPR, Full PPR, Trending
            position_count = len(doc_ids) - general_count
            return {
                "message": f"NFL players populated successfully ({len(doc_ids)} documents: {general_count} general + {position_count} position-specific)",
                "status": "completed",
                "document_ids": doc_ids,
                "document_count": len(doc_ids),
                "breakdown": {
                    "general": general_count,
                    "position_specific": position_count,
                    "positions": ["QB", "RB", "WR", "TE", "K"],
                    "ppr_types": ["Standard", "Half PPR", "Full PPR"]
                }
            }
        else:
            return {
                "message": "NFL players populated successfully",
                "status": "completed",
                "document_id": doc_ids
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sleeper/standings")
async def populate_sleeper_standings(request: SleeperStandingsRequest):
    """Populate database with NFL standings from Sleeper"""
    try:
        season = request.season or CURRENT_YEAR
        doc_id = await populator.populate_sleeper_nfl_standings(
            season,
            request.season_type,
            request.grouping
        )
        return {
            "message": "NFL standings populated successfully",
            "status": "completed",
            "document_id": doc_id,
            "grouping": request.grouping
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sleeper/injured-players")
async def populate_sleeper_injured_players(request: SleeperInjuredPlayersRequest):
    """Populate database with injured/out NFL players from Sleeper"""
    try:
        doc_ids = await populator.populate_sleeper_injured_players(
            request.sport,
            request.injury_status,
            request.status,
            request.has_team,
            request.separate_by_status
        )
        
        # If separate_by_status=True, doc_ids will be a list
        if isinstance(doc_ids, list):
            return {
                "message": "NFL injured players populated successfully (multiple documents by injury status)",
                "status": "completed",
                "document_ids": doc_ids,
                "document_count": len(doc_ids),
                "injury_statuses": ["Out", "Questionable", "Doubtful", "IR", "PUP"]
            }
        else:
            return {
                "message": "NFL injured players populated successfully",
                "status": "completed",
                "document_id": doc_ids,
                "injury_status": request.injury_status,
                "player_status": request.status
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sleeper/player-news")
async def populate_sleeper_player_news(request: SleeperPlayerNewsRequest):
    """Populate database with NFL player news from RSS feeds"""
    try:
        doc_ids = await populator.populate_nfl_player_news(
            request.source,
            request.limit,
            request.match_to_players,
            request.max_age_hours
        )
        
        # If match_to_players=True, doc_ids will be a list
        if isinstance(doc_ids, list):
            return {
                "message": f"NFL player news populated successfully ({len(doc_ids)} documents - {len(doc_ids)-1} players + 1 general)",
                "status": "completed",
                "document_ids": doc_ids,
                "document_count": len(doc_ids),
                "source": request.source
            }
        else:
            return {
                "message": "NFL player news populated successfully",
                "status": "completed",
                "document_id": doc_ids,
                "source": request.source
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sleeper/schedule")
async def populate_sleeper_schedule(request: SleeperScheduleRequest):
    """Populate database with NFL schedule/matchups"""
    try:
        season = request.season or CURRENT_YEAR
        doc_id = await populator.populate_nfl_schedule(
            season,
            request.season_type,
            request.week
        )
        return {
            "message": "NFL schedule populated successfully",
            "status": "completed",
            "document_id": doc_id,
            "season": season,
            "season_type": request.season_type,
            "week": request.week
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sleeper/team-rankings")
async def populate_sleeper_team_rankings(request: SleeperTeamRankingsRequest):
    """Populate database with NFL team rankings by offense, defense, etc."""
    try:
        season = request.season or CURRENT_YEAR
        doc_ids = await populator.populate_nfl_team_rankings(
            season,
            request.season_type,
            request.ranking_types
        )
        
        # If multiple ranking types, doc_ids will be a list
        if isinstance(doc_ids, list):
            return {
                "message": f"NFL team rankings populated successfully ({len(doc_ids)} documents: offense, defense, total)",
                "status": "completed",
                "document_ids": doc_ids,
                "document_count": len(doc_ids),
                "ranking_types": request.ranking_types or ["offense", "defense", "total"]
            }
        else:
            return {
                "message": "NFL team rankings populated successfully",
                "status": "completed",
                "document_id": doc_ids,
                "season": season,
                "season_type": request.season_type
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== Statistics Endpoints ====================

@router.get("/stats")
async def get_population_stats():
    """Get statistics about populated data"""
    try:
        stats = await populator.get_population_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
