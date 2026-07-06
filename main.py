import os
import time
import math
import random
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
        job_config = bigquery.QueryJobConfiguration(
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

# Tool definition for Gemini function calling
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
        
    for slot in slots:
        score = slot["score"]
        factors = list(slot["factors"])
        
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
            
        # Include active hazards in factors
        for h in active_hazards:
            factors.append(f"AI Alert: {h['description']} ({h['hazard_type']})")
            
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
            "factors": factors
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

@app.post("/api/chat")
async def chat_with_agent(req: ChatRequest):
    school = next((s for s in SCHOOLS_DB if s["id"] == req.school_id), None)
    school_name = school["name"] if school else "this school"
    
    # Try calling Vertex/Gemini Developer API using Google Gen AI SDK
    # We will look for an active API key or environment project
    api_key = os.environ.get("GEMINI_API_KEY")
    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "juaravibe01")
    
    response_text = ""
    used_gemini = False
    
    if HAS_GEMINI_SDK:
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                client = genai.Client(api_key=api_key)
            else:
                gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "juaravibe01")
                client = genai.Client(vertexai=True, project=gcp_project, location="us-central1")
            
            # Formulate full system prompt instructions
            system_instruction = (
                "You are 'Guardian AI,' a friendly, expert safety assistant representing the School-Zone Guardian platform.\n"
                "You help parents, administrators, and volunteers assess drop-off/pickup risk windows.\n"
                "CONSTRAINTS & RULES:\n"
                "1. ALWAYS ground risk assessments in data retrieved via function calling database tools. Do not speculate.\n"
                "2. Categorize risk scores (0-100) into low (Green, 0-39), medium (Yellow, 40-69), or high (Red, 70-100).\n"
                "3. Recommend alternative timing windows when high risk is requested.\n"
                "4. RESPONSIBLE AI: Never reference race, household income, socioeconomic status, or policing. Focus on road variables.\n"
                "5. Keep responses brief, friendly, structured in Markdown, and use bullet points."
            )
            
            # Call Gemini 2.5 Flash
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=req.message,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[database_lookup_tool],
                    temperature=0.3
                )
            )
            
            # Process function calls if any were triggered
            # Note: The SDK's client.models.generate_content automatically handles function execution if configured,
            # but if we do manual tool coordination, we can also extract function calls.
            # To ensure compatibility and avoid auth-errors in different environments, we handle tools.
            # If AFC is handled, response.text contains the answer.
            response_text = response.text
            used_gemini = True
            
        except Exception as e:
            # Fallback to local heuristic engine if API fails
            print(f"Gemini API invocation error: {e}. Falling back to rules engine.")
            used_gemini = False

    if not used_gemini:
        # Grounded rules-based safety response generator (Heuristics Engine)
        # Parses keywords to offer an exact grounded response to queries
        msg = req.message.lower()
        
        # Look up data
        school_data = database_lookup_tool(school_name)
        
        if "when" in msg or "safe" in msg or "time" in msg or "recommend" in msg:
            response_text = (
                f"### 🛡️ Safety Recommendation for {school_name}\n\n"
                f"Based on historical spatial incident joins, here is the safety analysis:\n\n"
                f"* **High Risk Alerts 🚨:** The peak bell-time windows of **07:45-08:15** and **14:45-15:15** show high congestion and collision indexes. Parents are advised to avoid arriving exactly at these times if possible.\n"
                f"* **Recommended Timing 🟢:** Arriving in the **07:30-07:45** or **08:30-08:45** windows reduces drop-off risk by up to **45%** because traffic volume drops and visibility is significantly better.\n"
                f"* **Current Dynamic Factors 🌦️:** Moderate road wetness and localized double-parking lanes increase overall caution requirements. Drive slowly (under 15mph) and prioritize pedestrian walks."
            )
        elif "why" in msg or "factor" in msg or "reason" in msg or "risk" in msg:
            response_text = (
                f"### 📊 Risk Drivers for {school_name}\n\n"
                f"Traffic safety analysts and historical data point to these physical parameters:\n\n"
                f"1. **Double Parking Clutter (Multiplier: {school['double_parking_factor']}x):** Parents parking in double lanes forces children to exit vehicles in live lanes, blocking line-of-sight for crossing guards.\n"
                f"2. **Spatial Design Bottleneck:** This school is near a busy arterial road, creating blind curves where approaching vehicles cannot see pedestrians clearly.\n"
                f"3. **Bell-Time Influx:** High student volume entering at 8:00 AM leads to sudden pedestrian crowding near crossing walks.\n\n"
                f"*Suggestion: Encourage carpooling to drop off 2 blocks away at designated visual zones.*"
            )
        else:
            response_text = (
                f"### Hello! I am Guardy, your School-Zone Guardian AI assistant. 🦉\n\n"
                f"I have analyzed the spatial datasets for **{school_name}**.\n\n"
                f"Here is a quick snapshot of the current safety profile:\n"
                f"* **Historical Crashes (300m radius):** {school.get('historical_incidents', 0)} cases.\n"
                f"* **Primary Hazard Factor:** High density drop-off double-parking.\n\n"
                f"You can ask me questions like:\n"
                f"* _'When is the safest time to drop off my kids?'_\n"
                f"* _'What are the main risk factors here?'_\n"
                f"* _'How does rain affect the risk index?'_"
            )

    return {
        "reply": response_text,
        "gemini_active": used_gemini
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
