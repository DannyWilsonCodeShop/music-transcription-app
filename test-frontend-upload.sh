#!/bin/bash

# Test script to debug frontend upload issues
# This simulates what the frontend does

API_ENDPOINT="https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com"
TEST_FILE="public/13_The_Girl_from_Ipanema__feat._Bebe[43060].mp3"

echo "🧪 Testing Frontend Upload Flow"
echo "================================"
echo ""

# Step 1: Request upload URL
echo "📤 Step 1: Requesting upload URL..."
RESPONSE=$(curl -s -X POST "$API_ENDPOINT/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test-upload.mp3",
    "contentType": "audio/mpeg",
    "userId": "guest"
  }')

echo "Response: $RESPONSE"
echo ""

# Extract jobId and uploadUrl
JOB_ID=$(echo "$RESPONSE" | jq -r '.jobId')
UPLOAD_URL=$(echo "$RESPONSE" | jq -r '.uploadUrl')

if [ "$JOB_ID" == "null" ] || [ "$UPLOAD_URL" == "null" ]; then
  echo "❌ Failed to get upload URL"
  exit 1
fi

echo "✅ Got upload URL"
echo "Job ID: $JOB_ID"
echo ""

# Step 2: Upload file to S3
echo "📤 Step 2: Uploading file to S3..."
if [ ! -f "$TEST_FILE" ]; then
  echo "❌ Test file not found: $TEST_FILE"
  echo "Please provide a test audio file"
  exit 1
fi

# Upload with progress
curl -X PUT "$UPLOAD_URL" \
  --data-binary "@$TEST_FILE" \
  --progress-bar \
  -o /dev/null

if [ $? -eq 0 ]; then
  echo "✅ File uploaded successfully"
else
  echo "❌ Upload failed"
  exit 1
fi

echo ""

# Step 3: Poll for status
echo "📊 Step 3: Polling for job status..."
for i in {1..30}; do
  sleep 2
  STATUS_RESPONSE=$(curl -s "$API_ENDPOINT/jobs/$JOB_ID")
  STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
  PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.progress // 0')
  
  echo "[$i] Status: $STATUS | Progress: $PROGRESS%"
  
  if [ "$STATUS" == "COMPLETED" ]; then
    echo ""
    echo "✅ Job completed successfully!"
    echo ""
    echo "Results:"
    echo "$STATUS_RESPONSE" | jq '{
      status,
      progress,
      chordsData: {
        key,
        mode,
        tempo,
        timeSignature,
        duration,
        totalChords
      }
    }'
    exit 0
  elif [ "$STATUS" == "FAILED" ]; then
    echo ""
    echo "❌ Job failed"
    echo "Error: $(echo "$STATUS_RESPONSE" | jq -r '.errorMessage')"
    exit 1
  fi
done

echo ""
echo "⏱️ Timeout waiting for job to complete"
echo "Last status: $STATUS"
