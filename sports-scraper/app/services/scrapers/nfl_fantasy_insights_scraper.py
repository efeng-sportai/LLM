"""
NFL Fantasy Insights Scraper
Uses FantasyPros API and Yahoo Sports API to get fantasy rankings, projections, and insights
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from .base_scraper import BaseScraper
from ..apis.fantasy_pros_api import FantasyProAPI


class NFLFantasyInsightsScraper(BaseScraper):
    """Scraper for NFL fantasy insights using FantasyPros API"""
    
    def __init__(self):
        super().__init__()
        self.fantasypros_api = FantasyProAPI()
    
    def get_expert_rankings(
        self,
        position: str = "QB",
        scoring: str = "HALF",
        week: str = "draft",
        source: str = "fantasypros"
    ) -> List[Dict[str, Any]]:
        """
        Get expert consensus rankings
        
        Args:
            position: Player position (QB, RB, WR, TE, K, DEF)
            scoring: Scoring format (STD, HALF, PPR)
            week: Week number or 'draft' (default: 'draft')
            source: Data source - 'fantasypros' or 'yahoo' (default: 'fantasypros')
        """
        try:
            if source.lower() == "fantasypros":
                rankings = self.fantasypros_api.get_expert_rankings(position, scoring, week)
            else:
                raise ValueError(f"Unsupported source: {source}. Only 'fantasypros' is supported.")
            
            # Enrich with metadata
            for ranking in rankings:
                ranking.update({
                    'data_source': source,
                    'scraped_at': datetime.now().isoformat(),
                    'data_type': 'expert_rankings'
                })
            
            return rankings
        except Exception as e:
            raise Exception(f"Failed to get {position} rankings from {source}: {str(e)}")
    
    def get_projections(
        self,
        position: str = "QB",
        scoring: str = "HALF",
        week: str = "draft",
        source: str = "fantasypros"
    ) -> List[Dict[str, Any]]:
        """
        Get fantasy projections
        
        Args:
            position: Player position (QB, RB, WR, TE, K, DEF)
            scoring: Scoring format (STD, HALF, PPR)
            week: Week number or 'draft' (default: 'draft')
            source: Data source - 'fantasypros' (default: 'fantasypros')
        """
        try:
            if source.lower() == "fantasypros":
                projections = self.fantasypros_api.get_projections(position, scoring, week)
            else:
                raise ValueError(f"Unsupported source: {source}")
            
            # Enrich with metadata
            for projection in projections:
                projection.update({
                    'data_source': source,
                    'scraped_at': datetime.now().isoformat(),
                    'data_type': 'fantasy_projections'
                })
            
            return projections
        except Exception as e:
            raise Exception(f"Failed to get {position} projections from {source}: {str(e)}")
    
    def get_start_sit_recommendations(
        self,
        position: str = "QB",
        week: str = "1",
        source: str = "fantasypros"
    ) -> List[Dict[str, Any]]:
        """
        Get start/sit recommendations
        
        Args:
            position: Player position (QB, RB, WR, TE, K, DEF)
            week: Week number (default: '1')
            source: Data source - 'fantasypros' (default: 'fantasypros')
        """
        try:
            if source.lower() == "fantasypros":
                recommendations = self.fantasypros_api.get_start_sit_recommendations(position, week)
            else:
                raise ValueError(f"Unsupported source: {source}")
            
            # Enrich with metadata
            for rec in recommendations:
                rec.update({
                    'data_source': source,
                    'scraped_at': datetime.now().isoformat(),
                    'data_type': 'start_sit_recommendations'
                })
            
            return recommendations
        except Exception as e:
            raise Exception(f"Failed to get {position} start/sit recommendations from {source}: {str(e)}")
    
    def get_trade_values(
        self,
        scoring: str = "HALF",
        source: str = "fantasypros"
    ) -> List[Dict[str, Any]]:
        """
        Get current trade values
        
        Args:
            scoring: Scoring format (STD, HALF, PPR)
            source: Data source - 'fantasypros' (default: 'fantasypros')
        """
        try:
            if source.lower() == "fantasypros":
                trade_values = self.fantasypros_api.get_trade_values(scoring)
            else:
                raise ValueError(f"Unsupported source: {source}")
            
            # Enrich with metadata
            for value in trade_values:
                value.update({
                    'data_source': source,
                    'scraped_at': datetime.now().isoformat(),
                    'data_type': 'trade_values'
                })
            
            return trade_values
        except Exception as e:
            raise Exception(f"Failed to get trade values from {source}: {str(e)}")
    
    def get_waiver_wire_pickups(
        self,
        week: str = "1",
        source: str = "fantasypros"
    ) -> List[Dict[str, Any]]:
        """
        Get waiver wire pickup recommendations
        
        Args:
            week: Week number (default: '1')
            source: Data source - 'fantasypros' (default: 'fantasypros')
        """
        try:
            if source.lower() == "fantasypros":
                pickups = self.fantasypros_api.get_waiver_wire_pickups(week)
            else:
                raise ValueError(f"Unsupported source: {source}")
            
            # Enrich with metadata
            for pickup in pickups:
                pickup.update({
                    'data_source': source,
                    'scraped_at': datetime.now().isoformat(),
                    'data_type': 'waiver_wire_pickups'
                })
            
            return pickups
        except Exception as e:
            raise Exception(f"Failed to get waiver wire pickups from {source}: {str(e)}")
    
    def get_all_position_rankings(
        self,
        scoring: str = "HALF",
        week: str = "draft",
        source: str = "fantasypros"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get rankings for all major positions
        
        Args:
            scoring: Scoring format (STD, HALF, PPR)
            week: Week number or 'draft' (default: 'draft')
            source: Data source - 'fantasypros' (default: 'fantasypros')
        """
        positions = ["QB", "RB", "WR", "TE", "K", "DEF"]
        all_rankings = {}
        
        for position in positions:
            try:
                rankings = self.get_expert_rankings(position, scoring, week, source)
                all_rankings[position] = rankings
            except Exception as e:
                print(f"Warning: Failed to get {position} rankings: {str(e)}")
                all_rankings[position] = []
        
        return all_rankings
    
    def format_expert_rankings_for_training(
        self,
        rankings: List[Dict[str, Any]],
        position: str,
        scoring: str,
        week: str
    ) -> str:
        """
        Format expert rankings into training data response
        
        Args:
            rankings: List of ranking dictionaries
            position: Player position
            scoring: Scoring format
            week: Week number or 'draft'
        """
        if not rankings:
            return f"No expert rankings found for {position} ({scoring} scoring)."
        
        response_parts = []
        week_text = f"Week {week}" if week != "draft" else "Draft"
        response_parts.append(f"Expert Consensus Rankings - {position} ({scoring} scoring, {week_text}):\n")
        
        # Sort by rank
        sorted_rankings = sorted(rankings, key=lambda x: x.get('rank', 999))
        
        for ranking in sorted_rankings[:50]:  # Top 50
            rank = ranking.get('rank', 'N/A')
            player = ranking.get('player', 'Unknown')
            team = ranking.get('team', 'N/A')
            
            line = f"{rank}. {player}"
            if team and team != 'N/A':
                line += f" ({team})"
            
            # Add projected points if available
            if ranking.get('projected_points'):
                line += f" - {ranking['projected_points']} pts"
            
            response_parts.append(line)
        
        response_parts.append(f"\nTotal players ranked: {len(rankings)}")
        response_parts.append(f"Source: {rankings[0].get('data_source', 'Unknown')}")
        return "\n".join(response_parts)
    
    def format_projections_for_training(
        self,
        projections: List[Dict[str, Any]],
        position: str,
        scoring: str,
        week: str
    ) -> str:
        """
        Format projections into training data response
        
        Args:
            projections: List of projection dictionaries
            position: Player position
            scoring: Scoring format
            week: Week number or 'draft'
        """
        if not projections:
            return f"No projections found for {position} ({scoring} scoring)."
        
        response_parts = []
        week_text = f"Week {week}" if week != "draft" else "Season"
        response_parts.append(f"Fantasy Projections - {position} ({scoring} scoring, {week_text}):\n")
        
        # Sort by projected fantasy points (if available)
        sorted_projections = sorted(
            projections,
            key=lambda x: x.get('fantasy_points', x.get('projected_points', 0)),
            reverse=True
        )
        
        for i, projection in enumerate(sorted_projections[:50], 1):
            player = projection.get('player', 'Unknown')
            team = projection.get('team', 'N/A')
            
            line = f"{i}. {player}"
            if team and team != 'N/A':
                line += f" ({team})"
            
            # Add projected stats based on position
            if position == "QB":
                if projection.get('pass_yds'):
                    line += f" - {projection['pass_yds']} pass yds"
                if projection.get('pass_td'):
                    line += f", {projection['pass_td']} TD"
            elif position in ["RB", "WR", "TE"]:
                stats = []
                if projection.get('rush_yds'):
                    stats.append(f"{projection['rush_yds']} rush yds")
                if projection.get('rec_yds'):
                    stats.append(f"{projection['rec_yds']} rec yds")
                if projection.get('total_td'):
                    stats.append(f"{projection['total_td']} TD")
                if stats:
                    line += f" - {', '.join(stats)}"
            
            # Add fantasy points
            fantasy_points = projection.get('fantasy_points', projection.get('projected_points'))
            if fantasy_points:
                line += f" - {fantasy_points} pts"
            
            response_parts.append(line)
        
        response_parts.append(f"\nTotal players projected: {len(projections)}")
        response_parts.append(f"Source: {projections[0].get('data_source', 'Unknown')}")
        return "\n".join(response_parts)
    
    def format_start_sit_for_training(
        self,
        recommendations: List[Dict[str, Any]],
        position: str,
        week: str
    ) -> str:
        """
        Format start/sit recommendations into training data response
        
        Args:
            recommendations: List of recommendation dictionaries
            position: Player position
            week: Week number
        """
        if not recommendations:
            return f"No start/sit recommendations found for {position} in Week {week}."
        
        response_parts = []
        response_parts.append(f"Start/Sit Recommendations - {position} (Week {week}):\n")
        
        # Group by recommendation type
        starts = [r for r in recommendations if r.get('recommendation') == 'start']
        sits = [r for r in recommendations if r.get('recommendation') == 'sit']
        
        if starts:
            response_parts.append("\nSTART:")
            for start in starts:
                player = start.get('player', start.get('player_text', 'Unknown'))
                response_parts.append(f"  • {player}")
        
        if sits:
            response_parts.append("\nSIT:")
            for sit in sits:
                player = sit.get('player', sit.get('player_text', 'Unknown'))
                response_parts.append(f"  • {player}")
        
        response_parts.append(f"\nTotal recommendations: {len(recommendations)}")
        response_parts.append(f"Source: {recommendations[0].get('data_source', 'Unknown')}")
        return "\n".join(response_parts)