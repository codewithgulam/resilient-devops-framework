#!/bin/bash

set -e

echo "=== Starting deployment ==="

cd "$HOME/resilient-devops-framework"

echo "Pulling latest source..."
git pull origin master

echo "Building application image..."
docker build -t resilient-app:latest .

echo "Stopping current deployment..."
docker stop resilient-container-v1 2>/dev/null || true
docker rm resilient-container-v1 2>/dev/null || true

echo "Stopping previous deployment container..."
docker stop resilient-container-v2 2>/dev/null || true
docker rm resilient-container-v2 2>/dev/null || true

echo "Starting new deployment..."
docker run -d \
  --name resilient-container-v2 \
  -p 8000:8000 \
  resilient-app:latest

echo "Waiting for application..."
sleep 10

echo "Running health check..."
curl --fail --silent http://localhost:8000/health/ > /dev/null

echo "================================"
echo "Deployment successful"
echo "Health check passed"
echo "================================"
