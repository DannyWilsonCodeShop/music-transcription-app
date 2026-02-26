#!/bin/bash

# Test direct upload to verify backend is working

API_ENDPOINT="https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com"
TEST_FILE="public/13_The_Girl_from_Ipanema__feat._Bebe[43060].mp3"

echo "🧪 Testing Direct Upload"
echo "========================"
echo ""

# Step 1: Request upload URL
echo "📤 Step 1: Requesting upload URL..."
RESPONSE=$(curl -s -X POST "$API_ENDPOINT/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.mp3",
    "contentType": "audio/mpeg",
    "userId": "test"
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

# Step 2: Upload file WITHOUT Content-Type header
echo "📤 Step 2: Uploading file (NO Content-Type header)..."
if [ ! -f "$TEST_FILE" ]; then
  echo "⚠️  Test file not found, creating dummy file..."
  echo "test data" > /tmp/test-upload.mp3
  TEST_FILE="/tmp/test-upload.mp3"
fi

# Upload with curl (no Content-Type header)
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/upload-response.txt \
  -X PUT "$UPLOAD_URL" \
  --data-binary "@$TEST_FILE")

echo "HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" == "200" ]; then
  echo "✅ Upload successful!"
else
  echo "❌ Upload failed"
  echo "Response:"
  cat /tmp/upload-response.txt
  exit 1
fi

echo ""
echo "🎉 Test passed! Backend is working correctly."
echo ""
echo "The issue is in the frontend. Check browser console for errors."
