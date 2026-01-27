#!/bin/bash

# Deploy YouTube Downloader Function
echo "🎵 Deploying YouTube Downloader Function..."

# Create zip file
cd backend/functions
zip -r youtube-downloader.zip youtube-downloader-fixed.py

# Update Lambda function
aws lambda update-function-code \
    --function-name chordscout-youtube-downloader-dev \
    --zip-file fileb://youtube-downloader.zip

echo "✅ YouTube Downloader function updated successfully!"