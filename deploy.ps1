# School-Zone Guardian - Google Cloud Run Deploy Automation Script

$PROJECT_ID = "juaravibe01"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/zoneguardian-app"
$SERVICE_NAME = "zoneguardian-app"

Write-Host "==============================================" -ForegroundColor Green
Write-Host "  School-Zone Guardian - Deploying to Cloud Run" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

# 1. Verify Active Project
Write-Host "[1/3] Configuring GCP Project target..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

# 2. Build Container using Cloud Build
Write-Host "[2/3] Submitting container build to Cloud Build..." -ForegroundColor Cyan
gcloud builds submit --tag $IMAGE_NAME

# 3. Deploy to Cloud Run
Write-Host "[3/3] Deploying image to Google Cloud Run (Serverless)..." -ForegroundColor Cyan
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID

Write-Host "==============================================" -ForegroundColor Green
Write-Host "  Deployment complete! Check the URL above." -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
