# Build the Docker image
docker build -t gcr.io/robinai/robin ./backend

# Push to Google Container Registry
docker push gcr.io/robinai/robin

# Deploy to Cloud Run
gcloud run deploy robin \
  --image gcr.io/robinai/robin \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --ingress all