# School-Zone Guardian - Architecture & Strategy Guide

This guide details the technical specifications, database schemas, agent workflows, custom skills, and frontend layouts for the **School-Zone Guardian** platform. It supplements the `MASTERPLAN_DRAFT.md` and provides the exact execution blueprint for building a production-ready application deployed on the Google Cloud Project `juaravibe01`.

---

## 1. Hybrid Transactional-Analytical Cloud Architecture Blueprint

To secure top marks in the hackathon, the platform utilizes a **hybrid database model** separating transactional (OLTP) and analytical (OLAP) workloads using Google Cloud's premium database services.

```
                                [ Cloud Scheduler ]
                                         │ 
                                         ▼
                     [ Cloud Functions ] (Lightweight Python ETL)
                        ┌────────────────┼────────────────┐
                        ▼                ▼                ▼
                 [ Open-Meteo API ] [ Waze Alerts ] [ BQ Public Data ]
                        │                │                │
                        ▼                ▼                ▼
              [ Google Cloud BigQuery ] ◄─► [ AlloyDB for PostgreSQL ]
              - Analytical Engine (OLAP)     - Operational DB (OLTP)
              - Stores: Spatial Join Geoms   - Stores: Parent User Profiles,
              - Table: risk_forecast         - Table: volunteer_roster
                        │                                 │
                        ▼                                 ▼
             [ Cloud Run (FastAPI API) ] ◄────────────────┘
                        │
                        ├───────────────────────────────┐
                        ▼                               ▼
           [ Vertex AI Agent Builder ]        [ Looker Studio Dashboard ]
           - Model: gemini-2.5-flash          - Embedded BI Analytics
           - Automatic Function Calling (AFC) - Historical Crash Heatmaps
                        │
                        ▼
             [ Front-End Dashboard ]
             (Lingo Aesthetic - HTML/JS/CSS)
```

---

## 2. Database Schemas & Data Tables

### 2.1 BigQuery (Analytical Engine - OLAP)
BigQuery is optimized for spatialjoins on millions of historical collisions. It stores coordinates, base risks, and pre-computed risk windows.

#### `schools` (Static Facilities)
```sql
CREATE OR REPLACE TABLE `juaravibe01.safety_dataset.schools` (
    school_id STRING NOT NULL,
    school_name STRING NOT NULL,
    address STRING,
    latitude FLOAT64 NOT NULL,
    longitude FLOAT64 NOT NULL,
    geometry GEOGRAPHY NOT NULL,
    zone_radius_meters INT64 DEFAULT 300,
    created_at TIMESTAMP
);
```

#### `risk_forecast` (Pre-Computed Flat Table)
Populated via daily scheduled queries:
```sql
CREATE OR REPLACE TABLE `juaravibe01.safety_dataset.risk_forecast` (
    school_id STRING NOT NULL,
    school_name STRING NOT NULL,
    time_window STRING NOT NULL,
    day_of_week STRING NOT NULL,
    historical_crash_count INT64,
    baseline_risk_score FLOAT64,
    weather_multiplier FLOAT64,
    live_risk_score FLOAT64,
    risk_level STRING,
    primary_factors ARRAY<STRING>,
    last_updated TIMESTAMP
);
```

### 2.2 AlloyDB (Transactional Database - OLTP)
AlloyDB is Google Cloud’s high-performance, fully-managed PostgreSQL database. It stores parent accounts, active volunteer patrol rosters, and real-time crossing guard assignments.

#### `users` (Parent & Admin Accounts)
```sql
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'parent', -- 'parent', 'administrator'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `volunteer_roster` (Active Safety Shifts)
```sql
CREATE TABLE volunteer_roster (
    roster_id SERIAL PRIMARY KEY,
    school_id VARCHAR(50) NOT NULL,
    volunteer_name VARCHAR(100) NOT NULL,
    assigned_zone VARCHAR(100) NOT NULL, -- e.g. "Crossing Zone A"
    time_window VARCHAR(50) NOT NULL,    -- e.g. "07:45-08:15"
    shift_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled', -- 'scheduled', 'completed', 'no_show'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Serverless Ingestion (Cloud Functions)

A Python **Google Cloud Function** triggered hourly by **Cloud Scheduler** pulls precipitation forecasts from the Open-Meteo API and Waze road hazard feeds, writing the data directly into BigQuery:

```python
import functions_framework
import urllib.request
import json
from google.cloud import bigquery

@functions_framework.http
def ingest_weather_forecast(request):
    # Latitude/Longitude coordinates for school zones
    schools = [
        {"id": "school_1", "lat": 40.7782, "lon": -73.9856},
        {"id": "school_2", "lat": 40.7178, "lon": -74.0139}
    ]
    
    bq_client = bigquery.Client()
    table_id = "juaravibe01.safety_dataset.weather_forecasts"
    
    rows_to_insert = []
    for school in schools:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={school['lat']}&longitude={school['lon']}&hourly=precipitation_probability&forecast_days=1"
        try:
            req = urllib.request.urlopen(url, timeout=5)
            data = json.loads(req.read().decode())
            # Parse precip probability
            prob = data['hourly']['precipitation_probability'][0] # Next hour forecast
            rows_to_insert.append({
                "school_id": school["id"],
                "forecast_time": data['hourly']['time'][0],
                "precipitation_probability": float(prob),
                "weather_code": int(data['hourly']['weather_code'][0]) if 'weather_code' in data['hourly'] else 0
            })
        except Exception as e:
            print(f"Error fetching for {school['id']}: {e}")

    if rows_to_insert:
        errors = bq_client.insert_rows_json(table_id, rows_to_insert)
        if errors == []:
            return "Weather successfully ingested.", 200
        return f"BigQuery Insert Errors: {errors}", 500
    return "No data to ingest.", 200
```

---

## 4. Looker Studio BI Dashboard Integration

To provide administrators with advanced historical reporting:
1.  **BI Connection:** Connect Looker Studio to the `safety_dataset.crashes_raw` and `schools` tables in BigQuery.
2.  **Visualizations:** Create collision heatmaps, 15-minute risk charts, and weekly traffic trends.
3.  **Frontend Embedding:** Embed the Looker Studio report directly inside the dashboard using an iframe inside `dashboard.html`.

---

## 5. Vertex AI "Guardian AI" Agent Specification

The conversational agent "Guardian AI" is powered by **Gemini 2.5 Flash** (or Gemini 3.5 Flash) with Automatic Function Calling (AFC) via the Vertex AI Agent Builder SDK (ADK).

### 5.1 System Instructions & Guardrails
```markdown
You are "Guardian AI," a friendly, expert safety assistant representing the School-Zone Guardian platform. Your goal is to help parents, school administrators, and crossing guards plan drop-offs, pickups, and safety patrols.

CONSTRAINTS & RULES:
1. ALWAYS ground your risk assessments in data retrieved via `query_school_risk`. If no data is returned, state that you do not have sufficient information.
2. Categorize risk scores (0-100) into three tiers and color-code them: Low (Green, 0-39), Medium (Yellow, 40-69), or High (Red, 70-100).
3. For every high-risk slot, suggest a specific, safer 15-minute timing window alternative.
4. RESPONSIBLE AI POLICY: Never reference socioeconomic demographics, census block race/income statistics, or local policing levels. Assess safety strictly based on physical variables.
```

---

## 6. GCP Deployment Strategy (`juaravibe01`)

To compile, build, and deploy the stack using Antigravity CLI `agy` on the target project `juaravibe01`, follow this sequence:

1.  **Deploy AlloyDB Instance:**
    Create a PostgreSQL cluster named `zoneguardian-db` with password credentials.
2.  **Deploy Cloud Function:**
    Deploy weather ETL ingestion routines to Cloud Functions.
3.  **BigQuery Scheduled Queries:**
    Configure BigQuery Scheduled Queries to aggregate NYPD crash points inside 300m school radii every 30 minutes.
4.  **FastAPI Backend (Cloud Run):**
    *   Deploy API as container image using Cloud Build:
        ```powershell
        gcloud builds submit --tag gcr.io/juaravibe01/safety-api
        ```
    *   Deploy to Cloud Run, passing database variables:
        ```powershell
        gcloud run deploy safety-api --image gcr.io/juaravibe01/safety-api --platform managed --region us-central1 --set-env-vars DB_HOST=alloydb_ip,DB_USER=postgres,DB_PASSWORD=pwd --allow-unauthenticated
        ```
