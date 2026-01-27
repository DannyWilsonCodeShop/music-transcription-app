#!/bin/bash

# Script to set up YouTube cookies for yt-dlp
# This allows bypassing YouTube's bot detection

echo "=== YouTube Cookies Setup for ChordScout ==="
echo ""

# Check for cookies file in multiple locations
COOKIES_FILE=""
if [ -f "public/cookies.txt" ]; then
    COOKIES_FILE="public/cookies.txt"
    echo "✓ Found cookies at public/cookies.txt"
elif [ -f "youtube-cookies.txt" ]; then
    COOKIES_FILE="youtube-cookies.txt"
    echo "✓ Found cookies at youtube-cookies.txt"
else
    echo "❌ Cookies file not found"
    echo ""
    echo "Please create one of these files:"
    echo "  - public/cookies.txt"
    echo "  - youtube-cookies.txt"
    echo ""
    echo "To export cookies from your browser:"
    echo "  1. Install 'Get cookies.txt LOCALLY' extension"
    echo "  2. Go to youtube.com (logged in)"
    echo "  3. Click extension icon and export"
    exit 1
fi

echo ""

# Upload to S3
echo "Uploading cookies to S3..."
aws s3 cp "$COOKIES_FILE" s3://chordscout-audio-dev-090130568474/config/youtube-cookies.txt \
    --region us-east-1 \
    --profile chordscout

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Cookies uploaded successfully!"
    echo ""
    echo "YouTube downloads should now work without bot detection."
    echo "The Lambda function will automatically use these cookies."
    echo ""
    echo "⚠️  SECURITY NOTE:"
    echo "  - These cookies give access to your YouTube account"
    echo "  - Only use this on your own AWS account"
    echo "  - Cookies expire after some time and will need to be refreshed"
    echo ""
    echo "To remove cookies from S3:"
    echo "  aws s3 rm s3://chordscout-audio-dev-090130568474/config/youtube-cookies.txt --region us-east-1 --profile chordscout"
else
    echo ""
    echo "❌ Failed to upload cookies to S3"
    echo "Make sure you have AWS credentials configured for the chordscout profile"
fi
