# School-Zone Guardian - Cloud Function Ingestion Deploy Script

$PROJECT_ID = "juaravibe01"
$REGION = "us-central1"
$FUNCTION_NAME = "ingest_weather_forecast"

Write-Host "==============================================" -ForegroundColor Green
Write-Host "  Deploying Weather Ingestion Cloud Function  " -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

# 1. Verify Active Project
Write-Host "[1/2] Setting target GCP Project..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

# 2. Deploy Cloud Function
Write-Host "[2/2] Deploying HTTP triggered Python function..." -ForegroundColor Cyan
# Navigate to ingest_function subdirectory to deploy
gcloud functions deploy $FUNCTION_NAME `
    --runtime python310 `
    --trigger-http `
    --allow-unauthenticated `
    --region $REGION `
    --source ./ingest_function `
    --entry-point ingest_weather_forecast

Write-Host "==============================================" -ForegroundColor Green
Write-Host "  Cloud Function deployed successfully!       " -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
