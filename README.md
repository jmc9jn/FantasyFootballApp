# Fantasy Football Application

## Overview
This application provides an interactive analytics platform for evaluating NFL player performance using weekly and season-level statistics. Users can explore rankings, trends, and individual player performance through a structured multi-tab interface.
---

## Features

### Weekly Rankings
The Weekly Rankings tab allows users to analyze player performance on a week-by-week basis.

- Filter by position (QB, RB, WR, TE, Defense)
- Select NFL week (1–17)
- View dynamic player rankings for selected filters
- Rankings based on computed fantasy performance metrics

---

### Season Rankings
The Season Rankings tab provides aggregated performance across the entire season.

- Filter by position group
- Toggle between:
  - Total stats (season-long production)
  - Average stats (per-game efficiency)
- Dynamically updated ranked tables

---

### Player Stats Explorer
The Player Stats tab provides detailed analysis of individual players.

- Filter by position and player
- View weekly stat breakdowns
- Interactive tables and trend charts
- Tracks performance over the full season

---
## Architecture
- Django backend for data storage and APIs
- AWS S3 for raw and processed data storage
- AWS Lambda for ETL processing
- Pandas for data transformation

## Pipeline Flow
1. Weekly stats pulled from stathead.com and uploaded to S3 (raw/)
2. Lambda triggers on upload to preprocess raw data
3. Data validated and further processed using pandas
4. Outputs written to processed/ S3 folder
5. Django ingests processed data for analytics dashboard

## Tech Stack
- Python
- Django
- AWS (S3, Lambda)
- Pandas
- PostgreSQL / SQLite

## Key Features
- Automated ETL pipeline for NFL stats
- Position-based aggregation (QB, RB, WR, TE)
- Fantasy point ranking system
- Modular data processing architecture

## How to Run Django App
```bash
pip install -r requirements.txt
python manage.py runserver
