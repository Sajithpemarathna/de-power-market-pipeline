# German power market pipeline

A data pipeline for German electricity market data from SMARD (Bundesnetzagentur). The goal is to load it into BigQuery every day, model it with dbt, and answer three questions on a dashboard:

1. When and why do day-ahead prices drop below zero?
2. What is solar power really worth on the market (capture price)?
3. How accurate are the wind and solar forecasts?

**Status:** work in progress. The SMARD download script works. BigQuery, dbt and the daily schedule come next.

## Run it locally

    python -m venv .venv
    source .venv/bin/activate        # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    pytest
    python -m ingestion.download_smard --start 2026-09-14 --end 2026-09-21

The script writes one CSV per series to `data/smard/`. That folder is not committed; the script recreates it.

## Data

Bundesnetzagentur | SMARD.de, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).