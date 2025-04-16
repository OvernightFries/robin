# Deployment script for Google Cloud Run
param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$true)]
    [string]$AlpacaApiKey,
    
    [Parameter(Mandatory=$true)]
    [string]$AlpacaSecretKey,
    
    [Parameter(Mandatory=$true)]
    [string]$PineconeApiKey,
    
    [Parameter(Mandatory=$true)]
    [string]$PineconeEnvironment,
    
    [string]$AlpacaBaseUrl = "https://paper-api.alpaca.markets/v2",
    [string]$PineconeIndexName = "robindocs",
    [string]$PineconeRealtimeIndex = "real-time-vectorization",
    [string]$CorsOrigin = "*",
    [string]$Region = "us-central1"
)

# Check if gcloud is installed
try {
    $gcloudVersion = gcloud version
    Write-Host "✅ Google Cloud SDK is installed"
} catch {
    Write-Host "❌ Google Cloud SDK is not installed. Please install it from: https://cloud.google.com/sdk/docs/install-sdk"
    exit 1
}

# Check if Docker is installed
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker is installed"
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
}

# Set the project
Write-Host "Setting project to $ProjectId..."
gcloud config set project $ProjectId

# Configure Docker to use gcloud as a credential helper
Write-Host "Configuring Docker credentials..."
gcloud auth configure-docker

# Build the container image
$imageName = "gcr.io/$ProjectId/robin-backend"
Write-Host "Building container image: $imageName"
docker build -t $imageName .

# Push the image to Google Container Registry
Write-Host "Pushing container image to Google Container Registry..."
docker push $imageName

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..."
$envVars = @(
    "ALPACA_API_KEY=$AlpacaApiKey",
    "ALPACA_SECRET_KEY=$AlpacaSecretKey",
    "ALPACA_BASE_URL=$AlpacaBaseUrl",
    "PINECONE_API_KEY=$PineconeApiKey",
    "PINECONE_ENVIRONMENT=$PineconeEnvironment",
    "PINECONE_INDEX_NAME=$PineconeIndexName",
    "PINECONE_REALTIME_INDEX=$PineconeRealtimeIndex",
    "CORS_ORIGIN=$CorsOrigin"
) -join ","

gcloud run deploy robin-backend `
    --image $imageName `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --set-env-vars=$envVars

Write-Host "✅ Deployment completed!" 
