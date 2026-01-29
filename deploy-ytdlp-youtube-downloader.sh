#!/bin/bash

# Deploy YouTube Downloader with yt-dlp
# This script packages and deploys the yt-dlp version of the YouTube downloader

set -e

echo "🚀 Deploying YouTube Downloader with yt-dlp..."

FUNCTION_NAME="chordscout-v2-youtube-downloader-dev"
REGION="us-east-1"
PROFILE="chordscout"

# Navigate to function directory
cd backend/functions-v2/youtube-downloader

echo "📦 Installing dependencies..."
pip3 install -r requirements.txt -t . --upgrade

echo "📦 Creating deployment package..."
zip -r function.zip . -x "*.pyc" -x "__pycache__/*" -x "*.dist-info/*" -x "*.egg-info/*"

echo "☁️  Uploading to Lambda..."
aws lambda update-function-code \
  --function-name $FUNCTION_NAME \
  --zip-file fileb://function.zip \
  --region $REGION \
  --profile $PROFILE

echo "⏳ Waiting for function to update..."
aws lambda wait function-updated \
  --function-name $FUNCTION_NAME \
  --region $REGION \
  --profile $PROFILE

echo "✅ Deployment complete!"
echo ""
echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""
echo "🧪 Test with:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"jobId\":\"test-123\",\"youtubeUrl\":\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}' response.json --profile $PROFILE --region $REGION"
