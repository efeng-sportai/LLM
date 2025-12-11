"""
Sports Scraper API Router
Provides endpoints for scraping Sleeper data
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from app.services.sports_scraper import SportsScraper
# get_documents_collection removed - only training_data collection is used
from bson import ObjectId

router = APIRouter()
scraper = SportsScraper()

# ==================== Request/Response Models ====================

class SleeperUserRequest(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None

class SleeperLeaguesRequest(BaseModel):
    user_id: str
    season: Optional[str] = None

class SleeperLeagueRequest(BaseModel):
    league_id: str

class SleeperMatchupsRequest(BaseModel):
    league_id: str
    week: Optional[int] = None

class BatchScrapeRequest(BaseModel):
    urls: List[HttpUrl]
    source: str = "sleeper"
    save_to_db: bool = False

# ==================== Sleeper Endpoints ====================

@router.get("/sleeper/user")
async def get_sleeper_user(
    username: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    save_to_db: bool = Query(False)
):
    """Get Sleeper user information"""
    try:
        if not username and not user_id:
            raise HTTPException(status_code=400, detail="Must provide either username or user_id")
        
        data = scraper.get_sleeper_user(username, user_id)
        
        # save_to_db functionality removed - only training_data collection is used
        if save_to_db:
            return {"data": data, "saved": False, "message": "save_to_db not available - only training_data collection is used"}
        
        return {"data": data, "saved": False}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sleeper/leagues")
async def get_sleeper_leagues(
    user_id: str = Query(...),
    season: Optional[str] = Query(None),
    save_to_db: bool = Query(False)
):
    """Get Sleeper leagues for a user"""
    try:
        data = scraper.get_sleeper_leagues(user_id, season)
        
        # save_to_db functionality removed - only training_data collection is used
        if save_to_db:
            return {"data": data, "saved": False, "message": "save_to_db not available - only training_data collection is used"}
        
        return {"data": data, "saved": False}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sleeper/league/{league_id}")
async def get_sleeper_league(league_id: str, save_to_db: bool = Query(False)):
    """Get Sleeper league information"""
    try:
        data = scraper.get_sleeper_league(league_id)
        
        # save_to_db functionality removed - only training_data collection is used
        if save_to_db:
            return {"data": data, "saved": False, "message": "save_to_db not available - only training_data collection is used"}
        
        return {"data": data, "saved": False}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sleeper/league/{league_id}/rosters")
async def get_sleeper_rosters(league_id: str, save_to_db: bool = Query(False)):
    """Get Sleeper league rosters"""
    try:
        data = scraper.get_sleeper_rosters(league_id)
        
        # save_to_db functionality removed - only training_data collection is used
        if save_to_db:
            return {"data": data, "saved": False, "message": "save_to_db not available - only training_data collection is used"}
        
        return {"data": data, "saved": False}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sleeper/league/{league_id}/matchups")
async def get_sleeper_matchups(
    league_id: str,
    week: Optional[int] = Query(None),
    save_to_db: bool = Query(False)
):
    """Get Sleeper league matchups"""
    try:
        data = scraper.get_sleeper_matchups(league_id, week)
        
        # save_to_db functionality removed - only training_data collection is used
        if save_to_db:
            return {"data": data, "saved": False, "message": "save_to_db not available - only training_data collection is used"}
        
        return {"data": data, "saved": False}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sleeper/league/{league_id}/transactions")
async def get_sleeper_transactions(
    league_id: str,
    round_num: Optional[int] = Query(None),
    save_to_db: bool = Query(False)
):
    """Get Sleeper league transactions"""
    try:
        data = scraper.get_sleeper_transactions(league_id, round_num)
        
        # save_to_db functionality removed - only training_data collection is used
        if save_to_db:
            return {"data": data, "saved": False, "message": "save_to_db not available - only training_data collection is used"}
        
        return {"data": data, "saved": False}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sleeper/players/{sport}")
async def get_sleeper_players(sport: str = "nfl", save_to_db: bool = Query(False)):
    """Get all players for a sport from Sleeper"""
    try:
        data = scraper.get_sleeper_players(sport)
        
        # save_to_db functionality removed - only training_data collection is used
        if save_to_db:
            return {
                "data": data,
                "player_count": len(data) if isinstance(data, dict) else 0,
                "saved": False,
                "message": "save_to_db not available - only training_data collection is used"
            }
        
        return {
            "data": data,
            "player_count": len(data) if isinstance(data, dict) else 0,
            "saved": False
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sleeper/draft/{draft_id}")
async def get_sleeper_draft(draft_id: str, save_to_db: bool = Query(False)):
    """Get Sleeper draft information"""
    try:
        data = scraper.get_sleeper_draft(draft_id)
        
        # save_to_db functionality removed - only training_data collection is used
        if save_to_db:
            return {"data": data, "saved": False, "message": "save_to_db not available - only training_data collection is used"}
        
        return {"data": data, "saved": False}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== Utility Endpoints ====================

@router.post("/batch-scrape")
async def batch_scrape(request: BatchScrapeRequest):
    """Batch scrape multiple URLs"""
    try:
        results = scraper.batch_fetch([str(url) for url in request.urls], request.source or "sleeper")
        
        # save_to_db functionality removed - only training_data collection is used
        if request.save_to_db:
            return {
                "results": results,
                "total": len(results),
                "successful": len([r for r in results if "error" not in r]),
                "saved": False,
                "message": "save_to_db not available - only training_data collection is used"
            }
        
        return {
            "results": results,
            "total": len(results),
            "successful": len([r for r in results if "error" not in r]),
            "saved": False
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

