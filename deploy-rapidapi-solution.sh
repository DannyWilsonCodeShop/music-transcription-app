#!/bin/bash

echo "=== Deploying RapidAPI YouTube Solution ==="
echo ""

# Check if RapidAPI key is provided
if [ -z "$RAPIDAPI_KEY" ]; then
    echo "❌ RAPIDAPI_KEY environment variable not set"
    echo ""
    echo "Please set your RapidAPI key:"
    echo "  export RAPIDAPI_KEY='your-rapidapi-key-here'"
    echo ""
    echo "Get your key from: https://rapidapi.com/"
    exit 1
fi

echo "✓ RapidAPI key found"

# Create deployment package
echo "Creating deployment package..."
mkdir -p temp-deploy
cp backend/lambda-functions/youtube-downloader-rapidapi.py temp-deploy/index.py

# Create requirements.txt
cat > temp-deploy/requirements.txt << EOF
requests==2.31.0
boto3==1.34.0
EOF

# Install dependencies
cd temp-deploy
pip install -r requirements.txt -t .

# Create deployment zip
zip -r ../youtube-downloader-rapidapi.zip . -x "*.pyc" "__pycache__/*"
cd ..

# Update Lambda function
echo "Updating Lambda function..."
aws lambda update-function-code \
    --function-name chordscout-youtube-downloader-dev \
    --zip-file fileb://youtube-downloader-rapidapi.zip \
    --region us-east-1

# Update environment variables
echo "Setting environment variables..."
aws lambda update-function-configuration \
    --function-name chordscout-youtube-downloader-dev \
    --environment Variables="{
        BUCKET_NAME=chordscout-audio-dev-090130568474,
        RAPIDAPI_KEY=$RAPIDAPI_KEY,
        ENVIRONMENT=dev
    }" \
    --region us-east-1

# Clean up
rm -rf temp-deploy
rm youtube-downloader-rapidapi.zip

echo ""
echo "✅ RapidAPI solution deployed successfully!"
echo ""
echo "Next steps:"
echo "1. Sign up for RapidAPI: https://rapidapi.com/"
echo "2. Subscribe to a YouTube API service"
echo "3. Test with a YouTube video"
echo ""
echo "Recommended APIs:"
echo "- YouTube MP3 Downloader: https://rapidapi.com/ytjar/api/youtube-mp36"
echo "- YouTube to MP3: https://rapidapi.com/api/youtube-to-mp315"
echo ""