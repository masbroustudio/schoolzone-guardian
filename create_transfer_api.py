import sys
from google.cloud import bigquery_datatransfer
from google.protobuf import struct_pb2

PROJECT_ID = "juaravibe01"
DATASET_ID = "safety_dataset"
LOCATION = "us" # default location

# Spatial join query to calculate 15-minute risk scores
SQL_QUERY = """
INSERT INTO `juaravibe01.safety_dataset.risk_forecast` (
  school_id, school_name, time_window, day_of_week, 
  historical_crash_count, baseline_risk_score, weather_multiplier, 
  live_risk_score, risk_level, primary_factors, last_updated
)
SELECT 
  s.school_id,
  s.school_name,
  FORMAT_TIME('%H:%M', TIME(
    EXTRACT(HOUR FROM c.crash_time), 
    DIV(EXTRACT(MINUTE FROM c.crash_time), 15) * 15, 
    0
  )) AS time_window,
  FORMAT_DATE('%A', c.crash_date) AS day_of_week,
  COUNT(c.unique_key) AS historical_crash_count,
  LEAST(95.0, COUNT(c.unique_key) * 4.5) AS baseline_risk_score,
  1.0 AS weather_multiplier,
  LEAST(95.0, COUNT(c.unique_key) * 4.5) AS live_risk_score,
  CASE 
    WHEN COUNT(c.unique_key) * 4.5 < 40 THEN 'LOW'
    WHEN COUNT(c.unique_key) * 4.5 < 70 THEN 'MEDIUM'
    ELSE 'HIGH'
  END AS risk_level,
  ARRAY['Peak congestion area', 'Historical vehicle collisions within 300m'] AS primary_factors,
  CURRENT_TIMESTAMP() AS last_updated
FROM 
  `juaravibe01.safety_dataset.schools` s
JOIN 
  `juaravibe01.safety_dataset.crashes_raw` c
ON 
  ST_DWithin(s.geometry, c.geometry, 300)
GROUP BY 
  s.school_id, s.school_name, time_window, day_of_week;
"""

from google.api_core.client_options import ClientOptions

def deploy_scheduled_query():
    print("Initializing BigQuery Data Transfer Service Client...")
    
    try:
        client_options = ClientOptions(quota_project_id=PROJECT_ID)
        client = bigquery_datatransfer.DataTransferServiceClient(client_options=client_options)
        
        # Prepare parameters
        params = {
            "query": SQL_QUERY
        }
        
        # Convert dictionary to protobuf Struct
        params_struct = struct_pb2.Struct()
        params_struct.update(params)
        
        # Create transfer configuration object
        transfer_config = bigquery_datatransfer.TransferConfig(
            display_name="School Zone Spatial Join Routine",
            data_source_id="scheduled_query",
            params=params_struct,
            schedule="every 24 hours",  # Trigger every 24 hours
            disabled=False
        )
        
        parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
        
        print("Sending creation request to GCP...")
        response = client.create_transfer_config(
            parent=parent,
            transfer_config=transfer_config
        )
        
        print(f"\n✅ Scheduled query successfully created!")
        print(f"Configuration Resource Name: {response.name}")
        print(f"State: {response.state}")
        
    except Exception as e:
        print(f"\n❌ Error deploying scheduled query: {e}", file=sys.stderr)
        print("Verify that google-cloud-bigquery-datatransfer is installed and ADC is logged in.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    deploy_scheduled_query()
