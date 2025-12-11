# Sports Data Population System

This system automatically scrapes data from Sleeper and populates your MongoDB database with NFL training data.

## Architecture

### Components

1. **SportsScraper** (`app/services/sports_scraper.py`)
   - Low-level scraper that fetches data from Sleeper API
   - Handles both API calls and web scraping fallbacks
   - Sources data from ESPN API for schedule and team statistics

2. **DataPopulator** (`app/services/data_populator.py`)
   - High-level service that orchestrates scraping and saves to MongoDB
   - Automatically converts scraped data to training data format
   - All data is saved to the `training_data` collection

3. **API Endpoints** (`app/routers/populate.py`)
   - REST API for triggering data population
   - Automatically saves all data to MongoDB as training data

## Documents Populated

When you run the population script or API endpoints, the following documents are created in the `training_data` collection:

### 1. NFL Schedule (1 document)
- **Category**: `schedule`
- **Content**: Complete NFL schedule for the season with all weeks, matchups, teams, dates, and scores
- **Source**: ESPN API

### 2. Team Rankings (3 documents)
- **Category**: `team_rankings`
- **Offense Rankings**: Teams ranked by total offensive yards (aggregated from player stats - passing + rushing + receiving)
- **Defense Rankings**: Teams ranked by defensive performance (aggregated from defensive player stats - sacks + interceptions)
- **Total Rankings**: Teams ranked by win percentage (from standings data)
- **Source**: Sleeper API (player stats) + Standings (web scraping)

### 3. Player Rankings (22 documents)
- **Category**: `player_list`
- **General Rankings** (4 documents):
  - Top 100 Players - Standard Scoring (sorted by Standard PPR fantasy points)
  - Top 100 Players - Half PPR Scoring (sorted by Half PPR fantasy points)
  - Top 100 Players - Full PPR Scoring (sorted by Full PPR fantasy points)
  - Trending Players (players being added/dropped on Sleeper)
- **Position-Specific Rankings** (18 documents):
  - Top QBs, RBs, WRs, TEs, DEF, K for each scoring type (Standard, Half PPR, Full PPR)
  - Each position has 3 documents (one per PPR type)
- **Source**: Sleeper API

### 4. NFL Standings (1 document)
- **Category**: `standings`
- **Content**: Current NFL standings with team records (wins, losses, ties) sorted by win percentage
- **Source**: Sleeper.com web scraping

### 5. Injured Players (1 document)
- **Category**: `player_injuries`
- **Content**: List of all injured/out players with their injury status, team, position, and status details
- **Source**: Sleeper API

### 6. Player News (31+ documents)
- **Category**: `player_news`
- **Content**: NFL news articles from RSS feeds (ESPN and NFL.com) matched to individual players
- Creates one document per player with news + one general news document
- Only includes articles from the past week (7 days)
- **Source**: ESPN/NFL.com RSS feeds

### Total Documents Created
Running the full population script creates approximately **59 training data documents**:
- 1 Schedule
- 3 Team Rankings
- 22 Player Rankings
- 1 Standings
- 1 Injured Players
- 31+ Player News

## Quick Start

### Via Script (Recommended)

```bash
# Run the population script
cd backend
python3 populate_sports_data.py
```

This will populate all NFL data documents in the correct order:
1. Schedule (first)
2. Team Rankings (offense, defense, total)
3. Player Rankings (all PPR types + positions)
4. Standings
5. Injured Players
6. Player News

### Via API

```bash
# Start your FastAPI server
python3 main.py

# Visit API docs
http://localhost:8000/docs
```

## API Endpoints

### Sleeper Endpoints

- **POST** `/populate/sleeper/schedule` - Populate NFL schedule
- **POST** `/populate/sleeper/team-rankings` - Populate team rankings (offense, defense, total)
- **POST** `/populate/sleeper/players` - Populate player rankings (all PPR types + positions)
- **POST** `/populate/sleeper/standings` - Populate NFL standings
- **POST** `/populate/sleeper/injured-players` - Populate injured/out players
- **POST** `/populate/sleeper/player-news` - Populate player news from RSS feeds

### Statistics

- **GET** `/populate/stats` - Get population statistics

## Examples

### Example 1: Populate NFL Schedule

```bash
curl -X POST "http://localhost:8000/populate/sleeper/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "season": "2025",
    "season_type": "regular",
    "week": null
  }'
```

### Example 2: Populate Team Rankings

```bash
curl -X POST "http://localhost:8000/populate/sleeper/team-rankings" \
  -H "Content-Type: application/json" \
  -d '{
    "season": "2025",
    "season_type": "regular",
    "ranking_types": ["offense", "defense", "total"]
  }'
```

### Example 3: Populate Player Rankings

```bash
curl -X POST "http://localhost:8000/populate/sleeper/players" \
  -H "Content-Type: application/json" \
  -d '{
    "sport": "nfl",
    "top_n": 100,
    "use_stats": true,
    "season": "2025",
    "season_type": "regular"
  }'
```

## Data Structure

All scraped data is saved to MongoDB in the `training_data` collection with the following structure:

- `prompt` - Question/prompt about the data
- `response` - Human-readable formatted response
- `context` - Context description
- `category` - Document category (schedule, team_rankings, player_list, standings, player_injuries, player_news)
- `source_type` - Always `"sleeper_scraper"`
- `metadata` - Additional metadata including:
  - `sport` - "nfl"
  - `season` - Season year
  - `season_type` - "regular", "pre", or "post"
  - `ranking_type` - For team rankings: "offense", "defense", or "total"
  - `ppr_type` - For player rankings: "std", "half_ppr", or "ppr"
  - `position` - For position-specific rankings: "QB", "RB", "WR", "TE", "DEF", "K"
  - `raw_players_data` or `raw_rankings_data` - Raw data for reference
- `created_at` - Timestamp when document was created
- `updated_at` - Timestamp when document was last updated
- `is_active` - Whether the document is active

## Integration with Training Data System

The populated data integrates seamlessly with your training data system:

- All data is stored in the `training_data` collection (the only collection used)
- Can be queried via `/training-data` endpoints
- Used for AI model training and fine-tuning
- Searchable via text search on prompt and response fields

## Key Features

- **Automatic Saving** - All data is automatically saved to MongoDB as training data
- **API Integration** - Uses official Sleeper API and ESPN API (more reliable than scraping)
- **Fallback Scraping** - Falls back to web scraping when APIs aren't available
- **Multiple Scoring Formats** - Supports Standard, Half PPR, and Full PPR fantasy scoring
- **Position-Specific Rankings** - Separate documents for QB, RB, WR, TE, DEF, K
- **Player News Matching** - Automatically matches news articles to players
- **Error Handling** - Graceful error handling with detailed error messages
- **Statistics** - Track what's been populated via `/populate/stats` endpoint

## Data Sources

- **Sleeper API** (`https://api.sleeper.app/v1`):
  - Player information and statistics
  - Trending players
  - Injured players
  - League standings (via web scraping)

- **ESPN API** (`https://site.api.espn.com/apis/site/v2/sports/football/nfl`):
  - NFL schedule/matchups
  - Scoreboard data

- **RSS Feeds**:
  - ESPN NFL news feed
  - NFL.com news feed

## Notes

- Only NFL data is currently supported
- All data is saved asynchronously for better performance
- The system is designed to be run on-demand or scheduled via cron/APScheduler if needed
- Player rankings are sorted by fantasy points (Standard, Half PPR, or Full PPR depending on the document)
- Team offense rankings aggregate all offensive player stats (QB, RB, WR, TE, FB) by team
- Team defense rankings aggregate defensive player stats (DEF, LB, CB, S, DT, DE, NT) by team
- Player news only includes articles from the past 7 days (168 hours) by default
