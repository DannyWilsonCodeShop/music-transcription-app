#!/bin/bash
# Test bass-only chord detection with analysis options modal

set -e

export AWS_PROFILE=production
REGION="us-east-1"
API_ENDPOINT="https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com"
JOBS_TABLE="ChordScout-Jobs-V2-dev"

# Test file
TEST_FILE="${1:-public/04 That_s What I Like.m4a}"

if [ ! -f "$TEST_FILE" ]; then
    echo "Error: Test file not found: $TEST_FILE"
    exit 1
fi

echo "========================================="
echo "Testing Bass-Only Chord Detection"
echo "========================================="
echo ""
echo "Test file: $TEST_FILE"
echo "API Endpoint: $API_ENDPOINT"
echo ""

# Step 1: Request upload URL with analysis options
echo "Step 1: Requesting upload URL with analysis options..."
FILENAME=$(basename "$TEST_FILE")
CONTENT_TYPE="audio/m4a"

UPLOAD_RESPONSE=$(curl -s -X POST "$API_ENDPOINT/upload" \
  -H "Content-Type: application/json" \
  -d "{
    \"filename\": \"$FILENAME\",
    \"contentType\": \"$CONTENT_TYPE\",
    \"userId\": \"test-user\",
    \"analysisOptions\": {
      \"musicPart\": \"bass\",
      \"includeLyrics\": false,
      \"includeKey\": true,
      \"includeTempo\": true,
      \"includeTimeSignature\": true
    }
  }")

echo "$UPLOAD_RESPONSE" | jq '.'

JOB_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.jobId')
UPLOAD_URL=$(echo "$UPLOAD_RESPONSE" | jq -r '.uploadUrl')

if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "null" ]; then
    echo "Error: Failed to get job ID"
    exit 1
fi

echo ""
echo "✓ Job ID: $JOB_ID"
echo ""

# Step 2: Upload file to S3
echo "Step 2: Uploading file to S3..."
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: $CONTENT_TYPE" \
  --data-binary "@$TEST_FILE" \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "✓ File uploaded"
echo ""

# Step 3: Check job data in DynamoDB
echo "Step 3: Checking job data in DynamoDB..."
aws dynamodb get-item \
  --table-name "$JOBS_TABLE" \
  --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
  --region "$REGION" \
  --query 'Item.{
    jobId: jobId.S,
    status: status.S,
    progress: progress.N,
    analysisOptions: analysisOptions.M
  }' \
  --output json | jq '.'

echo ""
echo "========================================="
echo "Test Complete!"
echo "========================================="
echo ""
echo "Job ID: $JOB_ID"
echo ""
echo "Monitor progress:"
echo "  watch -n 2 \"aws dynamodb get-item --table-name $JOBS_TABLE --key '{\\\"jobId\\\": {\\\"S\\\": \\\"$JOB_ID\\\"}}' --region $REGION --query 'Item.{status: status.S, progress: progress.N, statusMessage: statusMessage.S}' --output json | jq '.'\""
echo ""
echo "Check ECS logs:"
echo "  aws logs tail /ecs/chordscout-chord-detector-dev --follow --region $REGION"
echo ""
echo "View results:"
echo "  aws dynamodb get-item --table-name $JOBS_TABLE --key '{\"jobId\": {\"S\": \"$JOB_ID\"}}' --region $REGION --query 'Item.chordsData.M.{stemUsed: stemUsed.S, stemSeparationEnabled: stemSeparationEnabled.BOOL, totalChords: totalChords.N, key: key.S}' --output json | jq '.'"
echo ""
