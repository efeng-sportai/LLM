#!/usr/bin/env python3
"""
Populate MongoDB with Sports Data from Multiple Sources
This script demonstrates how to automatically scrape and save sports data from:
- Sleeper API (player stats, standings, injuries)
- Pro Football Reference (advanced statistics)
- FantasyPros (expert rankings and projections)
- ESPN API (schedule, team data, news)
"""

import asyncio
import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.data_populator import DataPopulator
from app.database import connect_to_mongo, close_mongo_connection
from app.utils.season_utils import get_smart_season_defaults, SeasonDetector

# Smart season detection
season_info = get_smart_season_defaults()
CURRENT_YEAR = season_info["season"]

async def populate_core_data():
    """Populate core NFL data from mixed sources"""
    print("\n" + "=" * 60)
    print("Populating Core NFL Data (Mixed Sources)")
    print("=" * 60)
    
    populator = DataPopulator()
    
    # Example 1: Populate NFL schedule (FIRST)
    print("\n1. Populating NFL Schedule (ESPN API)...")
    try:
        doc_id = await populator.populate_nfl_schedule(
            season=CURRENT_YEAR,
            season_type="regular",
            week=None  # All weeks
        )
        print(f"   [OK] NFL schedule saved (ID: {doc_id})")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Example 2: Populate NFL team rankings (offense, defense only)
    print("\n2. Populating NFL Team Rankings (Sleeper API - Offense, Defense)...")
    try:
        # Get the rankings first to show counts
        ranking_types = ["offense", "defense"]
        rankings_dict = populator.scraper.get_nfl_team_rankings(CURRENT_YEAR, "regular", ranking_types)
        offense_count = len(rankings_dict.get("offense", [])) if rankings_dict.get("offense") else 0
        defense_count = len(rankings_dict.get("defense", [])) if rankings_dict.get("defense") else 0
        
        doc_ids = await populator.populate_nfl_team_rankings(
            season=CURRENT_YEAR,
            season_type="regular",
            ranking_types=["offense", "defense"]
        )
        if isinstance(doc_ids, list):
            print(f"   [OK] Saved Offense rankings with ID: {doc_ids[0]} ({offense_count} teams)")
            print(f"   [OK] Saved Defense rankings with ID: {doc_ids[1]} ({defense_count} teams)")
            print(f"   [OK] Team rankings saved ({len(doc_ids)} documents):")
            for i, doc_id in enumerate(doc_ids):
                ranking_type = ["offense", "defense"][i] if i < 2 else f"document_{i+1}"
                print(f"      - Document {i+1}: {doc_id}")
        else:
            print(f"   [OK] Team rankings saved (ID: {doc_ids})")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Example 3: Populate top NFL players from Sleeper by stats (Top 100)
    print("\n3. Populating Top NFL Players (Sleeper API - Top 100 by stats)...")
    print("   This will create 19 documents:")
    print("      - Top 100 Players: Standard, Half PPR, Full PPR (3 docs)")
    print("      - Trending Players: 1 doc")
    print("      - Position Rankings (QB, RB, WR, TE, K): Each with Standard, Half PPR, Full PPR (15 docs)")
    print(f"   Note: Using {CURRENT_YEAR} season")
    print("   Note: DEF/team defenses not included (Sleeper doesn't provide reliable defense data)")
    try:
        doc_ids = await populator.populate_sleeper_players("nfl", top_n=100, use_stats=True, season=CURRENT_YEAR, season_type="regular")
        if isinstance(doc_ids, list):
            print(f"   [OK] Top 100 NFL players saved:")
            print(f"      - Standard Scoring: {doc_ids[0]}")
            print(f"      - Half PPR Scoring: {doc_ids[1]}")
            print(f"      - Full PPR Scoring: {doc_ids[2]}")
            print(f"      - Trending Players: {doc_ids[3]}")
            print(f"      - Position Rankings (QB, RB, WR, TE, K): {doc_ids[4]} to {doc_ids[-1]}")
            print(f"      Total documents created: {len(doc_ids)} (4 general + 15 position-specific)")
        else:
            print(f"   [OK] Top 100 NFL players saved (ID: {doc_ids})")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Example 4: Populate injured/out players
    print("\n4. Populating Injured/Out NFL Players (Sleeper API)...")
    try:
        # Get the injured players first to show count
        injured_players = populator.scraper.get_sleeper_injured_players("nfl")
        injured_count = len(injured_players) if injured_players else 0
        
        doc_id = await populator.populate_sleeper_injured_players("nfl")
        print(f"   [OK] Injured/out players saved (ID: {doc_id}) - {injured_count} players processed")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

async def populate_granular_data():
    """Example: Populate granular fantasy data from web scraping"""
    print("\n" + "=" * 60)
    print("Populating Advanced Fantasy Data (Multiple Sources)")
    print("=" * 60)
    
    populator = DataPopulator()
    
    # Example 1: Populate advanced team stats
    print("\n1. Populating Advanced Team Statistics (Pro Football Reference)...")
    try:
        # Get the stats first to show count
        team_stats = populator.scraper.get_team_advanced_stats(season=CURRENT_YEAR, source="pfr")
        team_count = len(team_stats) if team_stats else 0
        
        doc_id = await populator.populate_advanced_team_stats(season=CURRENT_YEAR, source="pfr")
        print(f"   [OK] Advanced team stats saved (ID: {doc_id}) - {team_count} teams processed")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Example 2: Populate player season stats for key positions
    print("\n2. Populating Player Season Statistics (Pro Football Reference)...")
    positions = ["QB", "RB", "WR", "TE"]
    for position in positions:
        try:
            # Get the stats first to show count
            player_stats = populator.scraper.get_player_season_stats(position=position, season=CURRENT_YEAR, source="pfr")
            player_count = len(player_stats) if player_stats else 0
            
            doc_id = await populator.populate_player_season_stats(position=position, season=CURRENT_YEAR, source="pfr")
            print(f"   [OK] {position} season stats saved (ID: {doc_id}) - {player_count} players processed")
        except Exception as e:
            print(f"   [ERROR] {position} season stats failed: {e}")
    
    # Example 3: Populate injury report using Sleeper data
    print("\n3. Populating Injury Report (Sleeper API)...")
    try:
        doc_id = await populator.populate_comprehensive_injury_report(source="sleeper")
        print(f"   [OK] Sleeper injury report saved (ID: {doc_id})")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Example 4: Populate NFL player news from RSS feeds (most recent articles only) - LAST
    print("\n4. Populating NFL Player News (ESPN RSS - past week)...")
    try:
        doc_ids = await populator.populate_nfl_player_news(source="espn", limit=50, match_to_players=True, max_age_hours=168)
        if isinstance(doc_ids, list):
            print(f"   [OK] Player news saved: {len(doc_ids)-1} players with news + 1 general news document")
            print(f"   [OK] Total documents: {len(doc_ids)}")
        else:
            print(f"   [OK] News saved (ID: {doc_ids})")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

async def get_statistics():
    """Get population statistics"""
    print("\n" + "=" * 60)
    print("Population Statistics")
    print("=" * 60)
    
    populator = DataPopulator()
    
    try:
        stats = await populator.get_population_stats()
        print(f"\nTotal Training Data: {stats['total_training_data']} entries")
        print(f"Core NFL Data (Sleeper): {stats['sleeper_training_data']} entries")
        print(f"Advanced Data (Web Scrapers): {stats['total_training_data'] - stats['sleeper_training_data']} entries")
        print(f"\nBreakdown by source:")
        for source, count in stats.get('by_source', {}).items():
            source_name = {
                'sleeper_scraper': 'Sleeper API',
                'web_scraper': 'Web Scrapers (PFR, FantasyPros, ESPN)'
            }.get(source, source)
            print(f"  {source_name}: {count}")
        print(f"\nBreakdown by category:")
        for category, count in stats.get('by_category', {}).items():
            print(f"  {category}: {count}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main population script"""
    print("=" * 60)
    print("NFL Data Population Script")
    print("=" * 60)
    print("\nThis script will populate MongoDB with NFL data from multiple sources:")
    print("• Sleeper API: Player stats, standings, injuries, trending players")
    print("• Pro Football Reference: Advanced team/player statistics")  
    print("• ESPN API: Schedule, team data, news")
    print("\nMake sure MongoDB is running and configured correctly.\n")
    
    # Show smart season detection info
    detector = SeasonDetector()
    current_season_info = detector.get_season_info()
    
    print("Smart Season Detection:")
    print(f"   Current Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"   NFL Season Phase: {current_season_info['phase'].replace('_', ' ').title()}")
    print(f"   Current NFL Season: {current_season_info['season_year']}")
    print(f"   Using Season: {CURRENT_YEAR} ({season_info['recommendation']['reason']})")
    print(f"   Available Seasons: {', '.join(detector.get_available_seasons())}")
    print()
    
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        print("[OK] Connected to MongoDB\n")
        
        # Populate core NFL data (mixed sources)
        await populate_core_data()
        
        # Populate granular fantasy data
        await populate_granular_data()
        
        # Get statistics
        await get_statistics()
        
        print("\n" + "=" * 60)
        print("Population Complete!")
        print("=" * 60)
        print("\nYou can also use the API endpoints:")
        print("  - POST /populate/sleeper/players")
        print("  - GET /populate/stats")
        print("\nSee API docs at: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_mongo_connection()
        print("\n[OK] MongoDB connection closed")

if __name__ == "__main__":
    asyncio.run(main())

