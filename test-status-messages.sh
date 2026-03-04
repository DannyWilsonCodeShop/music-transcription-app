#!/bin/bash

# Test script to verify status messages update throughout the pipeline
# This script uploads a file and monitors the status messages

set -e

AWS_PROFILE=production
REGION=us-east-1
API_ENDPOINT="https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com"
TEST_FILE="public/meetup_ring.mp3"

echo "=========================================="
echo "Testing Status Message Updates"
echo "=========================================="
echo ""

# Check if test file exists
if [ ! -f "$TEST_FILE" ]; then
    echo "❌ Test file not found: $TEST_FILE"
    exit 1
fi

echo "1. Requesting upload URL..."
UPLOAD_RESPONSE=$(curl -s -X POST "$API_ENDPOINT/upload" \
    -H "Content-Type: application/json" \
    -d "{\"filename\": \"test-status-$(date +%s).mp3\", \"contentType\": \"audio/mpeg\", \"userId\": \"test-user\"}")

echo "Response: $UPLOAD_RESPONSE"
echo ""

JOB_ID=$(echo $UPLOAD_RESPONSE | jq -r '.jobId')
UPLOAD_URL=$(echo $UPLOAD_RESPONSE | jq -r '.uploadUrl')

if [ "$JOB_ID" == "null" ] || [ "$UPLOAD_URL" == "null" ]; then
    echo "❌ Failed to get upload URL"
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi

echo "✓ Job ID: $JOB_ID"
echo "✓ Upload URL obtained"
echo ""

echo "2. Uploading file to S3..."
curl -s -X PUT "$UPLOAD_URL" \
    -H "Content-Type: audio/mpeg" \
    --data-binary "@$TEST_FILE" > /dev/null

echo "✓ File uploaded successfully"
echo ""

echo "3. Monitoring status messages (will check every 3 seconds for 5 minutes)..."
echo "   Expected progression:"
echo "   - Starting audio processing... (10%)"
echo "   - Downloading audio file... (30%)"
echo "   - Analyzing audio and detecting chords... (40%)"
echo "   - Extracting lyrics with AI... (70%)"
echo "   - Aligning lyrics with chords... (78%)"
echo "   - Saving chord data... (85%)"
echo "   - Generating PDF chord sheet... (90%)"
echo "   - Complete! Your chord sheet is ready. (100%)"
echo ""

LAST_STATUS=""
LAST_MESSAGE=""
LAST_PROGRESS=0
MAX_ATTEMPTS=100  # 5 minutes (100 * 3 seconds)
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    # Get job status
    STATUS_RESPONSE=$(curl -s "$API_ENDPOINT/jobs/$JOB_ID")
    
    CURRENT_STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
    CURRENT_MESSAGE=$(echo $STATUS_RESPONSE | jq -r '.statusMessage // "No message"')
    CURRENT_PROGRESS=$(echo $STATUS_RESPONSE | jq -r '.progress // 0')
    
    # Only print if status, message, or progress changed
    if [ "$CURRENT_STATUS" != "$LAST_STATUS" ] || [ "$CURRENT_MESSAGE" != "$LAST_MESSAGE" ] || [ "$CURRENT_PROGRESS" != "$LAST_PROGRESS" ]; then
        TIMESTAMP=$(date +"%H:%M:%S")
        echo "[$TIMESTAMP] Status: $CURRENT_STATUS | Progress: $CURRENT_PROGRESS% | Message: $CURRENT_MESSAGE"
        
        LAST_STATUS="$CURRENT_STATUS"
        LAST_MESSAGE="$CURRENT_MESSAGE"
        LAST_PROGRESS="$CURRENT_PROGRESS"
    fi
    
    # Check if completed or failed
    if [ "$CURRENT_STATUS" == "COMPLETED" ]; then
        echo ""
        echo "=========================================="
        echo "✅ Job completed successfully!"
        echo "=========================================="
        echo ""
        echo "Final status:"
        echo "$STATUS_RESPONSE" | jq '.'
        exit 0
    fi
    
    if [ "$CURRENT_STATUS" == "FAILED" ]; then
        echo ""
        echo "=========================================="
        echo "❌ Job failed"
        echo "=========================================="
        echo ""
        ERROR_MESSAGE=$(echo $STATUS_RESPONSE | jq -r '.errorMessage // "Unknown error"')
        echo "Error: $ERROR_MESSAGE"
        echo ""
        echo "Full response:"
        echo "$STATUS_RESPONSE" | jq '.'
        exit 1
    fi
    
    sleep 3
done

echo ""
echo "⚠️  Timeout: Job did not complete within 5 minutes"
echo "Last status: $CURRENT_STATUS ($CURRENT_PROGRESS%)"
echo "Last message: $CURRENT_MESSAGE"
exit 1
