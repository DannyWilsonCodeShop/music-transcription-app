#!/bin/bash

# Test the upload fix with Content-Type matching

API_ENDPOINT="https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com"

echo "🧪 Testing Upload Fix (Content-Type Matching)"
echo "=============================================="
echo ""

# Create a small test file
echo "Creating test audio file..."
dd if=/dev/zero of=/tmp/test-audio.mp3 bs=1024 count=10 2>/dev/null
echo ""

# Step 1: Request upload URL
echo "📤 Step 1: Requesting upload URL..."
RESPONSE=$(curl -s -X POST "$API_ENDPOINT/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test-audio.mp3",
    "contentType": "audio/mpeg",
    "userId": "test-user"
  }')

echo "$RESPONSE" | jq .
echo ""

JOB_ID=$(echo "$RESPONSE" | jq -r '.jobId')
UPLOAD_URL=$(echo "$RESPONSE" | jq -r '.uploadUrl')

if [ "$JOB_ID" == "null" ]; then
  echo "❌ Failed to get upload URL"
  exit 1
fi

echo "✅ Got upload URL"
echo "Job ID: $JOB_ID"
echo ""

# Step 2: Upload file WITH Content-Type header (matching presigned URL)
echo "📤 Step 2: Uploading file WITH Content-Type: audio/mpeg..."
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/upload-response.txt \
  -X PUT "$UPLOAD_URL" \
  -H "Content-Type: audio/mpeg" \
  --data-binary "@/tmp/test-audio.mp3")

echo "HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" == "200" ]; then
  echo "✅ Upload successful!"
  echo ""
  echo "🎉 FIX VERIFIED! Content-Type matching works!"
else
  echo "❌ Upload failed"
  echo "Response:"
  cat /tmp/upload-response.txt
  echo ""
  exit 1
fi

echo ""
echo "📊 Checking job status..."
sleep 2

STATUS_RESPONSE=$(curl -s "$API_ENDPOINT/jobs/$JOB_ID")
echo "$STATUS_RESPONSE" | jq .

echo ""
echo "✅ Test complete!"
