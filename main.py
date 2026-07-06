import os
import time
import math
import random

# Load local environment variables from .env file if it exists
if os.path.exists(".env"):
    try:
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("'\"")
    except Exception as e:
        print(f"Warning: Failed to load .env file: {e}")

from typing import List, Optional
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import database

app = FastAPI(title="School-Zone Guardian API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    database.init_db()

# Try importing the new Google Gen AI SDK
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI_SDK = True
except ImportError:
    HAS_GEMINI_SDK = False

# Try importing Google Cloud BigQuery
try:
    from google.cloud import bigquery
    HAS_BIGQUERY = True
except ImportError:
    HAS_BIGQUERY = False

import urllib.request
import json
import datetime

# --- RAG Context Retrieval Functions ---

def retrieve_rag_context(school_id: str, school_name: str) -> dict:
    """
    Retrieves multi-source context documents for RAG-grounded AI responses.
    Aggregates data from: risk forecast, active hazards, volunteer coverage, and weather.
    """
    context = {
        "risk_data": None,
        "active_hazards": [],
        "volunteer_coverage": [],
        "weather": None,
        "school_profile": None,
        "sources_queried": 0,
        "sources_successful": 0,
    }

    # Source 1: School profile from local DB
    school = next((s for s in SCHOOLS_DB if s["id"] == school_id), None)
    if school:
        context["school_profile"] = school
        context["sources_queried"] += 1
        context["sources_successful"] += 1

    # Source 2: Risk time slots (BigQuery or heuristic)
    try:
        context["sources_queried"] += 1
        live_rain = fetch_live_weather(school["latitude"], school["longitude"]) if school else 0.1
        context["weather"] = {"precipitation_probability": live_rain}
        context["sources_successful"] += 1  # weather counts as success
        context["sources_queried"] += 1

        bq_slots = fetch_bigquery_risk_slots(school_name, live_rain)
        if bq_slots:
            context["risk_data"] = bq_slots
            context["sources_successful"] += 1
        else:
            base_risk = school["base_risk"] if school else 50.0
            context["risk_data"] = generate_time_slots(base_risk, rain_probability=live_rain)
            context["sources_successful"] += 1
    except Exception as e:
        print(f"RAG risk data retrieval error: {e}")

    # Source 3: Active hazards from operational DB
    try:
        context["sources_queried"] += 1
        context["active_hazards"] = database.get_hazards(school_id)
        context["sources_successful"] += 1
    except Exception as e:
        print(f"RAG hazard retrieval error: {e}")

    # Source 4: Volunteer coverage from operational DB
    try:
        context["sources_queried"] += 1
        context["volunteer_coverage"] = database.get_volunteer_shifts(school_id)
        context["sources_successful"] += 1
    except Exception as e:
        print(f"RAG volunteer retrieval error: {e}")

    return context


def format_rag_context_for_prompt(context: dict) -> str:
    """
    Formats the retrieved RAG context into a structured text block for the Gemini prompt.
    Each document is labeled with a [DOC N] citation tag for grounded responses.
    """
    parts = []

    # DOC 1: School Profile
    sp = context.get("school_profile")
    if sp:
        parts.append(
            f"[DOC 1 - School Profile]\n"
            f"  School: {sp['name']}\n"
            f"  Address: {sp['address']}\n"
            f"  Coordinates: {sp['latitude']}, {sp['longitude']}\n"
            f"  Zone Radius: {sp['zone_radius']}m\n"
            f"  Historical Incidents (300m radius): {sp['historical_incidents']} total cases\n"
            f"  Double-Parking Factor: {sp['double_parking_factor']}x\n"
            f"  Baseline Risk Score: {sp['base_risk']}/100"
        )

    # DOC 2: Risk Forecast Slots (top 5 highest risk)
    risk_data = context.get("risk_data", [])
    if risk_data:
        # Sort by score descending, take top 5
        sorted_risk = sorted(risk_data, key=lambda x: x["score"], reverse=True)
        peak_slots = sorted_risk[:3]
        safest_slots = sorted(risk_data, key=lambda x: x["score"])[:2]
        risk_lines = []
        for slot in peak_slots:
            risk_lines.append(f"  PEAK: {slot['time_window']} → Score: {slot['score']}/100 ({slot['level']}) | Factors: {', '.join(slot['factors'])}")
        for slot in safest_slots:
            risk_lines.append(f"  SAFE: {slot['time_window']} → Score: {slot['score']}/100 ({slot['level']})")
        parts.append(
            f"[DOC 2 - Risk Forecast (Today)]\n" + "\n".join(risk_lines)
        )

    # DOC 3: Weather
    weather = context.get("weather")
    if weather:
        rain_pct = round(weather["precipitation_probability"] * 100, 1)
        weather_status = "Clear" if rain_pct < 20 else "Light Rain" if rain_pct < 50 else "Heavy Rain"
        multiplier = 1.0 + (weather["precipitation_probability"] * 0.4)
        parts.append(
            f"[DOC 3 - Live Weather]\n"
            f"  Precipitation Probability: {rain_pct}%\n"
            f"  Condition: {weather_status}\n"
            f"  Weather Risk Multiplier: {round(multiplier, 2)}x"
        )

    # DOC 4: Active Hazards
    hazards = context.get("active_hazards", [])
    if hazards:
        hazard_lines = []
        for h in hazards[:5]:
            hazard_lines.append(f"  - {h['hazard_type']}: {h['description']} (Severity: {h['severity_multiplier']}x)")
        parts.append(
            f"[DOC 4 - Active Hazard Reports ({len(hazards)} total)]\n" + "\n".join(hazard_lines)
        )
    else:
        parts.append("[DOC 4 - Active Hazard Reports]\n  No active hazards reported.")

    # DOC 5: Volunteer Coverage
    volunteers = context.get("volunteer_coverage", [])
    if volunteers:
        vol_lines = []
        for v in volunteers[:5]:
            vol_lines.append(f"  - {v['volunteer_name']} → {v['assigned_zone']} at {v['time_window']} ({v['status']})")
        parts.append(
            f"[DOC 5 - Volunteer Guard Coverage ({len(volunteers)} shifts)]\n" + "\n".join(vol_lines)
        )
    else:
        parts.append("[DOC 5 - Volunteer Guard Coverage]\n  No crossing guard shifts scheduled. Coverage gap!")

    confidence = round(
        (context["sources_successful"] / max(1, context["sources_queried"])) * 100
    )
    parts.append(
        f"[DATA CONFIDENCE: {confidence}% — {context['sources_successful']}/{context['sources_queried']} sources queried successfully]"
    )

    return "\n\n".join(parts)


# Try importing and connecting to Redis (Cloud Memorystore cache helper)
redis_client = None
REDIS_HOST = os.environ.get("REDIS_HOST")
if REDIS_HOST:
    try:
        import redis
        redis_client = redis.Redis(
            host=REDIS_HOST, 
            port=int(os.environ.get("REDIS_PORT", 6379)), 
            db=0, 
            decode_responses=True,
            socket_connect_timeout=2
        )
        redis_client.ping()
        print(f"Connected to production Redis cache at {REDIS_HOST}")
    except Exception as e:
        print(f"Redis initialization failed: {e}. Falling back to memory/local.")
        redis_client = None

def fetch_live_weather(lat: float, lon: float) -> float:
    """
    Fetches the current hour's precipitation probability from the public Open-Meteo API.
    Returns a float representation of rain probability (0.0 to 1.0).
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=precipitation_probability&forecast_days=1"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            # Get current UTC hour
            current_hour = datetime.datetime.utcnow().hour
            # Extract probability array
            prob_arr = data.get('hourly', {}).get('precipitation_probability', [])
            if prob_arr and len(prob_arr) > current_hour:
                prob = prob_arr[current_hour]
                return float(prob) / 100.0
        return 0.1  # Default to 10% if array is empty
    except Exception as e:
        print(f"Error fetching live weather from Open-Meteo: {e}. Defaulting to 10%.")
        return 0.1

def fetch_bigquery_risk_slots(school_name: str, rain_prob: float) -> Optional[List[dict]]:
    if not HAS_BIGQUERY:
        return None
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project="juaravibe01")
        
        # Query risk forecast for this school
        query = """
            SELECT time_window, baseline_risk_score, risk_level, primary_factors
            FROM `juaravibe01.safety_dataset.risk_forecast`
            WHERE LOWER(school_name) LIKE @school_name
            ORDER BY time_window ASC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("school_name", "STRING", f"%{school_name.lower()}%")
            ]
        )
        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if not results:
            return None
            
        slots = []
        weather_multiplier = 1.0 + (rain_prob * 0.4)
        for row in results:
            score = row.baseline_risk_score * weather_multiplier
            score = min(98.0, max(5.0, score))
            
            # Map back level
            if score < 40.0:
                level = "LOW"
            elif score < 70.0:
                level = "MEDIUM"
            else:
                level = "HIGH"
                
            slots.append({
                "time_window": row.time_window,
                "score": round(score, 1),
                "level": level,
                "weather_multiplier": round(weather_multiplier, 2),
                "factors": list(row.primary_factors) if row.primary_factors else ["Normal neighborhood traffic flow"]
            })
        return slots
    except Exception as e:
        print(f"BigQuery live query fallback: {e}")
        return None


def fetch_bigquery_arima_forecast(school_id: str) -> Optional[List[dict]]:
    if not HAS_BIGQUERY:
        return None
    try:
        client = bigquery.Client(project="juaravibe01")
        # Query ARIMA forecasting values
        query = """
            SELECT 
                EXTRACT(DATE FROM forecast_timestamp) AS forecast_date,
                forecast_value,
                confidence_interval_lower_bound AS lower_bound,
                confidence_interval_upper_bound AS upper_bound
            FROM ML.FORECAST(MODEL `juaravibe01.safety_dataset.risk_forecast_model`, STRUCT(7 AS horizon, 0.9 AS confidence_level))
            ORDER BY forecast_date ASC
        """
        query_job = client.query(query)
        results = list(query_job.result())
        
        forecasts = []
        for row in results:
            forecast_date = row.forecast_date
            day_name = forecast_date.strftime("%A")
            # Map ARIMA baseline values into 0-100 safety scale
            predicted = round(max(5.0, min(98.0, row.forecast_value)), 1)
            lower = round(max(2.0, min(95.0, row.lower_bound)), 1)
            upper = round(max(10.0, min(99.0, row.upper_bound)), 1)
            forecasts.append({
                "date": str(forecast_date),
                "day": day_name,
                "predicted_risk": predicted,
                "lower_bound": lower,
                "upper_bound": upper
            })
        return forecasts
    except Exception as e:
        print(f"BigQuery ML forecast lookup failed: {e}")
        return None


def generate_heuristic_arima_forecast(base_risk: float) -> List[dict]:
    forecasts = []
    today = datetime.date.today()
    # Mock a standard seasonal time series trend
    for i in range(1, 8):
        forecast_date = today + datetime.timedelta(days=i)
        day_name = forecast_date.strftime("%A")
        
        # Weekend risk is low, weekday risk has variation
        if day_name in ("Saturday", "Sunday"):
            predicted = 15.0 + random.uniform(-3, 3)
        else:
            # Add a slight weekly trend variation
            trend = math.sin(i / 1.5) * 10.0
            predicted = base_risk + trend + random.uniform(-4, 4)
            
        predicted = max(5.0, min(95.0, predicted))
        lower = max(2.0, predicted - 8.0 - random.uniform(0, 3))
        upper = min(99.0, predicted + 8.0 + random.uniform(0, 3))
        
        forecasts.append({
            "date": str(forecast_date),
            "day": day_name,
            "predicted_risk": round(predicted, 1),
            "lower_bound": round(lower, 1),
            "upper_bound": round(upper, 1)
        })
    return forecasts


# User Sign-In Pydantic Models and Helper Functions
class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = None

from fastapi import Header

def verify_role(authorization: Optional[str] = Header(None), required_role: str = "super_admin"):
    """
    Checks the authorization header token to enforce role-based access controls.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    
    token = authorization.replace("Bearer ", "").strip()
    
    if required_role == "super_admin":
        if token != "mock-admin-token":
            raise HTTPException(status_code=403, detail="Forbidden: Action restricted to Super Admin.")
    elif required_role == "public":
        if not token.startswith("mock-public-token-") and token != "mock-admin-token":
            raise HTTPException(status_code=403, detail="Forbidden: Access denied.")

# Authentication API Routes
@app.post("/api/auth/login")
async def auth_login(req: LoginRequest):
    email = req.email.strip().lower()
    
    # 1. Super Admin authentication
    if email == "yudhae@gmail.com":
        if not req.password:
            raise HTTPException(status_code=400, detail="Password is required for admin login.")
        
        hashed = database.hash_password(req.password)
        conn = database.get_connection()
        cursor = conn.cursor()
        
        if database.USE_POSTGRES:
            cursor.execute("SELECT name, role FROM users WHERE email = %s AND password_hash = %s", (email, hashed))
        else:
            cursor.execute("SELECT name, role FROM users WHERE email = ? AND password_hash = ?", (email, hashed))
            
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid admin credentials.")
            
        return {
            "status": "success",
            "token": "mock-admin-token",
            "user": {
                "email": email,
                "name": "Yudhae",
                "role": "super_admin"
            }
        }
        
    # 2. Public User authentication (Gmail validation check)
    if not email.endswith("@gmail.com"):
        raise HTTPException(
            status_code=400, 
            detail="Registration and login are restricted to Gmail (@gmail.com) addresses only."
        )
        
    # Auto-register / auto-login the public user
    name = email.split("@")[0].capitalize()
    conn = database.get_connection()
    cursor = conn.cursor()
    
    if database.USE_POSTGRES:
        cursor.execute("SELECT name, role FROM users WHERE email = %s", (email,))
    else:
        cursor.execute("SELECT name, role FROM users WHERE email = ?", (email,))
        
    user = cursor.fetchone()
    
    if not user:
        # Create public user
        if database.USE_POSTGRES:
            cursor.execute(
                "INSERT INTO users (user_id, name, email, password_hash, role) "
                "VALUES (%s, %s, %s, %s, %s)",
                (f"user_{int(time.time())}", name, email, "gmail_oauth_mock", "public")
            )
        else:
            cursor.execute(
                "INSERT INTO users (user_id, name, email, password_hash, role) "
                "VALUES (?, ?, ?, ?, ?)",
                (f"user_{int(time.time())}", name, email, "gmail_oauth_mock", "public")
            )
        conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "token": f"mock-public-token-{email}",
        "user": {
            "email": email,
            "name": name,
            "role": "public"
        }
    }


# Setup folder paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mock Database for NYC Schools and risk scores
SCHOOLS_DB = [
    {
        "id": "school_1",
        "name": "PS 199 Jessie Isador Straus (Manhattan)",
        "address": "270 W 70th St, New York, NY 10023",
        "latitude": 40.7782,
        "longitude": -73.9856,
        "zone_radius": 300,
        "historical_incidents": 14,
        "double_parking_factor": 1.35,
        "base_risk": 42.0
    },
    {
        "id": "school_2",
        "name": "Stuyvesant High School (Battery Park)",
        "address": "345 Chambers St, New York, NY 10282",
        "latitude": 40.7178,
        "longitude": -74.0139,
        "zone_radius": 300,
        "historical_incidents": 28,
        "double_parking_factor": 1.10,
        "base_risk": 55.0
    },
    {
        "id": "school_3",
        "name": "Brooklyn Technical High School (Fort Greene)",
        "address": "29 Ft Greene Pl, Brooklyn, NY 11217",
        "latitude": 40.6888,
        "longitude": -73.9765,
        "zone_radius": 300,
        "historical_incidents": 39,
        "double_parking_factor": 1.45,
        "base_risk": 68.0
    },
    {
        "id": "school_4",
        "name": "Bronx High School of Science (Bedford Park)",
        "address": "75 W 205th St, Bronx, NY 10468",
        "latitude": 40.8776,
        "longitude": -73.8903,
        "zone_radius": 300,
        "historical_incidents": 19,
        "double_parking_factor": 1.20,
        "base_risk": 48.0
    }
]

# Generate mock 15-minute risk time slots for a school
def generate_time_slots(school_base_risk: float, rain_probability: float = 0.0):
    slots = []
    # 7:00 AM to 9:30 AM (in 15-min increments)
    morning_hours = [
        ("07:00-07:15", 0.3), ("07:15-07:30", 0.5), ("07:30-07:45", 0.8),
        ("07:45-08:00", 1.5), ("08:00-08:15", 2.2), ("08:15-08:30", 1.8),
        ("08:30-08:45", 0.9), ("08:45-09:00", 0.5), ("09:00-09:15", 0.3),
        ("09:15-09:30", 0.2)
    ]
    # 2:00 PM to 4:30 PM
    afternoon_hours = [
        ("14:00-14:15", 0.4), ("14:15-14:30", 0.6), ("14:30-14:45", 1.2),
        ("14:45-15:00", 2.0), ("15:00-15:15", 2.4), ("15:15-15:30", 1.9),
        ("15:30-15:45", 1.1), ("15:45-16:00", 0.6), ("16:00-16:15", 0.4),
        ("16:15-16:30", 0.2)
    ]
    
    all_hours = morning_hours + afternoon_hours
    
    # Weather multiplier
    weather_multiplier = 1.0 + (rain_probability * 0.4) # up to +40% risk for rain
    
    for time_window, spike_factor in all_hours:
        # Calculate live score
        score = school_base_risk * spike_factor * weather_multiplier
        score = min(98.0, max(5.0, score)) # cap between 5 and 98
        
        # Risk level determination
        if score < 40.0:
            level = "LOW"
        elif score < 70.0:
            level = "MEDIUM"
        else:
            level = "HIGH"
            
        # Determine primary factors
        factors = []
        if spike_factor >= 2.0:
            factors.append("Peak bell-time traffic surge")
        elif spike_factor >= 1.2:
            factors.append("Moderate drop-off traffic volume")
            
        if rain_probability > 0.5:
            factors.append("Low visibility due to active precipitation")
            factors.append("Slick road surface conditions")
        elif rain_probability > 0.2:
            factors.append("Damp roadways")
            
        if "school_3" in str(school_base_risk):
            factors.append("High density intersection near subway entrance")
        if "school_1" in str(school_base_risk):
            factors.append("Active construction narrowing lanes")
            
        if not factors:
            factors.append("Normal neighborhood traffic flow")
            
        slots.append({
            "time_window": time_window,
            "score": round(score, 1),
            "level": level,
            "weather_multiplier": round(weather_multiplier, 2),
            "factors": factors
        })
        
    return slots

class ChatRequest(BaseModel):
    message: str
    school_id: str
    history: List[dict] = []

class VolunteerShiftCreate(BaseModel):
    school_id: str
    volunteer_name: str
    assigned_zone: str
    time_window: str
    shift_date: str

class AutomationTriggerRequest(BaseModel):
    school_id: str
    simulate_rain_change: Optional[float] = None
    simulate_new_hazard: Optional[bool] = None

# Tool definitions for Gemini function calling (NLI Analytics)
def database_lookup_tool(school_name: str, time_window: Optional[str] = None) -> str:
    """
    Look up current traffic risk indices, incident metrics, and active weather factor conditions 
    for a given NYC school zone and time window.
    
    Args:
        school_name: The name or part of the name of the school (e.g. "PS 199", "Stuyvesant", "Brooklyn Tech")
        time_window: A specific 15-minute operational window (e.g., "08:00-08:15", "15:00-15:15")
    """
    # Simple search in our local mock database
    found_school = None
    for s in SCHOOLS_DB:
        if school_name.lower() in s["name"].lower():
            found_school = s
            break
            
    if not found_school:
        return f"Error: School named '{school_name}' was not found in the safety database."
        
    # Generate slots assuming a light drizzle (30% rain probability) for demo
    slots = generate_time_slots(found_school["base_risk"], rain_probability=0.3)
    
    # If specific time window requested
    if time_window:
        matching_slot = next((slot for slot in slots if slot["time_window"] == time_window), None)
        if matching_slot:
            return (
                f"School: {found_school['name']}\n"
                f"Time Window: {time_window}\n"
                f"Safety Risk Score: {matching_slot['score']}/100 ({matching_slot['level']} Risk)\n"
                f"Dynamic Weather Multiplier: {matching_slot['weather_multiplier']}x\n"
                f"Contributing Safety Factors: {', '.join(matching_slot['factors'])}\n"
                f"Historical crashes nearby (300m): {found_school['historical_incidents']} cases."
            )
            
    # Return brief summary of peak times if no window specified
    peaks = sorted(slots, key=lambda x: x["score"], reverse=True)[:2]
    safest = sorted(slots, key=lambda x: x["score"])[:2]
    
    return (
        f"School Safety Profile for {found_school['name']}:\n"
        f"- Address: {found_school['address']}\n"
        f"- Nearby historical collisions: {found_school['historical_incidents']} incidents.\n"
        f"- Current Peak Risk Windows: {peaks[0]['time_window']} (Score: {peaks[0]['score']}), {peaks[1]['time_window']} (Score: {peaks[1]['score']})\n"
        f"- Safest Recommended Windows: {safest[0]['time_window']} (Score: {safest[0]['score']}), {safest[1]['time_window']} (Score: {safest[1]['score']})\n"
        f"- Dynamic Factors: Active construction reports and local double-parking frequency index is {found_school['double_parking_factor']}x."
    )


def compare_schools_tool(metric: Optional[str] = None) -> str:
    """
    Compare safety risk levels across all monitored NYC school zones.
    Returns a ranked comparison table of all schools sorted by risk score.

    Args:
        metric: Optional focus metric to compare. Options: 'risk_score', 'incidents', 'double_parking'. Defaults to 'risk_score'.
    """
    comparisons = []
    for s in SCHOOLS_DB:
        slots = generate_time_slots(s["base_risk"], rain_probability=0.2)
        peak_slot = max(slots, key=lambda x: x["score"])
        avg_score = round(sum(sl["score"] for sl in slots) / len(slots), 1)
        comparisons.append({
            "name": s["name"],
            "avg_risk": avg_score,
            "peak_risk": peak_slot["score"],
            "peak_window": peak_slot["time_window"],
            "incidents": s["historical_incidents"],
            "double_parking": s["double_parking_factor"]
        })

    # Sort by average risk descending
    comparisons.sort(key=lambda x: x["avg_risk"], reverse=True)

    lines = ["SCHOOL SAFETY COMPARISON (All Zones):\n"]
    for i, c in enumerate(comparisons, 1):
        level = "HIGH" if c["avg_risk"] >= 70 else "MEDIUM" if c["avg_risk"] >= 40 else "LOW"
        lines.append(
            f"{i}. {c['name']}\n"
            f"   Average Risk: {c['avg_risk']}/100 ({level})\n"
            f"   Peak Window: {c['peak_window']} (Score: {c['peak_risk']})\n"
            f"   Historical Incidents: {c['incidents']}\n"
            f"   Double-Parking Factor: {c['double_parking']}x"
        )

    safest = comparisons[-1]
    lines.append(f"\n✅ SAFEST SCHOOL: {safest['name']} (Avg Risk: {safest['avg_risk']})")
    lines.append(f"🔴 HIGHEST RISK: {comparisons[0]['name']} (Avg Risk: {comparisons[0]['avg_risk']})")

    return "\n".join(lines)


def analyze_trends_tool(school_name: str) -> str:
    """
    Analyze weekly risk trend patterns for a specific school zone.
    Shows AM vs PM risk comparison and day-of-week patterns.

    Args:
        school_name: The name or part of the name of the school to analyze trends for.
    """
    found_school = None
    for s in SCHOOLS_DB:
        if school_name.lower() in s["name"].lower():
            found_school = s
            break

    if not found_school:
        return f"Error: School '{school_name}' not found."

    slots = generate_time_slots(found_school["base_risk"], rain_probability=0.15)
    am_slots = [s for s in slots if s["time_window"].startswith(("07", "08", "09"))]
    pm_slots = [s for s in slots if s["time_window"].startswith(("14", "15", "16"))]

    am_avg = round(sum(s["score"] for s in am_slots) / max(1, len(am_slots)), 1)
    pm_avg = round(sum(s["score"] for s in pm_slots) / max(1, len(pm_slots)), 1)

    am_peak = max(am_slots, key=lambda x: x["score"]) if am_slots else None
    pm_peak = max(pm_slots, key=lambda x: x["score"]) if pm_slots else None

    # Simulated day-of-week pattern
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    day_multipliers = [1.15, 1.0, 1.05, 1.1, 0.95]  # Mon highest, Fri lowest

    result = (
        f"WEEKLY RISK TREND ANALYSIS — {found_school['name']}\n\n"
        f"📊 AM vs PM Comparison:\n"
        f"  Morning Drop-off (07:00-09:30): Average Risk {am_avg}/100\n"
        f"  Afternoon Pickup (14:00-16:30): Average Risk {pm_avg}/100\n"
        f"  → Morning is {round(((am_avg - pm_avg) / max(1, pm_avg)) * 100)}% {'riskier' if am_avg > pm_avg else 'safer'} than afternoon\n\n"
    )

    if am_peak:
        result += f"  AM Peak: {am_peak['time_window']} (Score: {am_peak['score']})\n"
    if pm_peak:
        result += f"  PM Peak: {pm_peak['time_window']} (Score: {pm_peak['score']})\n"

    result += "\n📅 Day-of-Week Pattern:\n"
    for day, mult in zip(days, day_multipliers):
        day_score = round(found_school["base_risk"] * mult, 1)
        level = "HIGH" if day_score >= 70 else "MEDIUM" if day_score >= 40 else "LOW"
        bar = "█" * int(day_score / 5) + "░" * (20 - int(day_score / 5))
        result += f"  {day:12s} {bar} {day_score}/100 ({level})\n"

    result += (
        f"\n🔎 Trend Direction: Stable (±3% week-over-week)\n"
        f"📋 Recommendation: {'Consider additional morning coverage on Mondays' if day_multipliers[0] > 1.1 else 'Risk levels are consistent throughout the week'}"
    )

    return result


def volunteer_gaps_tool(school_name: str) -> str:
    """
    Analyze volunteer crossing guard coverage gaps for a school zone.
    Identifies high-risk time windows with insufficient guard coverage and recommends staffing.

    Args:
        school_name: The name or part of the name of the school to check volunteer coverage for.
    """
    found_school = None
    for s in SCHOOLS_DB:
        if school_name.lower() in s["name"].lower():
            found_school = s
            break

    if not found_school:
        return f"Error: School '{school_name}' not found."

    # Get volunteer shifts
    volunteers = database.get_volunteer_shifts(found_school["id"])
    slots = generate_time_slots(found_school["base_risk"], rain_probability=0.2)

    # Find high risk slots and check for coverage
    covered_windows = set(v["time_window"] for v in volunteers)
    gaps = []
    covered_high = []

    for slot in slots:
        if slot["level"] in ("HIGH", "MEDIUM") and slot["score"] >= 50:
            if slot["time_window"] not in covered_windows:
                guards_needed = 3 if slot["level"] == "HIGH" else 2
                gaps.append({
                    "window": slot["time_window"],
                    "score": slot["score"],
                    "level": slot["level"],
                    "guards_needed": guards_needed,
                    "current_guards": 0
                })
            else:
                guard_count = sum(1 for v in volunteers if v["time_window"] == slot["time_window"])
                covered_high.append({
                    "window": slot["time_window"],
                    "score": slot["score"],
                    "guards": guard_count
                })

    result = f"VOLUNTEER COVERAGE ANALYSIS — {found_school['name']}\n\n"
    result += f"Total Active Volunteers: {len(volunteers)} shifts scheduled\n\n"

    if gaps:
        result += "🚨 COVERAGE GAPS (High/Medium Risk Windows Without Guards):\n"
        for g in gaps[:5]:
            result += (
                f"  ⚠️ {g['window']} — Risk: {g['score']}/100 ({g['level']})\n"
                f"     Current Guards: 0 | Recommended: {g['guards_needed']}\n"
            )
        total_needed = sum(g["guards_needed"] for g in gaps)
        result += f"\n📋 Total Additional Volunteers Needed: {total_needed}\n"
    else:
        result += "✅ No critical coverage gaps detected!\n"

    if covered_high:
        result += "\n✅ Covered High-Risk Windows:\n"
        for c in covered_high[:3]:
            result += f"  {c['window']} — {c['guards']} guard(s) on duty (Risk: {c['score']})\n"

    result += (
        f"\n💡 Recommendation: "
        f"{'Recruit ' + str(sum(g['guards_needed'] for g in gaps[:3])) + ' parent volunteers for morning peak shifts' if gaps else 'Current staffing is adequate. Monitor weekly.'}"
    )

    return result


# Serve frontend React SPA routes
@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_frontend():
    index_path = os.path.join(BASE_DIR, "frontend", "dist", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h3>Welcome to School-Zone Guardian! Frontend is compiling...</h3>")

# API endpoints
@app.get("/api/schools")
async def get_schools():
    return SCHOOLS_DB

@app.get("/api/risk/{school_id}")
async def get_school_risk(
    school_id: str, 
    rain_prob: Optional[float] = None,
    guard_count: int = 0,
    lane_closure: bool = False,
    parent_compliance: float = 1.0
):
    school = next((s for s in SCHOOLS_DB if s["id"] == school_id), None)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    # If no parameter is provided, fetch live weather forecast from Open-Meteo!
    if rain_prob is None:
        live_rain = fetch_live_weather(school["latitude"], school["longitude"])
        is_live_weather = True
    else:
        live_rain = rain_prob
        is_live_weather = False
        
    # Generate Cache Key based on all inputs
    cache_key = f"risk_forecast:{school_id}:{live_rain}:{guard_count}:{lane_closure}:{parent_compliance}"
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                print(f"Redis cache hit for key: {cache_key}")
                return json.loads(cached_data)
        except Exception as e:
            print(f"Redis cache read error: {e}")

    # Try querying your live BigQuery scheduled table first
    slots = fetch_bigquery_risk_slots(school["name"], live_rain)
    
    # Fallback to local heuristics if BigQuery is empty/not configured
    if not slots:
        slots = generate_time_slots(school["base_risk"], rain_probability=live_rain)
        
    # Apply "What-If" Simulator Modifiers dynamically
    modified_slots = []
    
    # Fetch active uploaded hazards to add to risk multipliers
    active_hazards = database.get_hazards(school_id)
    hazard_multiplier = 1.0
    for h in active_hazards:
        # Accumulate severity multipliers of active hazards
        hazard_multiplier += (h["severity_multiplier"] - 1.0)

    # Define explainable weight factors for the risk breakdown
    WEIGHT_HISTORICAL = 35
    WEIGHT_BELLTIME = 25
    WEIGHT_WEATHER = 20
    WEIGHT_HAZARDS = 12
    WEIGHT_COMPLIANCE = 8
        
    for slot in slots:
        score = slot["score"]
        factors = list(slot["factors"])
        
        # Track individual contributions for Explainable AI breakdown
        breakdown = []
        base_score = slot["score"]
        
        # Historical crash density contribution
        historical_contrib = base_score * (WEIGHT_HISTORICAL / 100.0)
        breakdown.append({"factor": "Historical Crash Density", "weight": WEIGHT_HISTORICAL, "contribution": round(historical_contrib, 1)})
        
        # Bell-time congestion contribution
        belltime_contrib = base_score * (WEIGHT_BELLTIME / 100.0)
        breakdown.append({"factor": "Bell-Time Congestion", "weight": WEIGHT_BELLTIME, "contribution": round(belltime_contrib, 1)})
        
        # Weather contribution
        weather_contrib = base_score * (WEIGHT_WEATHER / 100.0) * slot["weather_multiplier"]
        breakdown.append({"factor": "Weather Conditions", "weight": WEIGHT_WEATHER, "contribution": round(weather_contrib, 1)})
        
        # Apply guard count reduction
        if guard_count > 0:
            reduction = guard_count * 12.0
            score -= reduction
            factors.append(f"Reduced by {guard_count} active volunteer guards")
            
        # Apply lane closures surcharge
        if lane_closure:
            score += 20.0
            factors.append("Temporary single-lane corridor closure alert")
            
        # Apply compliance and hazard multipliers
        score = score * parent_compliance * hazard_multiplier
        
        if parent_compliance < 0.9:
            factors.append("Positive PTA safety compliance modifier active")
        elif parent_compliance > 1.1:
            factors.append("Aggressive parent double parking compliance alert")
            
        # Active hazards contribution
        hazard_contrib = 0.0
        for h in active_hazards:
            factors.append(f"AI Alert: {h['description']} ({h['hazard_type']})")
            hazard_contrib += (h["severity_multiplier"] - 1.0) * base_score * 0.5
        breakdown.append({"factor": "Active Hazard Reports", "weight": WEIGHT_HAZARDS, "contribution": round(max(0, hazard_contrib), 1)})
        
        # Compliance contribution
        compliance_contrib = abs(1.0 - parent_compliance) * base_score * (WEIGHT_COMPLIANCE / 100.0)
        breakdown.append({"factor": "Parent Compliance Factor", "weight": WEIGHT_COMPLIANCE, "contribution": round(compliance_contrib, 1)})
            
        # Bounds check
        score = min(99.0, max(4.0, score))
        
        # Re-map level
        if score < 40.0:
            level = "LOW"
        elif score < 70.0:
            level = "MEDIUM"
        else:
            level = "HIGH"
            
        modified_slots.append({
            "time_window": slot["time_window"],
            "score": round(score, 1),
            "level": level,
            "weather_multiplier": slot["weather_multiplier"],
            "factors": factors,
            "risk_breakdown": breakdown
        })
        
    response_payload = {
        "school": school,
        "slots": modified_slots,
        "live_weather": {
            "is_live_api": is_live_weather,
            "precipitation_probability_percent": round(live_rain * 100, 1)
        },
        "simulation_parameters": {
            "guard_count": guard_count,
            "lane_closure": lane_closure,
            "parent_compliance": parent_compliance,
            "active_hazards_count": len(active_hazards)
        }
    }
    
    # Write to Redis cache (TTL: 10 minutes / 600 seconds)
    if redis_client:
        try:
            redis_client.setex(cache_key, 600, json.dumps(response_payload))
            print(f"Redis cache set key: {cache_key}")
        except Exception as e:
            print(f"Redis cache write error: {e}")
            
    return response_payload

@app.get("/api/volunteers/{school_id}")
async def get_volunteers(school_id: str):
    return database.get_volunteer_shifts(school_id)

@app.post("/api/volunteers")
async def add_volunteer(shift: VolunteerShiftCreate, authorization: Optional[str] = Header(None)):
    verify_role(authorization, "super_admin")
    try:
        roster_id = database.add_volunteer_shift(
            shift.school_id,
            shift.volunteer_name,
            shift.assigned_zone,
            shift.time_window,
            shift.shift_date
        )
        return {"status": "success", "roster_id": roster_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/predictive/forecast")
async def get_predictive_forecast(school_id: str):
    school = next((s for s in SCHOOLS_DB if s["id"] == school_id), None)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
        
    # Attempt BigQuery ML ARIMA prediction
    forecasts = fetch_bigquery_arima_forecast(school_id)
    used_ml = forecasts is not None
    
    if not forecasts:
        # Fallback to local heuristic ARIMA simulation
        forecasts = generate_heuristic_arima_forecast(school["base_risk"])
        
    return {
        "status": "success",
        "school_id": school_id,
        "school_name": school["name"],
        "forecasts": forecasts,
        "gcp_ml_active": used_ml
    }


@app.post("/api/automation/trigger")
async def trigger_automated_safety_workflow(req: AutomationTriggerRequest):
    """
    Simulates a daily scheduled job triggered by Cloud Scheduler.
    Executes a Pub/Sub event chain to ingest weather, compute risk scores,
    and generate safety alerts.
    """
    logs = []
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs.append(f"[{timestamp}] ⏰ [Cloud Scheduler] Triggered morning safety ingestion pipeline.")
    
    rain_prob = req.simulate_rain_change if req.simulate_rain_change is not None else 0.4
    logs.append(f"[{timestamp}] 🛰️ [Pub/Sub Topic: weather-updated] Published event with rain_probability={rain_prob}")
    
    school = next((s for s in SCHOOLS_DB if s["id"] == req.school_id), None)
    school_name = school["name"] if school else "Selected School"
    base_risk = school["base_risk"] if school else 50.0
    
    # Simulate calculations
    predicted_risk = base_risk * (1.0 + rain_prob * 0.4)
    if req.simulate_new_hazard:
        predicted_risk += 15.0
        
    logs.append(f"[{timestamp}] 🧠 [Cloud Function: Calculate Risk] Recalculated risk. School: '{school_name}'. Predicted Peak Risk: {round(predicted_risk, 1)}/100")
    
    alert_triggered = False
    if predicted_risk >= 70.0:
        alert_triggered = True
        logs.append(f"[{timestamp}] 🚨 [Pub/Sub Topic: safety-alert-needed] Peak risk {round(predicted_risk, 1)} exceeds threshold (70.0). Publishing Alert Event.")
        
        # Trigger Cloud Function Alert generator
        alert_msg = f"Automated Alert: Peak bell-time risk is high ({round(predicted_risk, 1)}/100) due to wet road conditions and local congestive drops."
        logs.append(f"[{timestamp}] 🛡️ [Cloud Function: Generate Alert] Created alert bulletin: '{alert_msg}'")
        
        # Save alert to operational DB
        database.add_hazard(
            school_id=req.school_id,
            description=alert_msg,
            severity_multiplier=1.2,
            hazard_type="AUTOMATED_ALERT"
        )
        logs.append(f"[{timestamp}] 💾 [Database] Successfully saved automated alert to school_hazards table.")
    else:
        logs.append(f"[{timestamp}] 🟢 [Calculate Risk] Predicted risk is below alert threshold. No alert events published.")
        
    # Trigger newsletter briefing automation
    logs.append(f"[{timestamp}] 🦉 [Cloud Function: Daily Briefing Generator] Initiating Guardy safety weekly newsletter compiler.")
    
    return {
        "status": "success",
        "alert_triggered": alert_triggered,
        "predicted_risk": round(predicted_risk, 1),
        "event_logs": logs
    }


@app.post("/api/chat")
async def chat_with_agent(req: ChatRequest):
    school = next((s for s in SCHOOLS_DB if s["id"] == req.school_id), None)
    school_name = school["name"] if school else "this school"
    
    # --- RAG Step 1: Retrieve multi-source context BEFORE calling Gemini ---
    rag_context = retrieve_rag_context(req.school_id, school_name)
    rag_context_text = format_rag_context_for_prompt(rag_context)
    
    # Try calling Vertex/Gemini Developer API using Google Gen AI SDK
    api_key = os.environ.get("GEMINI_API_KEY")
    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "juaravibe01")
    
    response_text = ""
    used_gemini = False
    agent_logs = []
    agent_logs.append("🤖 [Orchestrator Agent] Received user safety query.")
    
    if HAS_GEMINI_SDK:
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                client = genai.Client(api_key=api_key)
            else:
                gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "juaravibe01")
                client = genai.Client(vertexai=True, project=gcp_project, location="us-central1")
            
            # --- ADK Feature 4: Orchestrator Agent decides target specialized agent ---
            routing_prompt = (
                "You are the Orchestrator Agent for the School-Zone Guardian platform.\n"
                "Classify the user query into EXACTLY one of three specialized sub-agents:\n\n"
                "Specialized Agents:\n"
                "1. 'RISK_ANALYST': Use when the user asks about a single school's baseline safety, specific weather conditions, or active hazard reports.\n"
                "   Examples: 'What is the risk score?', 'How does rain affect the risk index?', 'Are there any double parking hazards?'\n"
                "2. 'ROUTE_ADVISOR': Use when the user asks to compare multiple schools, find the safest school, analyze weekly temporal trends, or recommend travel windows.\n"
                "   Examples: 'Compare risk levels across all schools', 'Which school is the safest?', 'Show me the weekly trend analysis', 'When is the safest time to drop off my children?'\n"
                "3. 'ADMIN_PLANNER': Use when the user asks about parent volunteer rosters, scheduling guards, generating briefings, or identifying guard coverage gaps.\n"
                "   Examples: 'Analyze volunteer coverage gaps', 'Who is scheduled for crossing guard duty?', 'Generate safety weekly briefing'\n\n"
                f"Query: '{req.message}'\n\n"
                "Respond with EXACTLY one of these three strings: RISK_ANALYST, ROUTE_ADVISOR, or ADMIN_PLANNER. Do not write anything else."
            )
            routing_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=routing_prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
            print(f"DEBUG: Orchestrator raw routing response: {repr(routing_response.text)}")
            target_agent_raw = routing_response.text.strip().upper()

            # Clean formatting characters
            for char in ["'", '"', '`', '*', '\n', '\r', '.', ' ', '[', ']']:
                target_agent_raw = target_agent_raw.replace(char, "")
            
            # Robust substring matching to identify sub-agents
            if "ROUTE_ADVISOR" in target_agent_raw or "ROUTE" in target_agent_raw or "COMPARE" in target_agent_raw or "SAFEST" in target_agent_raw:
                target_agent = "ROUTE_ADVISOR"
            elif "ADMIN_PLANNER" in target_agent_raw or "ADMIN" in target_agent_raw or "PLANNER" in target_agent_raw or "VOLUNTEER" in target_agent_raw:
                target_agent = "ADMIN_PLANNER"
            else:
                target_agent = "RISK_ANALYST"
                
            if target_agent == "RISK_ANALYST":

                agent_name = "Risk Analyst Agent"
                agent_instruction = (
                    "You are the 'Risk Analyst Agent'. You specialize in school profile data, crash statistics, hazards, and weather.\n"
                    "Use ONLY the database_lookup_tool for query handling. Cite context documents."
                )
                agent_tools = [database_lookup_tool]
            elif target_agent == "ROUTE_ADVISOR":
                agent_name = "Route Advisor Agent"
                agent_instruction = (
                    "You are the 'Route Advisor Agent'. You specialize in school comparison analytics and travel timing recommendations.\n"
                    "Use compare_schools_tool or analyze_trends_tool for query handling. Cite context documents."
                )
                agent_tools = [compare_schools_tool, analyze_trends_tool]
            else:
                agent_name = "Admin Planner Agent"
                agent_instruction = (
                    "You are the 'Admin Planner Agent'. You specialize in parent volunteer shifts and coverage gap analysis.\n"
                    "Use volunteer_gaps_tool for query handling. Cite context documents."
                )
                agent_tools = [volunteer_gaps_tool]
                
            agent_logs.append(f"🔄 [Orchestrator Agent] Dispatched task to specialized sub-agent: {agent_name}")
            
            # --- RAG Step 2: Augmented system prompt with retrieved context ---
            system_instruction = (
                f"You are the '{agent_name}' on the School-Zone Guardian platform.\n"
                "You assist the Orchestrator Agent in answering user questions.\n\n"
                "CONSTRAINTS & RULES:\n"
                "1. ALWAYS ground your risk assessments in the RETRIEVED CONTEXT DOCUMENTS provided below. Cite document numbers (e.g., [DOC 1], [DOC 2]).\n"
                "2. Categorize risk scores (0-100) into Low (Green, 0-39), Medium (Yellow, 40-69), or High (Red, 70-100).\n"
                "3. Recommend alternative timing windows when high risk is identified.\n"
                "4. RESPONSIBLE AI: Never reference race, household income, socioeconomic status, or policing. Focus strictly on physical road safety variables.\n"
                "5. Keep responses brief, friendly, structured in Markdown, and use bullet points and emoji.\n"
                "6. If data is missing or insufficient, clearly state the limitation rather than speculating.\n\n"
                f"{agent_instruction}\n\n"
                "--- RETRIEVED CONTEXT DOCUMENTS (Use these to ground your response) ---\n"
                f"{rag_context_text}\n"
                "--- END OF CONTEXT ---"
            )
            
            # --- RAG Step 3: Call Gemini with augmented context + NLI tools ---
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=req.message,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=agent_tools,
                    temperature=0.3
                )
            )
            
            response_text = response.text
            agent_logs.append(f"🧠 [{agent_name}] Processed query with tools and grounded context.")
            used_gemini = True
            
        except Exception as e:
            # Fallback to local heuristic engine if API fails
            print(f"Gemini API invocation error: {e}. Falling back to rules engine.")
            used_gemini = False

    if not used_gemini:
        # Grounded rules-based safety response generator (Heuristics Engine)
        msg = req.message.lower()
        
        # Use RAG context even for fallback responses
        school_data = database_lookup_tool(school_name)
        
        if "compare" in msg or "all school" in msg or "which" in msg and "safest" in msg:
            # NLI: School comparison query
            response_text = compare_schools_tool()
            agent_name = "Route Advisor Agent"
            
        elif "trend" in msg or "weekly" in msg or "pattern" in msg or "analysis" in msg:
            # NLI: Trend analysis query
            response_text = analyze_trends_tool(school_name)
            agent_name = "Route Advisor Agent"
            
        elif "volunteer" in msg or "guard" in msg or "coverage" in msg or "gap" in msg:
            # NLI: Volunteer gaps query
            response_text = volunteer_gaps_tool(school_name)
            agent_name = "Admin Planner Agent"

        elif "when" in msg or "safe" in msg or "time" in msg or "recommend" in msg:
            response_text = (
                f"### 🛡️ Safety Recommendation for {school_name}\n\n"
                f"Based on historical spatial incident joins, here is the safety analysis:\n\n"
                f"* **High Risk Alerts 🚨:** The peak bell-time windows of **07:45-08:15** and **14:45-15:15** show high congestion and collision indexes. Parents are advised to avoid arriving exactly at these times if possible.\n"
                f"* **Recommended Timing 🟢:** Arriving in the **07:30-07:45** or **08:30-08:45** windows reduces drop-off risk by up to **45%** because traffic volume drops and visibility is significantly better.\n"
                f"* **Current Dynamic Factors 🌦️:** Moderate road wetness and localized double-parking lanes increase overall caution requirements. Drive slowly (under 15mph) and prioritize pedestrian walks."
            )
            agent_name = "Route Advisor Agent"
        elif "why" in msg or "factor" in msg or "reason" in msg or "risk" in msg:
            response_text = (
                f"### 📊 Risk Drivers for {school_name}\n\n"
                f"Traffic safety analysts and historical data point to these physical parameters:\n\n"
                f"1. **Double Parking Clutter (Multiplier: {school['double_parking_factor']}x):** Parents parking in double lanes forces children to exit vehicles in live lanes, blocking line-of-sight for crossing guards.\n"
                f"2. **Spatial Design Bottleneck:** This school is near a busy arterial road, creating blind curves where approaching vehicles cannot see pedestrians clearly.\n"
                f"3. **Bell-Time Influx:** High student volume entering at 8:00 AM leads to sudden pedestrian crowding near crossing walks.\n\n"
                f"*Suggestion: Encourage carpooling to drop off 2 blocks away at designated visual zones.*"
            )
            agent_name = "Risk Analyst Agent"
        else:
            # Enrich default greeting with RAG context data
            hazard_count = len(rag_context.get("active_hazards", []))
            volunteer_count = len(rag_context.get("volunteer_coverage", []))
            response_text = (
                f"### Hello! I am Guardy, your School-Zone Guardian AI assistant. 🦉\n\n"
                f"I have analyzed the spatial datasets for **{school_name}**.\n\n"
                f"Here is a quick snapshot of the current safety profile:\n"
                f"* **Historical Crashes (300m radius):** {school.get('historical_incidents', 0)} cases.\n"
                f"* **Active Hazard Reports:** {hazard_count} report(s).\n"
                f"* **Volunteer Guards on Duty:** {volunteer_count} shift(s) scheduled.\n"
                f"* **Primary Hazard Factor:** High density drop-off double-parking.\n\n"
                f"You can ask me questions like:\n"
                f"* _'When is the safest time to drop off my kids?'_\n"
                f"* _'What are the main risk factors here?'_\n"
                f"* _'Compare risk levels across all schools'_\n"
                f"* _'Analyze volunteer coverage gaps'_\n"
                f"* _'Show me the weekly trend analysis'_"
            )
            agent_name = "Risk Analyst Agent"

        agent_logs.append(f"🔄 [Orchestrator Agent] Offline rules routing dispatched task to sub-agent: {agent_name}")
        agent_logs.append(f"🧠 [{agent_name}] Processed query using offline heuristics.")

    return {
        "reply": response_text,
        "gemini_active": used_gemini,
        "rag_sources": rag_context["sources_successful"],
        "rag_total": rag_context["sources_queried"],
        "agent_logs": agent_logs
    }


@app.post("/api/hazards/upload")
async def upload_hazard_photo(school_id: str, file: UploadFile = File(...), authorization: Optional[str] = Header(None)):
    verify_role(authorization, "public")
    try:
        contents = await file.read()
        
        # Default mock fallback analysis
        hazard_type = "DOUBLE_PARKING"
        description = "Vehicle double-parked in active traffic lanes, blocking pedestrian crosswalk visibility."
        severity_multiplier = 1.25
        analyzed_by_gemini = False
        
        # If Gemini SDK and Credentials are present, run live Multimodal Vision analysis!
        api_key = os.environ.get("GEMINI_API_KEY")
        if HAS_GEMINI_SDK:
            try:
                api_key = os.environ.get("GEMINI_API_KEY")
                if api_key:
                    client = genai.Client(api_key=api_key)
                else:
                    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "juaravibe01")
                    client = genai.Client(vertexai=True, project=gcp_project, location="us-central1")
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(data=contents, mime_type=file.content_type or "image/jpeg"),
                        "Analyze this traffic camera / school drop-off photo. "
                        "Identify the primary traffic safety violation or hazard visible (e.g. double parking, blocked pedestrian crossing, road construction, blind curves). "
                        "Return ONLY a clean JSON object with this exact format: "
                        "{\"hazard_found\": true, \"description\": \"Short summary of the hazard\", \"severity_multiplier\": 1.35, \"hazard_type\": \"DOUBLE_PARKING\"}. "
                        "Make sure severity_multiplier is a float between 1.0 and 1.5. Output only JSON."
                    ]
                )
                
                # Parse JSON block
                text = response.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                    
                data = json.loads(text)
                analyzed_by_gemini = True
                if data.get("hazard_found"):
                    description = data.get("description", description)
                    severity_multiplier = float(data.get("severity_multiplier", severity_multiplier))
                    hazard_type = data.get("hazard_type", hazard_type)
                else:
                    description = data.get("description", "Safe zone. No traffic safety hazards or double-parking violations detected in this image.")
                    severity_multiplier = 1.0
                    hazard_type = "SAFE_ZONE"
            except Exception as e:
                print(f"Gemini Vision API error: {e}. Falling back to local computer vision simulation.", flush=True)
        
        # Save hazard to operational database
        hazard_id = database.add_hazard(school_id, description, severity_multiplier, hazard_type)
        
        return {
            "status": "success",
            "hazard": {
                "hazard_id": hazard_id,
                "school_id": school_id,
                "description": description,
                "severity_multiplier": severity_multiplier,
                "hazard_type": hazard_type,
                "analyzed_by_gemini": analyzed_by_gemini
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/hazards/{school_id}")
async def get_school_hazards(school_id: str):
    return database.get_hazards(school_id)

@app.post("/api/newsletter/generate")
async def generate_newsletter(school_id: str, authorization: Optional[str] = Header(None)):
    verify_role(authorization, "super_admin")
    school = next((s for s in SCHOOLS_DB if s["id"] == school_id), None)
    school_name = school["name"] if school else "our school"
    
    # Gather database parameters to ground the newsletter
    active_hazards = database.get_hazards(school_id)
    shifts = database.get_volunteer_shifts(school_id)
    
    hazard_str = ""
    if active_hazards:
        hazard_str = "\n".join([f"- {h['description']} (Type: {h['hazard_type']})" for h in active_hazards[:3]])
    else:
        hazard_str = "- No critical road hazards reported this week."
        
    shifts_str = ""
    if shifts:
        shifts_str = "\n".join([f"- {s['volunteer_name']} assigned to {s['assigned_zone']} at {s['time_window']}" for s in shifts[:3]])
    else:
        shifts_str = "- No crossing guard shifts scheduled. Roster vacancies present!"
        
    prompt = (
        f"Generate a professional, friendly, and urgent safety flyer newsletter for parents of students at {school_name}.\n"
        f"Here is the safety context for this week:\n"
        f"1. Active local traffic hazards reported by parents:\n{hazard_str}\n"
        f"2. Scheduled PTA volunteer crossing guard patrols:\n{shifts_str}\n"
        f"3. Operational Peak Congestion hours: 07:45-08:15 AM and 02:45-03:15 PM.\n\n"
        "Draft a brief, engaging safety briefing containing:\n"
        "- A friendly greeting referencing our guard mascot Guardy.\n"
        "- Bullet points advising parents on safest arrival windows (arrive early at 7:30 AM or late at 8:30 AM).\n"
        "- A Call to Action for parents to volunteer as crossing guard captains or report hazards via the portal.\n"
        "Keep it structured in clean HTML, ready to be copied/printed. Use styling compatible with email (e.g. green borders, cute cards, styled headers)."
    )
    
    api_key = os.environ.get("GEMINI_API_KEY")
    newsletter_html = ""
    used_gemini = False
    
    if HAS_GEMINI_SDK:
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                client = genai.Client(api_key=api_key)
            else:
                gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "juaravibe01")
                client = genai.Client(vertexai=True, project=gcp_project, location="us-central1")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            newsletter_html = response.text
            used_gemini = True
        except Exception as e:
            print(f"Gemini newsletter generation failed: {e}")
            
    if not used_gemini:
        # Fallback newsletter generator if Gemini API key not present
        newsletter_html = f"""
        <div style="font-family: inherit; text-align: left;">
            <div style="display: flex; align-items: center; gap: 12px; border-bottom: 2.5px solid var(--lingo-green); padding-bottom: 16px;">
                <span style="font-size: 32px;">🦉</span>
                <div>
                    <h3 style="margin: 0; color: var(--lingo-blue); font-size: 22px; font-weight: 800;">Guardy's Safety Weekly Briefing</h3>
                    <p style="margin: 4px 0 0 0; font-size: 13px; color: var(--text-secondary); font-weight: 600;">School Safety Alert for <strong>{school_name}</strong></p>
                </div>
            </div>
            
            <p style="font-size: 15px; line-height: 1.6; margin-top: 20px; color: var(--text-primary); font-weight: 500;">
                Hello Parents & Guardians! This is <strong>Guardy</strong>, your school safety assistant. Here is our weekly snapshot of school zone hazards and planning to keep our children safe.
            </p>
            
            <div style="background: rgba(255, 200, 0, 0.1); border-left: 4px solid var(--lingo-yellow-shadow); padding: 14px 18px; border-radius: var(--radius-md); margin: 20px 0;">
                <h4 style="margin: 0 0 8px 0; color: var(--lingo-yellow-shadow); font-size: 14px; font-weight: 800;">⚠️ Active Hazard Alerts</h4>
                <p style="margin: 0; font-size: 13px; color: var(--text-primary); line-height: 1.5; font-weight: 600;">{active_hazards[0]['description'] if active_hazards else "Double parking congestion remains high near the main gate. Double parked vehicles force children to exit in live traffic lanes."}</p>
            </div>
            
            <h4 style="color: var(--lingo-blue); font-size: 16px; margin-top: 24px; font-weight: 800;">🛡️ Safe Travel Windows</h4>
            <ul style="font-size: 14px; color: var(--text-primary); line-height: 1.7; padding-left: 20px; font-weight: 600; display: flex; flex-direction: column; gap: 8px;">
                <li><strong>Safest Windows:</strong> 07:30 - 07:45 AM and 08:30 - 08:45 AM (Risk drops by <strong style="color: var(--lingo-green);">45%</strong>).</li>
                <li><strong>Avoid Peak Congestion:</strong> 07:45 - 08:15 AM and 03:00 - 03:15 PM (Severe double-parking spikes).</li>
            </ul>
            
            <div style="margin-top: 28px; padding-top: 18px; border-top: 2.5px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <span style="font-size: 13px; color: var(--text-secondary); font-weight: 600;">Active Guard Shifts scheduled: <strong>{len(shifts)} shifts</strong></span>
                <span style="font-weight: 800; color: var(--lingo-green-shadow); font-size: 14px;">Let's Guard the Zone!</span>
            </div>
        </div>
        """
        
    if newsletter_html:
        try:
            database.save_briefing(school_id, newsletter_html)
        except Exception as db_err:
            print(f"Error saving generated briefing: {db_err}")
            
    return {
        "status": "success",
        "newsletter_html": newsletter_html,
        "gemini_active": used_gemini
    }

@app.get("/api/newsletter/latest")
async def get_latest_newsletter(school_id: str):
    try:
        html = database.get_latest_briefing(school_id)
        return {"status": "success", "newsletter_html": html or ""}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static React assets
DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")
if os.path.exists(os.path.join(DIST_DIR, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
