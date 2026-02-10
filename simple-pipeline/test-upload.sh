#!/bin/bash
# Test File Upload Pipeline

set -e

export AWS_PROFILE=production

# Load config
if [ ! -f config-upload.json ]; then
    echo "Error: config-upload.json not found. Run ./deploy-file-upload.sh first"
    exit 1
fi

API_ENDPOINT=$(cat config-upload.json | python3 -c "import sys, json; print(json.load(sys.stdin)['apiEndpoint'])")
AUDIO_FILE=${1:-""}

if [ -z "$AUDIO_FILE" ]; then
    echo "Usage: ./test-upload.sh <audio-file>"
    echo "Example: ./test-upload.sh ~/Music/song.mp3"
    exit 1
fi

if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: File not found: $AUDIO_FILE"
    exit 1
fi

FILENAME=$(basename "$AUDIO_FILE")
FILE_SIZE=$(stat -f%z "$AUDIO_FILE" 2>/dev/null || stat -c%s "$AUDIO_FILE" 2>/dev/null)

echo "========================================="
echo "Testing File Upload Pipeline"
echo "========================================="
echo ""
echo "File: $AUDIO_FILE"
echo "Size: $FILE_SIZE bytes ($(echo "scale=2; $FILE_SIZE / 1024 / 1024" | bc) MB)"
echo "API Endpoint: $API_ENDPOINT"
echo ""

# Step 1: Request upload URL
echo "📝 Requesting upload URL..."
RESPONSE=$(curl -s -X POST "${API_ENDPOINT}/upload" \
  -H "Content-Type: application/json" \
  -d "{\"filename\": \"$FILENAME\", \"contentType\": \"audio/mpeg\", \"userId\": \"test-user\"}")

echo "Response: $RESPONSE"
echo ""

JOB_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['jobId'])")
UPLOAD_URL=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['uploadUrl'])")

echo "Job ID: $JOB_ID"
echo ""

# Step 2: Upload file
echo "☁️  Uploading file..."
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: audio/mpeg" \
  --data-binary "@$AUDIO_FILE" \
  --progress-bar | cat

echo ""
echo "✅ Upload complete!"
echo ""

# Step 3: Check job status
echo "📊 Checking job status..."
sleep 2

STATUS_RESPONSE=$(curl -s "${API_ENDPOINT}/jobs/${JOB_ID}")
echo "$STATUS_RESPONSE" | python3 -m json.tool

echo ""
echo "========================================="
echo "✅ Test Complete!"
echo "========================================="
echo ""
echo "Job ID: $JOB_ID"
echo ""
echo "Check job status:"
echo "  curl ${API_ENDPOINT}/jobs/${JOB_ID} | python3 -m json.tool"
echo ""
