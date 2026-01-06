"""
Season Utilities - Smart season detection for NFL data
Handles the complexity of NFL seasons spanning calendar years
"""

from datetime import datetime, date
from typing import Tuple, Optional


class SeasonDetector:
    """Smart season detection for NFL data based on current date"""
    
    @staticmethod
    def get_current_nfl_season() -> str:
        """
        Determine the current NFL season based on the date
        
        NFL Season Timeline:
        - Season starts in September (e.g., 2024 season starts Sept 2024)
        - Regular season: September - January
        - Playoffs: January - February
        - Offseason: March - August
        
        Returns:
            Season year as string (e.g., "2024")
        """
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        # NFL season logic:
        # Jan-Feb: Still in previous year's season (playoffs/Super Bowl)
        # Mar-Aug: Offseason, use previous year's completed season
        # Sep-Dec: Current year's season is active
        
        if current_month <= 2:
            # January-February: We're in playoffs of previous year's season
            return str(current_year - 1)
        elif current_month <= 8:
            # March-August: Offseason, use previous year's completed season
            return str(current_year - 1)
        else:
            # September-December: Current year's season is active
            return str(current_year)
    
    @staticmethod
    def get_season_info(target_date: Optional[datetime] = None) -> dict:
        """
        Get comprehensive season information for a given date
        
        Args:
            target_date: Date to analyze (default: current date)
            
        Returns:
            Dictionary with season info
        """
        if target_date is None:
            target_date = datetime.now()
        
        year = target_date.year
        month = target_date.month
        day = target_date.day
        
        # Determine season year
        if month <= 2:
            season_year = year - 1
            phase = "playoffs" if month == 1 or (month == 2 and day <= 14) else "offseason"
        elif month <= 8:
            season_year = year - 1
            phase = "offseason"
        else:
            season_year = year
            if month == 9:
                phase = "regular_season"
            elif month <= 12:
                phase = "regular_season"
            else:
                phase = "regular_season"
        
        # Determine season type based on date
        season_type = "regular"
        if phase == "playoffs":
            season_type = "post"
        elif month == 8:  # Preseason typically in August
            season_type = "pre"
        
        # Estimate current week (rough approximation)
        current_week = None
        if phase == "regular_season":
            # NFL regular season typically starts first week of September
            # Week 1 is usually the first Sunday after Labor Day
            if month == 9:
                current_week = min(4, max(1, day // 7))
            elif month == 10:
                current_week = min(8, 4 + (day // 7))
            elif month == 11:
                current_week = min(12, 8 + (day // 7))
            elif month == 12:
                current_week = min(18, 12 + (day // 7))
        elif phase == "playoffs":
            if month == 1:
                current_week = min(4, max(1, day // 7))  # Wild card to championship
        
        return {
            "season_year": str(season_year),
            "season_type": season_type,
            "phase": phase,
            "current_week": current_week,
            "is_active_season": phase in ["regular_season", "playoffs"],
            "is_offseason": phase == "offseason",
            "analysis_date": target_date.isoformat()
        }
    
    @staticmethod
    def get_best_data_season(prefer_completed: bool = True) -> str:
        """
        Get the best season to fetch data from
        
        Args:
            prefer_completed: If True, prefer completed seasons over active ones
            
        Returns:
            Season year as string
        """
        season_info = SeasonDetector.get_season_info()
        current_season = season_info["season_year"]
        phase = season_info["phase"]
        
        # If we're in playoffs, the regular season is complete, so we can use current season data
        if phase == "playoffs":
            return current_season
        elif prefer_completed and season_info["is_active_season"] and phase == "regular_season":
            # Only fall back to previous season if we're in active regular season
            return str(int(current_season) - 1)
        else:
            return current_season
    
    @staticmethod
    def get_available_seasons(years_back: int = 5) -> list:
        """
        Get list of available NFL seasons going back N years
        
        Args:
            years_back: Number of years to go back
            
        Returns:
            List of season years as strings, newest first
        """
        current_season = int(SeasonDetector.get_current_nfl_season())
        seasons = []
        
        for i in range(years_back + 1):
            season_year = current_season - i
            seasons.append(str(season_year))
        
        return seasons


def get_smart_season_defaults() -> dict:
    """
    Get smart defaults for season parameters based on current date
    
    Returns:
        Dictionary with recommended season parameters
    """
    detector = SeasonDetector()
    season_info = detector.get_season_info()
    
    # For most data, use the most recent completed season for reliability
    best_season = detector.get_best_data_season(prefer_completed=True)
    
    # Create more specific recommendation reason
    phase = season_info["phase"]
    current_season = season_info["season_year"]
    
    if phase == "playoffs":
        reason = f"Using {best_season} season (regular season complete, playoffs active)"
    elif phase == "offseason":
        reason = f"Using {best_season} season (most recent completed season)"
    elif phase == "regular_season":
        if best_season == current_season:
            reason = f"Using {best_season} season (current active season)"
        else:
            reason = f"Using {best_season} season (current season {current_season} still in progress)"
    else:
        reason = f"Using {best_season} season (most recent with complete data)"
    
    return {
        "season": best_season,
        "season_type": "regular",  # Most data is from regular season
        "current_season_info": season_info,
        "available_seasons": detector.get_available_seasons(),
        "recommendation": {
            "season": best_season,
            "reason": reason
        }
    }


# Convenience functions for backward compatibility
def get_current_nfl_season() -> str:
    """Get current NFL season year"""
    return SeasonDetector.get_current_nfl_season()


def get_best_data_season() -> str:
    """Get best season for data fetching"""
    return SeasonDetector.get_best_data_season()