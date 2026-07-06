import functions_framework
import urllib.request
import json
from google.cloud import bigquery

@functions_framework.http
def ingest_weather_forecast(request):
    """
    HTTP Google Cloud Function that fetches current precipitation probabilities
    for registered schools and writes them directly into Google Cloud BigQuery.
    """
    
    # List of school zone coordinates to query
    schools = [
        {"id": "school_1", "lat": 40.7782, "lon": -73.9856},
        {"id": "school_2", "lat": 40.7178, "lon": -74.0139},
        {"id": "school_3", "lat": 40.6888, "lon": -73.9765},
        {"id": "school_4", "lat": 40.8776, "lon": -73.8903}
    ]
    
    # Initialize BigQuery client
    bq_client = bigquery.Client()
    table_id = "juaravibe01.safety_dataset.weather_forecasts"
    
    rows_to_insert = []
    
    for school in schools:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={school['lat']}&longitude={school['lon']}&hourly=precipitation_probability,weather_code,temperature_2m,wind_speed_10m&forecast_days=1"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                # Fetch first hourly index (representing next hour forecast)
                hourly = data.get('hourly', {})
                times = hourly.get('time', [])
                precips = hourly.get('precipitation_probability', [])
                codes = hourly.get('weather_code', [])
                temps = hourly.get('temperature_2m', [])
                winds = hourly.get('wind_speed_10m', [])
                
                if times and precips:
                    rows_to_insert.append({
                        "school_id": school["id"],
                        "forecast_time": times[0],  # ISO8601 String format compatible with BigQuery
                        "precipitation_probability": float(precips[0]) / 100.0,
                        "weather_code": int(codes[0]) if codes else 0,
                        "temperature_2m": float(temps[0]) if temps else 15.0,
                        "wind_speed_10m": float(winds[0]) if winds else 5.0
                    })
        except Exception as e:
            print(f"Error fetching live weather API for {school['id']}: {e}")

    if rows_to_insert:
        # Stream rows directly into BigQuery table
        errors = bq_client.insert_rows_json(table_id, rows_to_insert)
        if errors == []:
            print(f"Successfully inserted {len(rows_to_insert)} weather records into BigQuery.")
            return f"Successfully ingested {len(rows_to_insert)} records.", 200
        else:
            print(f"Failed to stream rows to BigQuery: {errors}")
            return f"BigQuery streaming errors: {errors}", 500
            
    return "No weather data collected.", 200
