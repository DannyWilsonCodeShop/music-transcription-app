#!/bin/bash

# Test Phase 2 Interactive Workflow
# This script tests the full v3.0 workflow with mode selection and key confirmation

set -e

export AWS_PROFILE=production
REGION="us-east-1"
UPLOAD_API="https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com"
TABLE="ChordScout-Jobs-V2-dev"

echo "========================================="
echo "Phase 2 Interactive Workflow Test"
echo "========================================="
echo ""

# Use test audio file
TEST_FILE="${1:-public/04 That_s What I Like.m4a}"

if [ ! -f "$TEST_FILE" ]; then
    echo "❌ Test file not found: $TEST_FILE"
    exit 1
fi

echo "📁 Test file: $TEST_FILE"
echo ""

# Upload via API
FILENAME=$(basename "$TEST_FILE")
CONTENT_TYPE="audio/x-m4a"

echo "📤 Uploading file via API..."
UPLOAD_RESPONSE=$(curl -s -X POST "$UPLOAD_API/upload" \
  -H "Content-Type: application/json" \
  -d "{
    \"filename\": \"$FILENAME\",
    \"contentType\": \"$CONTENT_TYPE\",
    \"analysisOptions\": {
      \"musicPart\": \"bass\",
      \"includeKey\": true,
      \"includeTempo\": true,
      \"includeTimeSignature\": true
    }
  }")

JOB_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.jobId')
UPLOAD_URL=$(echo "$UPLOAD_RESPONSE" | jq -r '.uploadUrl')

if [ "$JOB_ID" == "null" ] || [ -z "$JOB_ID" ]; then
    echo "❌ ERROR: Failed to get job ID"
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi

echo "✓ Job ID: $JOB_ID"
echo ""

# Upload file to S3
echo "📤 Uploading file to S3..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$UPLOAD_URL" \
  -H "Content-Type: $CONTENT_TYPE" \
  --data-binary "@$TEST_FILE")

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ ERROR: Upload failed with HTTP code: $HTTP_CODE"
    exit 1
fi

echo "✓ File uploaded successfully"
echo ""

# Wait for S3 trigger
echo "Waiting 5 seconds for S3 event trigger..."
sleep 5
echo ""

# Monitor job status
echo "📊 Monitoring job status..."
echo "   (Waiting for PENDING_MODE_SELECTION status)"
echo ""

TIMEOUT=300
ELAPSED=0
POLL_INTERVAL=5

while [ $ELAPSED -lt $TIMEOUT ]; do
    # Get job status
    JOB_DATA=$(aws dynamodb get-item \
        --table-name $TABLE \
        --key "{\"jobId\": {\"S\": \"${JOB_ID}\"}}" \
        --region $REGION \
        --output json)
    
    STATUS=$(echo "$JOB_DATA" | jq -r '.Item.status.S // "UNKNOWN"')
    PROGRESS=$(echo "$JOB_DATA" | jq -r '.Item.progress.N // "0"')
    MESSAGE=$(echo "$JOB_DATA" | jq -r '.Item.statusMessage.S // ""')
    
    echo "[$(date +%H:%M:%S)] Status: $STATUS | Progress: ${PROGRESS}% | $MESSAGE"
    
    # Check if we reached mode selection
    if [ "$STATUS" = "PENDING_MODE_SELECTION" ]; then
        echo ""
        echo "✅ SUCCESS: Job reached PENDING_MODE_SELECTION status!"
        echo ""
        echo "🎯 Next steps to test manually:"
        echo "   1. Open ChordScout UI"
        echo "   2. TranscriptionModeSelector modal should appear"
        echo "   3. Select a mode (bass-only, bass+piano, bass+guitar, or all)"
        echo "   4. Job should proceed to PENDING_KEY_CONFIRMATION"
        echo "   5. KeyConfirmation modal should appear"
        echo "   6. Confirm or change the key"
        echo "   7. Job should complete with PDF generation"
        echo ""
        echo "📋 Job ID for UI testing: $JOB_ID"
        echo ""
        exit 0
    fi
    
    # Check for failure
    if [ "$STATUS" = "FAILED" ]; then
        echo ""
        echo "❌ Job failed!"
        ERROR_MSG=$(echo "$JOB_DATA" | jq -r '.Item.errorMessage.S // "Unknown error"')
        echo "Error: $ERROR_MSG"
        echo "   Check CloudWatch logs for details"
        exit 1
    fi
    
    # Check if completed (shouldn't happen without mode selection)
    if [ "$STATUS" = "COMPLETED" ]; then
        echo ""
        echo "⚠️  Job completed without mode selection prompt!"
        echo "   This indicates the backend is still bypassing mode selection"
        exit 1
    fi
    
    sleep $POLL_INTERVAL
    ELAPSED=$((ELAPSED + POLL_INTERVAL))
done

echo ""
echo "⏱️  Timeout waiting for PENDING_MODE_SELECTION status"
echo "   Last status: $STATUS"
echo "   Check CloudWatch logs for details"
exit 1
