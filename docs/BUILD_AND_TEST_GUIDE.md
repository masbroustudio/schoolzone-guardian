# School-Zone Guardian - Build, Setup, & Test Guide

This document tracks the completed features, pending tasks, and step-by-step instructions for testing the **School-Zone Guardian** platform built for the Google Cloud Hackathon.

---

## 1. What Has Been Completed ✅

We have built a fully functional end-to-end Python FastAPI backend with a modern **React + Vite** front-end client, integrated with GCP BigQuery, Vertex AI Gemini clients, and local/PostgreSQL databases.

### 1.1 Backend Architecture ([main.py](file:///C:/dev/ZoneGuardian/main.py))
*   **FastAPI Web Server:** Configured routes serving the React build assets, static assets, and JSON API endpoints.
*   **API Routes:**
    *   `GET /api/schools`: Returns a dataset of school zone coordinates, baseline risk figures, and locations.
    *   `GET /api/risk/{school_id}`: Retrieves 15-minute window risk models.
    *   `POST /api/chat`: Coordinates chat history and prompts with Vertex AI Gemini using tool calling, featuring a robust rule-engine fallback.
    *   `POST /api/newsletter/generate`: Generates an AI-driven safety briefing incorporating hazard tables and rosters.
    *   `GET /api/newsletter/latest`: Retrieves the latest published weekly safety newsletter.
*   **BigQuery Live Fetching:** Implemented `fetch_bigquery_risk_slots()` which pulls real-time safety rows from the live GCP `safety_dataset.risk_forecast` table.
*   **Authorization Fix:** Resolved the Bearer token request validation layer to secure database writes and newsletter generations.

### 1.2 Frontend Architecture (Migrated to React + Vite)
*   **Modern Framework:** Migrated from static HTML/CSS files to a high-performance React + TypeScript single-page application powered by Vite.
*   **State Management & Routing:** Features cohesive client-side routing, typed component states, and session contexts in [App.tsx](file:///C:/dev/ZoneGuardian/frontend/src/App.tsx).
*   **Authentication & Auth Guard:** Secure local/mock OAuth authentication redirects with roles (`super_admin` vs. `public_user`) that guard private pages and API routes.
*   **Active Features & Tabs:**
    *   *Safety Dashboard:* School selector dropdown, real-time spatial GIS canvas mapping collision nodes, large tactile safety risk score gauges, and weather precipitation multipliers.
    *   *Guardian AI Chat:* Live interactive chat terminal with Gemini support, suggestion chips, message history, and loading states.
    *   *Admin Weekly Digest:* Volunteer crossing guard roster shift optimizer (database writes persist to SQLite/PostgreSQL) and PDF export triggers.
    *   *AI Safety Briefing (New Dedicated Page):* Dedicated publication page compiling the latest AI-generated PTA newsletters. Includes instant `📋 Copy HTML`, `🖨️ Print Briefing`, and admin `🔄 Regenerate (AI)` commands, backed by a clean compile loader.
    *   *Report Safety Hazard:* Multimodal Gemini Vision hazard uploader that updates database hazard indexes in real-time.
*   **Mobile-First Responsive Design:**
    *   *Collapsible Hamburger Sidebar:* Swaps the bulky side menu for a sliding drawer menu triggered via header button on mobile, complete with touch-overlay close triggers.
    *   *Fluid Portrait Scaling:* Media queries adapt logo headers, hide long GCP developer strings/emails on narrow viewports, and stack KPI card blocks to fit mobile screens.
*   **Aesthetic Theme Engine ([index.css](file:///C:/dev/ZoneGuardian/frontend/src/index.css)):** Duolingo-styled tactile buttons, rounded badges, and linear gradients. Automatically maps CSS variables to backend templates to provide unified Light/Dark mode styling for safety documents.

### 1.3 GCP BigQuery Integration
*   **GCP APIs Enabled:** Enabled BigQuery, BigQuery Data Transfer Service, Vertex AI, Cloud Run, and Artifact Registry on project `juaravibe01`.
*   **Table Schemas Provisioned ([setup_db.py](file:///C:/dev/ZoneGuardian/setup_db.py)):** Successfully created `safety_dataset` and tables (`schools`, `crashes_raw`, `weather_forecasts`, and `risk_forecast`) in project `juaravibe01`.
*   **Scheduled Query Script ([create_transfer_api.py](file:///C:/dev/ZoneGuardian/create_transfer_api.py)):** Configured python client script using BigQuery Data Transfer Client to schedule automated GIS joining queries.

### 1.4 Operational Database Layer ([database.py](file:///C:/dev/ZoneGuardian/database.py))
*   **Hybrid Client Router:** Configured SQLite (local `zoneguardian.db`) and PostgreSQL AlloyDB connectors.
*   **Auto Schema Definition:** Tables `users`, `volunteer_roster`, `school_hazards`, and `school_briefings` are automatically provisioned on launch.
*   **Wired APIs:** `/api/volunteers` POST and GET queries, hazard reports, and safety briefings read/write directly to the operational database.

### 1.5 Serverless Weather Ingestion ([ingest_function/](file:///C:/dev/ZoneGuardian/ingest_function))
*   **Cloud Function ([main.py](file:///C:/dev/ZoneGuardian/ingest_function/main.py)):** Implemented a complete Python Cloud Function to scrape hourly weather data from Open-Meteo and stream records directly into BigQuery tables.
*   **Package Manifest:** Documented dependencies in [requirements.txt](file:///C:/dev/ZoneGuardian/ingest_function/requirements.txt).

---

## 2. What Still Needs to be Done (Pending Tasks) ⏳

To prepare the final production release for the hackathon judges, complete these tasks:

### 2.1 Ingest Real-World Coordinates
*   **Task:** Populate the `schools` table with your actual pilot school locations, and load historical collision points into the `crashes_raw` table.
*   **Strategy:** You can run a SQL command inside your BigQuery Studio Console to load the public NYPD Motor Vehicle Collisions dataset:
    ```sql
    INSERT INTO `juaravibe01.safety_dataset.crashes_raw`
    SELECT unique_key, crash_date, crash_time, latitude, longitude, geometry, 
           number_of_persons_injured, number_of_pedestrians_injured, 
           number_of_cyclist_injured, contributing_factor_vehicle_1, vehicle_type_code1
    FROM `bigquery-public-data.new_york_mv_collisions.nypd_mv_collisions`
    WHERE crash_date >= '2025-01-01' AND latitude IS NOT NULL AND longitude IS NOT NULL;
    ```

### 2.2 Schedule the BigQuery Joins
*   **Task:** Deploy the SQL query in the BigQuery Web Console to run every 24 hours (or hourly) and populate the flat `risk_forecast` table.
*   **Strategy:** Copy the SQL script detailed in [ARCHITECTURE_AND_STRATEGY.md](file:///C:/dev/ZoneGuardian/docs/ARCHITECTURE_AND_STRATEGY.md) under Step 2 into your BigQuery Console, click **Schedule**, and save.

### 2.3 Connect Live Gemini (Vertex AI) API Keys
*   **Task:** Set up API access key env variables in your production environment so the Chat interface links to the live Gemini 2.5/3.5 models instead of falling back to rules engine simulation.
*   **Strategy:** Export the key locally:
    ```powershell
    $env:GEMINI_API_KEY="your-api-key"
    ```

---

## 3. Step-by-Step Testing Guide 🧪

The FastAPI server is running locally at **`http://localhost:8000`**. Follow these steps to verify all features:

### Test Case 1: Landing Page Timeline Demo
1.  Navigate to **`http://localhost:8000/`**.
2.  Scroll down to the **Pre-aggregate Spatial Hazards** segment.
3.  Drag the slider handle. Verify that:
    *   The circular score changes values and updates colors (Green at 7:00 AM, Red at 8:00 AM, Yellow at 8:30 AM).
    *   The "Primary Risk Drivers" text changes values (e.g. showing "Gridlock at school gate drop-off zone" during peak bell-times).
4.  Click the sun/moon icon in the top header. Verify that the entire page successfully switches to the dark Lingo theme.

### Test Case 2: Sign In Page
1.  Click the blue **Sign In** button in the header.
2.  Verify you see the Duolingo-styled input fields under a clean client route.
3.  Type in Super Admin credentials (`yudhae@gmail.com` and `Password!123`) or mock public credentials.
4.  Verify the button registers a tactile press and transitions you directly to the `/dashboard`.

### Test Case 3: Safety Dashboard & Weather Multiplier
1.  In the dashboard page, change the school selection dropdown to *Stuyvesant High School* or *Brooklyn Technical High School*.
2.  Verify the coordinates text and map visual markers update to reflect the selected school.
3.  Move the timeline slider and observe the risk progress dial.
4.  Check the **Current Weather** toggle to turn on **Rainy Weather**. Verify:
    *   The weather indicator text changes to `🌧️ Rainy`.
    *   All risk scores jump up by 40% (simulating real-time weather risk scales).
    *   Rain hazard factors (e.g. "Low visibility due to active precipitation") are appended to the risk drivers list.

### Test Case 4: Guardian AI Chat Terminal
1.  Click the **Guardian AI Chat** button in the left sidebar menu.
2.  Click the **🕒 Safest Drop-off Windows** chip.
3.  Verify:
    *   A user message bubble appears containing the prompt.
    *   A bot bubble appears showing a `Thinking...` state.
    *   The bot returns a structured markdown recommendation outlining high-risk alerts and safer alternatives.
4.  Type a manual message (e.g. *"What are the primary hazards?"*) and hit Enter. Verify the chatbot processes it and scrolls down.

### Test Case 5: Admin Digest & Roster Database CRUD
1.  Click **Admin Weekly Digest** in the left sidebar menu (only visible for Super Admin).
2.  Review the **Crossing Guard Shift Optimizer** table. Verify that risk zones show appropriate patrol configurations.
3.  Click the green **Add Volunteer Captain** button.
4.  Follow the prompts:
    *   **Prompt 1 (Name):** Enter `John Doe`.
    *   **Prompt 2 (Zone):** Enter `Crossing Zone A` (or keep default).
    *   **Prompt 3 (Shift):** Enter `07:45-08:00`.
5.  **Verify Database Write:** Check that a new card is successfully added to the roster. Refresh the webpage or switch schools and switch back; the roster card will persist because it is permanently saved in the local SQL database!
6.  **Verify Print Layout:** Click **Export PDF Safety Digest** to launch the browser's native print manager formatting the roster into a clean A4 report sheet.

### Test Case 6: Predictive Scenario Simulator
1.  On the **Safety Dashboard** tab, locate the **🎛️ Scenario Simulator** card.
2.  Adjust the **PTA Crossing Guards** slider from `0` to `2`. Verify:
    *   The safety risk circle score drops immediately due to active patrol coverage.
    *   The "Primary Risk Drivers" list appends a new item: *"Reduced by 2 active volunteer guards"*.
3.  Check the **Lane Closure Alert** toggle box. Verify the safety risk index increases by `20` points and lists a closure alert factor.
4.  Drag the **Parent Drop-off Compliance** slider. Verify the risk dials fluctuate dynamically based on compliance level.
5.  Click **Reset Parameters** to restore baseline scores.

### Test Case 7: Multimodal Hazard Photo Upload (Gemini Vision)
1.  Click **Report Safety Hazard** in the left sidebar menu.
2.  Click the drag-and-drop file upload zone and select an image file.
3.  **Test Case 7A (Hazard Detected):** Upload an image containing road traffic or double-parking. Verify that the results table displays the detected hazard type (e.g., `DOUBLE_PARKING`), severity modifier, and custom hazard description returned by Gemini.
4.  **Test Case 7B (No Hazard/Safe Scan):** Upload an image containing no traffic safety hazards (e.g., a photo of a cat). Verify:
    *   The result table displays `SAFE_ZONE` under Detected Hazard.
    *   The Risk Multiplier shows `1.0x` (no risk surcharge).
    *   The Description reads: `Safe zone. No traffic safety hazards or double-parking violations detected in this image.`
    *   The green success banner shows: `✔ Gemini Multimodal Vision analysis successful!`
5.  Click the green **Add Hazard to Safety Database** button.
6.  Verify:
    *   An alert dialog confirms the save.
    *   The hazard appears inside the **Active Safety Hazard Reports** list at the bottom of the page.
    *   Switch to the **Safety Dashboard** tab; the primary risk dial has now adapted to account for the new active hazard multiplier!

### Test Case 8: AI Safety Newsletter & Alert Briefing
1.  Click **AI Safety Briefing** in the left sidebar menu.
2.  Click the purple **✨ Generate PTA Safety Briefing (AI)** button (visible only for Super Admin if no briefing exists).
3.  Verify:
    *   A loading compiles spinner displays: *"Compiling Safety Publication... Guardian AI is synthesizing..."*
    *   A styled card renders the fully compiled Weekly Safety Briefing utilizing system theme colors.
4.  Click **Copy HTML** to copy the generated email template to the clipboard.
5.  Click **Print Briefing** to print the publication sheet.
6.  For Super Admins, click **Regenerate (AI)** to test rebuilding the document.
7.  Log in as a public user. Navigate to the **AI Safety Briefing** page and verify that the generated briefing is visible in read-only mode, without any edit or generation buttons.

---

## 4. GCP Production Deployment Guide 🚀

To transition the application from your local machine to the production Google Cloud Platform (`juaravibe01`), follow these instructions.

### 4.1 Deploy Web App to Cloud Run
Run the deployment automation script in your PowerShell terminal:
```powershell
./deploy.ps1
```
*This script uploads your code to Google Cloud Build, containerizes it via the [Dockerfile](file:///C:/dev/ZoneGuardian/Dockerfile), and deploys it to a secure, auto-scaling Cloud Run endpoint.*

### 4.2 Deploy Weather Ingestion Cloud Function
Run the Cloud Function deploy script:
```powershell
./deploy_function.ps1
```
*This deploys the python scraper inside the [ingest_function/](file:///C:/dev/ZoneGuardian/ingest_function) directory to run serverless weather ETL jobs.*

### 4.3 Configure AlloyDB PostgreSQL Cluster (OLTP)
1.  Go to **AlloyDB** in your Google Cloud Console.
2.  Click **Create Cluster** and set up a PostgreSQL cluster named `zoneguardian-db` with a database name `postgres` and password.
3.  Deploy a Serverless VPC Access connector to connect Cloud Run privately to AlloyDB.
4.  Update your Cloud Run service's environment variables using:
    ```powershell
    gcloud run services update zoneguardian-app --set-env-vars DB_HOST=YOUR_ALLOYDB_IP,DB_USER=postgres,DB_PASSWORD=YOUR_PASSWORD,DB_NAME=postgres --region us-central1
    ```
    *The app will automatically detect these variables and migrate from local SQLite to your production AlloyDB cluster!*

### 4.4 Set Up Vertex AI Service Account Roles
To authorize the live Gemini chatbot to run without needing API keys, give your Cloud Run Service Account Vertex AI user rights:
1.  Go to **IAM & Admin** in the GCP Console.
2.  Locate the Compute Engine / Cloud Run service account (e.g. `12345678-compute@developer.gserviceaccount.com`).
3.  Click **Edit** and add the role: **Vertex AI User** (`roles/aiplatform.user`).
4.  Gemini chatbot queries will now execute securely in production!
