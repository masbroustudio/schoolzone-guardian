import os
import sys
from google.cloud import bigquery
from google.api_core.exceptions import Conflict

# Set Target Project ID
PROJECT_ID = "juaravibe01"
DATASET_ID = "safety_dataset"

def run_db_setup():
    print(f"Initializing Google Cloud BigQuery client for project '{PROJECT_ID}'...")
    
    # Initialize the BigQuery client
    try:
        client = bigquery.Client(project=PROJECT_ID)
    except Exception as e:
        print(f"Error initializing client: {e}")
        print("Please verify you have run: gcloud auth application-default login")
        sys.exit(1)
        
    dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
    
    # Create dataset if not exists
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "US"
    dataset.description = "Dataset containing school zone geographic geometries and historical traffic hazards"
    
    try:
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"Dataset '{DATASET_ID}' created successfully.")
    except Conflict:
        print(f"Dataset '{DATASET_ID}' already exists.")
    except Exception as e:
        print(f"Failed to create dataset: {e}")
        sys.exit(1)

    # 1. Create schools table
    schools_table_id = f"{PROJECT_ID}.{DATASET_ID}.schools"
    schools_schema = [
        bigquery.SchemaField("school_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("school_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("address", "STRING"),
        bigquery.SchemaField("latitude", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("longitude", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("geometry", "GEOGRAPHY", mode="REQUIRED"),
        bigquery.SchemaField("zone_radius_meters", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
    ]
    
    schools_table = bigquery.Table(schools_table_id, schema=schools_schema)
    try:
        client.create_table(schools_table)
        print(f"Table '{schools_table_id}' created successfully.")
    except Conflict:
        print(f"Table '{schools_table_id}' already exists.")
        
    # 2. Create crashes_raw table
    crashes_table_id = f"{PROJECT_ID}.{DATASET_ID}.crashes_raw"
    crashes_schema = [
        bigquery.SchemaField("unique_key", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("crash_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("crash_time", "TIME", mode="REQUIRED"),
        bigquery.SchemaField("latitude", "FLOAT64"),
        bigquery.SchemaField("longitude", "FLOAT64"),
        bigquery.SchemaField("geometry", "GEOGRAPHY"),
        bigquery.SchemaField("number_of_persons_injured", "INTEGER"),
        bigquery.SchemaField("number_of_pedestrians_injured", "INTEGER"),
        bigquery.SchemaField("number_of_cyclist_injured", "INTEGER"),
        bigquery.SchemaField("contributing_factor_vehicle_1", "STRING"),
        bigquery.SchemaField("vehicle_type_code1", "STRING"),
    ]
    
    crashes_table = bigquery.Table(crashes_table_id, schema=crashes_schema)
    try:
        client.create_table(crashes_table)
        print(f"Table '{crashes_table_id}' created successfully.")
    except Conflict:
        print(f"Table '{crashes_table_id}' already exists.")

    # 3. Create weather_forecasts table
    weather_table_id = f"{PROJECT_ID}.{DATASET_ID}.weather_forecasts"
    weather_schema = [
        bigquery.SchemaField("school_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("forecast_time", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("precipitation_probability", "FLOAT64"),
        bigquery.SchemaField("weather_code", "INTEGER"),
        bigquery.SchemaField("temperature_2m", "FLOAT64"),
        bigquery.SchemaField("wind_speed_10m", "FLOAT64"),
        bigquery.SchemaField("last_updated", "TIMESTAMP"),
    ]
    
    weather_table = bigquery.Table(weather_table_id, schema=weather_schema)
    try:
        client.create_table(weather_table)
        print(f"Table '{weather_table_id}' created successfully.")
    except Conflict:
        print(f"Table '{weather_table_id}' already exists.")

    # 4. Create risk_forecast table (pre-computed flat target)
    risk_table_id = f"{PROJECT_ID}.{DATASET_ID}.risk_forecast"
    risk_schema = [
        bigquery.SchemaField("school_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("school_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("time_window", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("day_of_week", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("historical_crash_count", "INTEGER"),
        bigquery.SchemaField("baseline_risk_score", "FLOAT64"),
        bigquery.SchemaField("weather_multiplier", "FLOAT64"),
        bigquery.SchemaField("live_risk_score", "FLOAT64"),
        bigquery.SchemaField("risk_level", "STRING"),
        bigquery.SchemaField("primary_factors", "STRING", mode="REPEATED"),
        bigquery.SchemaField("last_updated", "TIMESTAMP"),
    ]
    
    risk_table = bigquery.Table(risk_table_id, schema=risk_schema)
    try:
        client.create_table(risk_table)
        print(f"Table '{risk_table_id}' created successfully.")
    except Conflict:
        print(f"Table '{risk_table_id}' already exists.")
        
    print("\n--- GCP BigQuery Provisioning Completed ---")
    print(f"Dataset location: {PROJECT_ID}.{DATASET_ID}")
    print("Next step: Populate NYC school coordinates and deploy Cloud Scheduler aggregation triggers.")

if __name__ == "__main__":
    run_db_setup()
