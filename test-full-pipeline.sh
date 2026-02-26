#!/bin/bash

# Test the full pipeline end-to-end

API_ENDPOINT="https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com"

echo "🧪 Testing Full Pipeline (Upload → Process → Complete)"
echo "========================================================"
echo ""

# Create a small test file
echo "Creating test audio file..."
dd if=/dev/zero of=/tmp/test-pipeline.mp3 bs=1024 count=10 2>/dev/null
echo ""

# Step 1: Request upload URL
echo "📤 Step 1: Requesting upload URL..."
RESPONSE=$(curl -s -X POST "$API_ENDPOINT/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test-pipeline.mp3",
    "contentType": "audio/mpeg",
    "userId": "test-user"
  }')

JOB_ID=$(echo "$RESPONSE" | jq -r '.jobId')
UPLOAD_URL=$(echo "$RESPONSE" | jq -r '.uploadUrl')

if [ "$JOB_ID" == "null" ]; then
  echo "❌ Failed to get upload URL"
  exit 1
fi

echo "✅ Got upload URL"
echo "Job ID: $JOB_ID"
echo ""

# Step 2: Upload file
echo "📤 Step 2: Uploading file..."
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/upload-response.txt \
  -X PUT "$UPLOAD_URL" \
  -H "Content-Type: audio/mpeg" \
  --data-binary "@/tmp/test-pipeline.mp3")

if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ Upload failed with status $HTTP_CODE"
  cat /tmp/upload-response.txt
  exit 1
fi

echo "✅ Upload successful!"
echo ""

# Step 3: Poll job status
echo "📊 Step 3: Monitoring job status..."
echo ""

for i in {1..60}; do
  sleep 5
  
  STATUS_RESPONSE=$(curl -s "$API_ENDPOINT/jobs/$JOB_ID")
  STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
  PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.progress // 0')
  
  echo "[$i] Status: $STATUS | Progress: $PROGRESS%"
  
  if [ "$STATUS" == "COMPLETED" ]; then
    echo ""
    echo "🎉 Job completed successfully!"
    echo ""
    echo "Final result:"
    echo "$STATUS_RESPONSE" | jq .
    exit 0
  fi
  
  if [ "$STATUS" == "FAILED" ]; then
    echo ""
    echo "❌ Job failed!"
    echo ""
    echo "Error details:"
    echo "$STATUS_RESPONSE" | jq .
    exit 1
  fi
done

echo ""
echo "⏱️  Timeout: Job did not complete within 5 minutes"
echo ""
echo "Last status:"
curl -s "$API_ENDPOINT/jobs/$JOB_ID" | jq .
