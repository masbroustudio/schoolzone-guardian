import subprocess
import json
import sys

PROJECT_ID = "juaravibe01"
DATASET_ID = "safety_dataset"

# Define the spatial join query
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
  MIN(95.0, COUNT(c.unique_key) * 4.5) AS baseline_risk_score,
  1.0 AS weather_multiplier,
  MIN(95.0, COUNT(c.unique_key) * 4.5) AS live_risk_score,
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

def create_scheduled_query():
    print("Creating BigQuery Scheduled Query configuration...")
    
    # Parameters must be passed as JSON string
    params = {
        "query": SQL_QUERY
    }
    
    # Run the bq CLI tool using python subprocess to prevent shell escaping issues
    command = [
        r"C:\Users\fr13t\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\bq.cmd", "mk",
        "--transfer_config",
        f"--project_id={PROJECT_ID}",
        "--data_source=scheduled_query",
        f"--target_dataset={DATASET_ID}",
        "--display_name=School Zone Spatial Join Routine",
        "--schedule=every 24 hours",  # Free tier default schedule rate
        f"--params={json.dumps(params)}"
    ]
    
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True, shell=True)
        print("Scheduled Query created successfully!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error creating scheduled query:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    create_scheduled_query()
