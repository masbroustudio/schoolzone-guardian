# MASTERPLAN.md: School-Zone Guardian - Decision Intelligence Platform

---

## 1. Executive Summary & Hackathon Proposal

### One-Liner
An AI-powered Decision Intelligence Platform that predicts risky 15-minute school drop-off/pick-up windows and suggests safer routes, timing, and operational setups for parents and school administrators.

### Problem Statement & Root Causes
1. **Drop-Off Peak-Time Chaos:** Traffic surges around school bell times create high-stress environments characterized by double-parking, illegal U-turns, and poor pedestrian visibility, leading to frequent near-misses.
2. **Stale and Coarse Safety Data:** Traditional municipal crash statistics are published monthly or quarterly. They lack integration with dynamic, daily contextual factors like live weather, active roadwork, or temporal events.
3. **One-Size-Fits-All Advice:** Traditional safety messaging relies on static, generic tips (e.g., "arrive early") that completely ignore school-specific layouts, local congestion patterns, and historical micro-windows.
4. **Limited Administrative Capacity:** School principals and PTA volunteers lack the technical resources to continuously aggregate spatial-temporal datasets to optimize crossing guard shifts or traffic signage.

### Proposed Solution & Core Features
* **Micro-Window Risk Scoring:** Computes an dynamic risk index (0 to 100) for every school zone in 15-minute intervals across operational hours.
* **Grounded AI Conversational Agent ("Guardian AI"):** A natural language interface that allows parents to ask questions about specific timeslots and receive real-time, evidence-based recommendations.
* **Weekly Admin Digest Dashboard:** A planning view for school administrators that highlights the week’s worst 30-minute risk spikes, maps local incidents, and recommends precise volunteer or crossing guard shifts.

### Target Audience & Customer Segments
* **Primary Users:** Commuting parents/guardians, school principals, and PTA/parent councils.
* **Secondary Stakeholders:** Municipal traffic safety planners, school district coordinators, and crossing guard deployment agencies.

### Key Metrics for Success
* **Risk Calibration:** Ensure over 75% of actual traffic incidents or flagged near-misses occur within predicted medium-to-high risk temporal windows.
* **Parent Engagement:** Achieve a daily-active-user rate of over 30% among parents in pilot school zones.
* **Operational Action:** Measure the number of administrative safety shifts (e.g., volunteer positioning, cones deployed) adjusted based on the platform's weekly digest recommendations.

---

## 2. Production-Grade Cloud Architecture Blueprint

This architecture is optimized for high-concurrency read peaks (e.g., 7:30 AM–8:15 AM) and ensures highly responsive, low-latency AI reasoning.

```
                      [ Cloud Scheduler ]
                               │ (30-Min / Daily Triggers)
                               ▼
                      [ Cloud Run Jobs ] (Lightweight Python ETL)
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
     [ Open-Meteo API ]  [ BQ Public Data ] [ Waze Alerts Feed ]
            └──────────────────┬──────────────────┘
                               ▼
                   [ Google Cloud BigQuery ]
        ┌──────────────────────┴──────────────────────┐
        ▼ (Raw Data Tables)                           ▼ (Scheduled Query Pipeline)
   [schools, crashes_raw, weather]              [risk_forecast (Flat & Indexed Table)]
                                                      │
                                                      ▼
                                           [ Cloud Run (FastAPI API) ] ◄──► [ Cloud Memorystore ]
                                                      │                       (Redis Caching Layer)
                                                      ▼
                                         [ Vertex AI Agent Builder ]
                                         - Model: gemini-2.5-flash
                                         - Automatic Function Calling (AFC)
                                                      │
                                                      ▼
                                           [ Front-End Dashboard ]
                                           (Streamlit / Looker Studio)
```

### Technical Component Breakdown
1. **Ingestion Layer (Cloud Run Jobs & Cloud Scheduler):** Executes cron-triggered micro-batch processes to pull current weather forecasts, active road closures, and localized hazard feeds.
2. **Data Warehouse & Spatial Engine (Google Cloud BigQuery):** Stores spatial representations of school zones and processes historical collision trends alongside real-time parameters.
3. **Application & AI Layer (Cloud Run - FastAPI):** Exposes REST endpoints, communicates with the Gemini model, and coordinates database operations.
4. **Caching Layer (Cloud Memorystore for Redis):** Stores hot-cache JSON payloads for individual school risk summaries to minimize redundant database lookups.
5. **AI Reasoning Engine (Vertex AI - Gemini 2.5 Flash):** Utilizes tool-calling configurations to convert structured SQL query payloads into natural, actionable advice.

### Resolving Hidden Technical Bottlenecks

#### BigQuery GIS Join Limitations on Materialized Views
* *The Bottleneck:* BigQuery does not permit complex spatial-join functions (such as spatial distance measurements or radius buffer checks) inside real-time Materialized Views [1]. Executing raw geographic joins on every API request causes excessive latency and high query costs.
* *The Solution:* Implement a scheduled, pre-aggregated database flat table. Use BigQuery Scheduled Queries to compute school-to-incident spatial relationships on a fixed schedule (e.g., every 30 minutes). The FastAPI service queries this pre-computed, non-spatial index, reducing API response times to less than 100 milliseconds.

#### Concurrency and Query Cost Management
* *The Bottleneck:* Thousands of parents checking the app simultaneously during the peak 7:30 AM window would trigger thousands of duplicate queries to BigQuery, exponentially increasing query scan costs.
* *The Solution:* Implement a Redis caching strategy inside the API. Store calculated school risk evaluations with a 10-minute expiration limit. If multiple requests target the same school, serve the payload directly from Redis memory.

#### Managing API Cold Starts on Serverless Container Apps
* *The Bottleneck:* Cloud Run downscales instances to zero when idle to save costs, creating a startup latency delay (5 to 10 seconds) for the first user query of the morning.
* *The Solution:* Configure the Cloud Run API with a minimum instance configuration during operational school hours (Monday to Friday, 6:30 AM to 4:30 PM). Use Cloud Scheduler to send a keep-alive request every 5 minutes during these windows.

#### Responsible AI and Safety Guardrails
* *The Bottleneck:* AI models can hallucinate coordinates or offer biased, subjective safety descriptions based on neighborhood demographics.
* *The Solution:* Define strict system boundaries. Program the AI model to *only* evaluate risk using specific, physical variables: physical road closures, historical crash geometries, active precipitation, and light levels. Restrict the model from accessing or referencing any socioeconomic, census, or policing demographic data.

---

## 3. Real-World Data Strategy (Using BigQuery Public Datasets)

To eliminate the need for synthetic data while maintaining spatial-temporal accuracy, the platform leverages real-world, high-volume municipal datasets natively hosted on Google Cloud [1].

### Primary Dataset: NYC Motor Vehicle Collisions
* **Location in GCP:** BigQuery Public Datasets (`bigquery-public-data.new_york_mv_collisions.nypd_mv_collisions`).
* **Attributes Utilized:** Collision date and time, precise latitude/longitude, total injuries, contributing factors, and vehicle type.

### School Reference Data
* **Location in GCP:** BigQuery US Census Public Datasets, or custom geographic coordinates for key school facilities mapped inside New York City.

### Spatial Joining Workflow
1. Convert latitude and longitude decimal values from the public collision database into native geographic point shapes.
2. Define static school zones by creating spatial boundaries (e.g., a 300-meter circular zone around the school's central coordinate).
3. Query and join the datasets by finding collision coordinates that fall geographically within the designated school boundary zones.
4. Filter historical records to focus on specific drop-off and pick-up hour intervals, matching them by day of the week to establish a localized temporal risk baseline.

---

## 4. Antigravity CLI (`agy`) Execution Roadmap

The following plan is designed for an autonomous development agent running on the Antigravity CLI (`agy`) with VS Code. The agent will read this masterplan, understand the boundaries, and generate the target codebase.

### Phase 1: Virtual Environment and Agent Guardrails
*   **Target:** Setup the runtime workspace and instruct the agent to align with modern Google Cloud SDK styles.
*   **Agent Instructions:**
    *   Initialize a Python virtual environment and isolate the runtime.
    *   Create a dependency manifest installing FastAPI, Uvicorn, the official Google Gen AI Client SDK, the Google Cloud BigQuery client, and Redis client libraries.
    *   Create a workspace policy file forcing the use of modern Python typing, strict exception-handling blocks, and asynchronous FastAPI path operations.

### Phase 2: Database Schemas & Data Pipeline Execution
*   **Target:** Establish the schema structure and deploy the scheduled geospatial data pipelines.
*   **Agent Instructions:**
    *   Write a script to define the tables in BigQuery for school facilities (using geographic geometry formats) and live weather forecasts.
    *   Draft a data-loading routine that populates the school coordinates table with a defined list of real NYC high schools.
    *   Build a pipeline script that executes a scheduled query in BigQuery. The query must join the local school zones with the NYC public collision dataset, calculating a 0-100 normalized risk score based on collision density, weather forecasts, and light levels, then outputting to a flat database table.

### Phase 3: Core API Design & AI Model Tool Integration
*   **Target:** Build the FastAPI engine and configure the Gemini 2.5 Flash agent with native tool execution.
*   **Agent Instructions:**
    *   Develop a backend API exposing paths for parent conversational prompts and weekly administrator digests.
    *   Implement a Python helper function that executes a parameterized SQL lookup on the flat risk forecast table in BigQuery. Ensure this function has a descriptive docstring defining its purpose, inputs, and outputs.
    *   Initialize the Gemini client using the modern, unified `google-genai` SDK.
    *   Configure the AI Chat interface with Gemini 2.5 Flash, feeding the risk lookup helper function directly into the model's tool configuration list to enable Automatic Function Calling (AFC).
    *   Draft system instructions that mandate the AI must use the database tool when responding to school inquiries, categorize the raw numbers into clear color-coded risk tiers, and provide an actionable timing alternative.

### Phase 4: Cache Optimization & Frontend Layer
*   **Target:** Build the user interface and secure database query costs.
*   **Agent Instructions:**
    *   Integrate a Redis caching check directly inside the database lookup tool to prevent duplicate calls for identical schools within a 10-minute window.
    *   Construct a clean, single-page web dashboard using Streamlit.
    *   Incorporate a geographic map display showing school safety flags.
    *   Implement an interactive chat window that routes questions to the backend API, rendering the formatted markdown safety output dynamically.

---

## 5. Strategic Pitch & Winning Criteria

To capture the interest of both municipal stakeholders and cloud engineering judges, align your presentation around three core architectural pillars:

### Pillar 1: High Viability and Portability
*   **Key Message:** The platform does not rely on expensive proprietary sensors or custom hardware.
*   **Supporting Evidence:** By using open-source web frameworks, public weather feeds, and standardized municipal open data structures (like NYPD collision feeds), the platform is highly portable and can be deployed in any metropolitan area globally within 48 hours.

### Pillar 2: Cost-Effective Enterprise Performance
*   **Key Message:** This system is built to scale to thousands of daily users on a minimal serverless budget.
*   **Supporting Evidence:** High-cost geographic computation is handled ahead of time via scheduled queries, and hot data is stored in memory via Redis. As a result, the active runtime operates within minimal compute resource envelopes, keeping pilot operation costs under $50 per month.

### Pillar 3: Zero-Hallucination Grounded AI
*   **Key Message:** Parents and administrators can make critical safety decisions with complete trust in the AI's recommendations.
*   **Supporting Evidence:** Through Automatic Function Calling on Gemini 2.5 Flash, the conversational agent is strictly bound to factual database schemas. It does not speculate or hallucinate hazard patterns; if data is missing, the agent clearly states the limitation, ensuring a reliable, transparent, and explainable decision system.