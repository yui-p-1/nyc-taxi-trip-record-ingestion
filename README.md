# NYC Taxi Data Ingestion Pipeline

## Overview
This project is an automated data ingestion pipeline for NYC Taxi Trip Record Data.

It is part of a modular data platform and provides raw and staged datasets for downstream analytics and data warehouse processing.

## Architecture

Data ingestion flow:

Cloud Scheduler  
→ Cloud Run (Python ETL)  
→ Google Cloud Storage (Raw Data Lake)  
→ BigQuery External Tables (Staging Layer)  
→ Dataform Trigger (Transformation Layer)  
→ Tableau Dashboard (Consumption Layer)

## Technologies
- Google Cloud Scheduler
- Cloud Run (Python)
- Google Cloud Storage
- BigQuery
- Dataform
- Tableau

## Data Source
NYC Taxi & Limousine Commission Trip Record Data  
https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page  

## Output
This pipeline outputs:
- Raw data stored in GCS
- Staging data in BigQuery external tables
- Datasets used by the downstream Data Warehouse project

## Relationship to DWH
This pipeline is the upstream data ingestion layer of the NYC Taxi Data Warehouse project.

It provides curated datasets that are transformed and modeled in the DWH layer for analytics and BI use.
