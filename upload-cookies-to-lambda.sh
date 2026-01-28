#!/bin/bash

# Upload YouTube cookies to S3 for Lambda function use
# This script uploads cookies to the correct S3 bucket for the ChordScout V2 backend

set -e

echo "🍪 Uploading YouTube Cookies to S3"
echo "=================================="

# Configuration
COOKIES_FILE="public/cookies.txt"
S3_BUCKET="chordscout-audio-temp-dev-090130568474"
S3_KEY="cookies/youtube-cookies.txt"
LAMBDA_FUNCTION="chordscout-v2-youtube-downloader-dev"
AWS_REGION="us-east-1"

# Check if cookies file exists
if [ ! -f "$COOKIES_FILE" ]; then
    echo "❌ Error: Cookies file not found at $COOKIES_FILE"
    exit 1
fi

echo "📁 Cookies file: $COOKIES_FILE"
echo "🪣 S3 Bucket: $S3_BUCKET"
echo "🔑 S3 Key: $S3_KEY"
echo ""

# Upload to S3
echo "⬆️  Uploading cookies to S3..."
aws s3 cp "$COOKIES_FILE" "s3://$S3_BUCKET/$S3_KEY" \
    --region "$AWS_REGION" \
    --profile chordscout 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Cookies uploaded successfully!"
else
    echo "❌ Failed to upload cookies"
    exit 1
fi

echo ""
echo "🔧 Updating Lambda function environment variables..."

# Update Lambda environment variables
aws lambda update-function-configuration \
    --function-name "$LAMBDA_FUNCTION" \
    --environment "Variables={
        S3_AUDIO_BUCKET=$S3_BUCKET,
        DYNAMODB_JOBS_TABLE=ChordScout-Jobs-V2-dev,
        COOKIES_BUCKET=$S3_BUCKET,
        COOKIES_KEY=$S3_KEY
    }" \
    --region "$AWS_REGION" \
    --profile chordscout > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Lambda environment variables updated!"
else
    echo "⚠️  Warning: Could not update Lambda environment variables"
    echo "   You may need to update them manually in the AWS Console"
fi

echo ""
echo "✅ Done! YouTube cookies are now available to the Lambda function."
echo ""
echo "🧪 Test with a YouTube URL:"
echo "   curl -X POST https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev/jobs \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"youtubeUrl\": \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}'"
