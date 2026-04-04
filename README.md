# Fantasy Football Application

## Overview
End-to-end data engineering and analytics platform that processes NFL weekly stats and generates tables/charts for easy consumption and analysis 

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
