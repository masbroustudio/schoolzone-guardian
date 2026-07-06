# School-Zone Guardian - Decision Intelligence Platform

An AI-powered Decision Intelligence Platform built for Google Cloud Hackathon. It predicts risky 15-minute school drop-off/pick-up windows and suggests safer routes, timings, and patrol rosters for parents and school administrators.

Aesthetic Theme: **Lingo** (Duolingo-inspired playful, tactile 3D elements)

---

## 📁 Repository Structure
```
ZoneGuardian/
├── docs/
│   ├── ARCHITECTURE_AND_STRATEGY.md  # Technical specifications and GCP plans
│   ├── BUILD_AND_TEST_GUIDE.md        # Guide for setting up and testing
│   └── NEXT_FEATURES_ANALYSIS.md     # Future enhancement roadmap matrix
├── frontend/                         # React TypeScript SPA codebase
│   ├── src/
│   │   ├── App.tsx                   # Single-page dashboard & interface
│   │   └── index.css                 # Custom Lingo styles and themes
│   └── package.json                  # Node.js dependencies and build tasks
├── main.py                           # FastAPI Backend, RAG pipeline & NLI router
├── database.py                       # Hybrid SQL database engine (SQLite/Postgres)
├── requirements.txt                  # Python dependencies manifest
├── setup_db.py                       # BigQuery dataset & schema creation script
├── .env.example                      # Template for local environment variables
└── README.md                         # This execution guide
```

---

## 🚀 Getting Started Locally

### 1. Prerequisites
Ensure you have Python 3.9+ and Node.js/npm installed on your machine.

### 2. Set Up Environment Variables
Copy `.env.example` to a new file named `.env` in the root directory:
```bash
cp .env.example .env
```
Open `.env` and set your local variables. The FastAPI backend will load these variables automatically at startup.

### 3. Install Dependencies & Build Frontend
Navigate to the `frontend` folder, install the packages, and compile the client build:
```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Set Up Virtual Environment & Python dependencies
Initialize a virtual environment in the root directory and install dependencies:
```powershell
# Create environment
python -m venv venv

# Activate environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 5. Run the Application
Start the FastAPI server:
```powershell
python main.py
```
The server will start at **`http://127.0.0.1:8000`**. Open this URL in your web browser.
* **Landing Page:** `http://127.0.0.1:8000/`
* **Login/Register Page:** `http://127.0.0.1:8000/login`
* **Parent & Admin Dashboard:** `http://127.0.0.1:8000/` (Serves unified React single page app)

---

## ✨ Completed Implementations (Tier 1 Features)

We have fully implemented and deployed the following core decision intelligence systems:

### 1. RAG-Powered Context Retrieval
* **Context Augmentation:** Before queries reach the model, the backend retrieves real-time weather forecasts, parent-reported physical hazards, volunteer patrols, and baseline safety records.
* **Prompt Grounding:** Incorporates structured document citations (`[DOC 1]`, `[DOC 2]`) to provide zero-hallucination, verified safety advice.
* **RAG Grounding Badge:** Displays an active **`✅ RAG-Grounded`** indicator beneath responses to show that answers are verified against physical school databases.

### 2. Explainable AI (XAI) Risk Factor Decomposition
* **Risk Score Breakdown:** Exposes the exact math behind every 15-minute risk score (Historical crash density, peak bell-time traffic, precipitation forecasts, active hazards, and parent compliance index).
* **Interactive Panel:** Visualizes these contributions dynamically as progress bars on the temporal timeline.
* **Responsible AI Policy:** Hardcodes strict policy guidelines preventing the use of demographic, income, or policing inputs, focusing purely on physical road safety.

### 3. Conversational NLI Analytics Tools
* **NLI Analytic Tools:** Registered custom tools for automated query handling:
  * `compare_schools_tool` — Ranks and compares risk levels across all school zones.
  * `analyze_trends_tool` — Compares AM/PM hazards and outlines day-of-week risk distributions.
  * `volunteer_gaps_tool` — Cross-references guard shifts with high-risk windows to recommend safety coverage.
* **Analytics Suggestion Chips:** Added quick-action chip buttons in the chat interface to trigger advanced queries instantly.

---

## 🏆 Hackathon Strategic Pillars

1. **High Viability & Portability:** Uses NYC Open Data (NYPD vehicle collisions) and public weather feeds which are portable to any city in 48 hours.
2. **Cost-Effective Scalability:** Offloads spatial processing to pre-computed scheduled queries in BigQuery and caches JSON payloads in memory (Redis), allowing serverless execution for under $50/month.
3. **Zero-Hallucination Grounded AI:** Limits Vertex AI Gemini agent queries to database function calls, ensuring safe and Demographics-blind safety indices.

