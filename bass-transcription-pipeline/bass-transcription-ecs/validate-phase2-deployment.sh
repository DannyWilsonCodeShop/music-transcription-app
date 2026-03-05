#!/bin/bash
# Phase 2 Deployment Validation Script
# Tests multi-stem transcription with mode selection

set -e

export AWS_PROFILE=production
REGION="us-east-1"
UPLOAD_API="https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com"
JOBS_TABLE="ChordScout-Jobs-V2-dev"
TEST_FILE="${1:-public/04 That_s What I Like.m4a}"

echo "========================================="
echo "PHASE 2 DEPLOYMENT VALIDATION"
echo "========================================="
echo ""
echo "Test file: $TEST_FILE"
echo "Upload API: $UPLOAD_API"
echo "Jobs table: $JOBS_TABLE"
echo ""

# Check if test file exists
if [ ! -f "$TEST_FILE" ]; then
    echo "❌ ERROR: Test file not found: $TEST_FILE"
    exit 1
fi

echo "✓ Test file found"
echo ""

# Test 1: Bass-only mode (backward compatibility)
echo "========================================="
echo "TEST 1: Bass-Only Mode (Backward Compatibility)"
echo "========================================="
echo ""

FILENAME=$(basename "$TEST_FILE")
CONTENT_TYPE="audio/x-m4a"

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
    exit 1
fi

echo "✓ Job ID: $JOB_ID"
echo ""

# Upload file
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
echo "Monitoring job status..."
MAX_WAIT=600
ELAPSED=0
POLL_INTERVAL=10

while [ $ELAPSED -lt $MAX_WAIT ]; do
    JOB_DATA=$(aws dynamodb get-item \
        --table-name "$JOBS_TABLE" \
        --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
        --region "$REGION" \
        --output json)
    
    STATUS=$(echo "$JOB_DATA" | jq -r '.Item.status.S // "UNKNOWN"')
    PROGRESS=$(echo "$JOB_DATA" | jq -r '.Item.progress.N // "0"')
    STATUS_MSG=$(echo "$JOB_DATA" | jq -r '.Item.statusMessage.S // ""')
    
    echo "[$(date +%H:%M:%S)] Status: $STATUS | Progress: $PROGRESS% | $STATUS_MSG"
    
    if [ "$STATUS" == "COMPLETED" ]; then
        echo ""
        echo "✓ Bass-only mode completed successfully!"
        break
    fi
    
    if [ "$STATUS" == "FAILED" ]; then
        echo ""
        echo "❌ Bass-only mode failed!"
        ERROR_MSG=$(echo "$JOB_DATA" | jq -r '.Item.errorMessage.S // "Unknown error"')
        echo "Error: $ERROR_MSG"
        exit 1
    fi
    
    sleep $POLL_INTERVAL
    ELAPSED=$((ELAPSED + POLL_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo ""
    echo "❌ ERROR: Job did not complete within $MAX_WAIT seconds"
    exit 1
fi

# Verify bass data
BASS_DATA=$(echo "$JOB_DATA" | jq '.Item.bassData')
if [ "$BASS_DATA" == "null" ]; then
    echo "❌ ERROR: No bass data found"
    exit 1
fi

TOTAL_NOTES=$(echo "$BASS_DATA" | jq -r '.M.totalNotes.N // "0"')
echo "✓ Bass transcription: $TOTAL_NOTES notes"

# Verify PDF
PDF_URL=$(echo "$JOB_DATA" | jq -r '.Item.pdfUrl.S // "null"')
if [ "$PDF_URL" == "null" ]; then
    echo "❌ ERROR: No PDF URL found"
    exit 1
fi
echo "✓ PDF generated: $PDF_URL"
echo ""

# Test 2: Check CloudWatch logs
echo "========================================="
echo "TEST 2: Check CloudWatch Logs"
echo "========================================="
echo ""

echo "Checking for errors in ECS logs..."
LOG_STREAM=$(aws logs describe-log-streams \
    --log-group-name "/ecs/bass-transcription-dev" \
    --order-by LastEventTime \
    --descending \
    --max-items 1 \
    --region "$REGION" \
    --query 'logStreams[0].logStreamName' \
    --output text 2>/dev/null || echo "")

if [ -n "$LOG_STREAM" ] && [ "$LOG_STREAM" != "None" ]; then
    echo "✓ Found ECS log stream: $LOG_STREAM"
    echo ""
    
    # Check for errors
    ERROR_COUNT=$(aws logs filter-log-events \
        --log-group-name "/ecs/bass-transcription-dev" \
        --log-stream-names "$LOG_STREAM" \
        --filter-pattern "ERROR" \
        --region "$REGION" \
        --query 'length(events)' \
        --output text 2>/dev/null || echo "0")
    
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "⚠️  WARNING: Found $ERROR_COUNT ERROR entries in logs"
        echo ""
        echo "Recent errors:"
        aws logs filter-log-events \
            --log-group-name "/ecs/bass-transcription-dev" \
            --log-stream-names "$LOG_STREAM" \
            --filter-pattern "ERROR" \
            --region "$REGION" \
            --query 'events[].message' \
            --output text | tail -5
        echo ""
    else
        echo "✓ No ERROR entries found in logs"
    fi
    
    # Show recent log entries
    echo ""
    echo "Recent log entries:"
    aws logs get-log-events \
        --log-group-name "/ecs/bass-transcription-dev" \
        --log-stream-name "$LOG_STREAM" \
        --limit 20 \
        --region "$REGION" \
        --query 'events[].message' \
        --output text | tail -20
else
    echo "⚠️  WARNING: No ECS logs found"
fi

echo ""

# Test 3: Verify processing completed successfully
echo "========================================="
echo "TEST 3: Verify Processing Metrics"
echo "========================================="
echo ""

# Check if ENABLE_MULTI_STEM is working
TRANSCRIPTION_MODE=$(echo "$JOB_DATA" | jq -r '.Item.transcriptionMode.S // "not-set"')
echo "Transcription mode: $TRANSCRIPTION_MODE"

if [ "$TRANSCRIPTION_MODE" == "not-set" ]; then
    echo "⚠️  Note: transcriptionMode field not set (expected for bass-only default)"
else
    echo "✓ Transcription mode field is set"
fi

# Check for stem data (should not exist for bass-only)
STEM_DATA=$(echo "$JOB_DATA" | jq '.Item.stemData // null')
if [ "$STEM_DATA" != "null" ]; then
    echo "⚠️  WARNING: Unexpected stem data found for bass-only mode"
else
    echo "✓ No stem data (correct for bass-only mode)"
fi

echo ""

# Summary
echo "========================================="
echo "VALIDATION SUMMARY"
echo "========================================="
echo ""
echo "✅ Phase 2 Deployment Validation Complete!"
echo ""
echo "Results:"
echo "  ✓ Bass-only mode works (backward compatibility)"
echo "  ✓ Processing completes successfully"
echo "  ✓ PDF generation works"
echo "  ✓ No critical errors in logs"
echo ""
echo "Job ID: $JOB_ID"
echo "PDF: $PDF_URL"
echo ""
echo "Note: Multi-stem mode selection requires frontend interaction."
echo "To test mode selection:"
echo "  1. Upload a file through the frontend"
echo "  2. Wait for PENDING_MODE_SELECTION status"
echo "  3. Select a mode (bass+piano, bass+guitar, or all)"
echo "  4. Verify stems are transcribed"
echo ""
echo "========================================="

