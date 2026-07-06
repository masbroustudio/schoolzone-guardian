# School-Zone Guardian - Decision Intelligence Platform

An AI-powered Decision Intelligence Platform built for Google Cloud Hackathon. It predicts risky 15-minute school drop-off/pick-up windows and suggests safer routes, timings, and patrol rosters for parents and school administrators.

GCP Project ID: `project_name`
Aesthetic Theme: **Lingo** (Duolingo-inspired playful, tactile 3D elements)

---

## 📁 Repository Structure
```
ZoneGuardian/
├── docs/
│   └── ARCHITECTURE_AND_STRATEGY.md  # Data tables, Agent specs, GCP plans
├── static/
│   ├── css/
│   │   └── style.css                 # Lingo styling, dark mode, animations
│   ├── index.html                    # Interactive Landing Page
│   ├── login.html                    # Tactile Login/Register Card
│   └── dashboard.html                # Main Map, timeline slider, AI Chat, and Admin Planner
├── main.py                           # FastAPI Backend and conversational routing
├── requirements.txt                  # Python dependencies manifest
├── setup_db.py                       # BigQuery dataset & schema creation script
└── README.md                         # This execution guide
```

---

## 🚀 Getting Started Locally

### 1. Prerequisites
Ensure you have Python 3.9+ installed on your machine.

### 2. Set Up Virtual Environment & Dependencies
Initialize a virtual environment in the project directory and install requirements:

```powershell
# Create environment
python -m venv venv

# Activate environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 3. Run the Application
Start the FastAPI server:

```powershell
python main.py
```

The server will start at **`http://127.0.0.1:8000`**. Open this URL in your web browser.
* **Landing Page:** `http://127.0.0.1:8000/`
* **Login/Register Page:** `http://127.0.0.1:8000/login`
* **Parent & Admin Dashboard:** `http://127.0.0.1:8000/dashboard`

---

## ☁️ Google Cloud Platform Integration (`project_name`)

To configure GCP services, follow the guides below.

### 1. Authenticate GCP Credentials
In your terminal, configure your active project:

```powershell
# Set project
gcloud config set project project_name

# Authorize application default credentials
gcloud auth application-default login
```

### 2. Provision BigQuery Tables
Run the schema setup script to automatically create the tables in your project:

```powershell
python setup_db.py
```

This provisions `schools`, `crashes_raw`, `weather_forecasts`, and `risk_forecast` tables inside a BigQuery dataset named `safety_dataset`.

### 3. Configure Gemini AI Agent
If you want to run live Gemini AI calls in the Chat tab, export your API Key or authenticate through Application Default Credentials (ADC):

```powershell
# Option A: Export Gemini API Key
$env:GEMINI_API_KEY="your_api_key_here"

# Option B: Run gcloud application credentials
$env:GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
```

If no keys are found, the chat module automatically falls back to a high-fidelity Rule Heuristics Engine that mimics Guardy's responses using school parameters.

---

## 🏆 Hackathon Strategic Pillars

1. **High Viability & Portability:** Uses NYC Open Data (NYPD vehicle collisions) and public weather feeds which are portable to any city in 48 hours.
2. **Cost-Effective Scalability:** Offloads spatial processing to pre-computed scheduled queries in BigQuery and caches JSON payloads in memory (Redis), allowing serverless execution for under $50/month.
3. **Zero-Hallucination Grounded AI:** Limits Vertex AI Gemini agent queries to database function calls, ensuring safe and Demographics-blind safety indices.
