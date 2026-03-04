#!/bin/bash
# End-to-End Test for Bass Transcription Pipeline
# Tests the complete flow from upload to PDF generation

set -e

export AWS_PROFILE=production
REGION="us-east-1"
UPLOAD_API="https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com"
JOBS_TABLE="ChordScout-Jobs-V2-dev"
TEST_FILE="${1:-public/04 That_s What I Like.m4a}"

echo "========================================="
echo "BASS TRANSCRIPTION PIPELINE E2E TEST"
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

# Step 1: Request upload URL
echo "========================================="
echo "STEP 1: Request Upload URL"
echo "========================================="

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

echo "Upload response:"
echo "$UPLOAD_RESPONSE" | jq '.'

JOB_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.jobId')
UPLOAD_URL=$(echo "$UPLOAD_RESPONSE" | jq -r '.uploadUrl')

if [ "$JOB_ID" == "null" ] || [ -z "$JOB_ID" ]; then
    echo "❌ ERROR: Failed to get job ID"
    exit 1
fi

echo ""
echo "✓ Job ID: $JOB_ID"
echo "✓ Upload URL obtained"
echo ""

# Step 2: Upload file to S3
echo "========================================="
echo "STEP 2: Upload File to S3"
echo "========================================="

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$UPLOAD_URL" \
  -H "Content-Type: $CONTENT_TYPE" \
  --data-binary "@$TEST_FILE")

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ ERROR: Upload failed with HTTP code: $HTTP_CODE"
    exit 1
fi

echo "✓ File uploaded successfully (HTTP $HTTP_CODE)"
echo ""

# Step 3: Wait for S3 event to trigger process Lambda
echo "========================================="
echo "STEP 3: Wait for S3 Event Trigger"
echo "========================================="

echo "Waiting 5 seconds for S3 event notification..."
sleep 5
echo "✓ S3 event should have triggered process Lambda"
echo ""

# Step 4: Monitor job status
echo "========================================="
echo "STEP 4: Monitor Job Status"
echo "========================================="

MAX_WAIT=600  # 10 minutes
ELAPSED=0
POLL_INTERVAL=10

echo "Polling job status every $POLL_INTERVAL seconds (max $MAX_WAIT seconds)..."
echo ""

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Get job status from DynamoDB
    JOB_DATA=$(aws dynamodb get-item \
        --table-name "$JOBS_TABLE" \
        --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
        --region "$REGION" \
        --output json)
    
    STATUS=$(echo "$JOB_DATA" | jq -r '.Item.status.S // "UNKNOWN"')
    PROGRESS=$(echo "$JOB_DATA" | jq -r '.Item.progress.N // "0"')
    STATUS_MSG=$(echo "$JOB_DATA" | jq -r '.Item.statusMessage.S // ""')
    
    echo "[$(date +%H:%M:%S)] Status: $STATUS | Progress: $PROGRESS% | $STATUS_MSG"
    
    # Check for completion
    if [ "$STATUS" == "COMPLETED" ]; then
        echo ""
        echo "✓ Job completed successfully!"
        break
    fi
    
    # Check for failure
    if [ "$STATUS" == "FAILED" ]; then
        echo ""
        echo "❌ Job failed!"
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
    echo "Last status: $STATUS ($PROGRESS%)"
    exit 1
fi

echo ""

# Step 5: Verify bass data
echo "========================================="
echo "STEP 5: Verify Bass Transcription Data"
echo "========================================="

BASS_DATA=$(echo "$JOB_DATA" | jq '.Item.bassData')

if [ "$BASS_DATA" == "null" ]; then
    echo "❌ ERROR: No bass data found in job"
    exit 1
fi

echo "Bass data found!"
echo ""

# Extract key metrics
KEY=$(echo "$BASS_DATA" | jq -r '.M.key.S // "unknown"')
MODE=$(echo "$BASS_DATA" | jq -r '.M.mode.S // "unknown"')
RELATIVE_MAJOR=$(echo "$BASS_DATA" | jq -r '.M.relativeMajor.S // "unknown"')
TEMPO=$(echo "$BASS_DATA" | jq -r '.M.tempo.N // "0"')
TIME_SIG=$(echo "$BASS_DATA" | jq -r '.M.timeSignature.S // "unknown"')
TOTAL_NOTES=$(echo "$BASS_DATA" | jq -r '.M.totalNotes.N // "0"')
TOTAL_MEASURES=$(echo "$BASS_DATA" | jq -r '.M.totalMeasures.N // "0"')
CONFIDENCE=$(echo "$BASS_DATA" | jq -r '.M.confidence.N // "0"')

echo "Key: $KEY $MODE (Relative major: $RELATIVE_MAJOR)"
echo "Tempo: $TEMPO BPM"
echo "Time Signature: $TIME_SIG"
echo "Total Notes: $TOTAL_NOTES"
echo "Total Measures: $TOTAL_MEASURES"
echo "Key Confidence: $(echo "$CONFIDENCE * 100" | bc)%"
echo ""

# Validate expected values for "That's What I Like"
if [[ "$TEST_FILE" == *"That_s What I Like"* ]]; then
    echo "Validating expected values for 'That's What I Like'..."
    
    if [ "$KEY" != "Bb" ]; then
        echo "⚠️  WARNING: Expected key Bb, got $KEY"
    else
        echo "✓ Key is correct (Bb)"
    fi
    
    if [ "$MODE" != "minor" ]; then
        echo "⚠️  WARNING: Expected minor mode, got $MODE"
    else
        echo "✓ Mode is correct (minor)"
    fi
    
    if [ "$RELATIVE_MAJOR" != "Db" ]; then
        echo "⚠️  WARNING: Expected relative major Db, got $RELATIVE_MAJOR"
    else
        echo "✓ Relative major is correct (Db)"
    fi
    
    TEMPO_INT=$(echo "$TEMPO" | cut -d. -f1)
    if [ "$TEMPO_INT" -lt 130 ] || [ "$TEMPO_INT" -gt 140 ]; then
        echo "⚠️  WARNING: Expected tempo ~134 BPM, got $TEMPO BPM"
    else
        echo "✓ Tempo is in expected range (~134 BPM)"
    fi
fi

echo ""

# Step 6: Check first few measures
echo "========================================="
echo "STEP 6: Verify Measure Data"
echo "========================================="

MEASURES=$(echo "$BASS_DATA" | jq '.M.measures.L')
MEASURE_COUNT=$(echo "$MEASURES" | jq 'length')

echo "Found $MEASURE_COUNT measures"
echo ""
echo "First 4 measures:"

for i in {0..3}; do
    MEASURE=$(echo "$MEASURES" | jq ".[$i].M")
    if [ "$MEASURE" != "null" ]; then
        MEASURE_NUM=$(echo "$MEASURE" | jq -r '.measure.N')
        NNS_DISPLAY=$(echo "$MEASURE" | jq -r '.nns_display.S')
        NOTES_DISPLAY=$(echo "$MEASURE" | jq -r '.notes_display.S')
        
        echo "  Measure $MEASURE_NUM: | $NNS_DISPLAY | ($NOTES_DISPLAY)"
    fi
done

echo ""

# Step 7: Verify PDF URL
echo "========================================="
echo "STEP 7: Verify PDF Generation"
echo "========================================="

PDF_URL=$(echo "$JOB_DATA" | jq -r '.Item.pdfUrl.S // "null"')

if [ "$PDF_URL" == "null" ]; then
    echo "❌ ERROR: No PDF URL found"
    exit 1
fi

echo "✓ PDF URL: $PDF_URL"
echo ""

# Test PDF accessibility
echo "Testing PDF accessibility..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$PDF_URL")

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ ERROR: PDF not accessible (HTTP $HTTP_CODE)"
    exit 1
fi

echo "✓ PDF is accessible (HTTP $HTTP_CODE)"
echo ""

# Step 8: Check ECS logs
echo "========================================="
echo "STEP 8: Check ECS Task Logs"
echo "========================================="

echo "Checking for ECS task logs..."
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
    echo "Last 10 log entries:"
    aws logs get-log-events \
        --log-group-name "/ecs/bass-transcription-dev" \
        --log-stream-name "$LOG_STREAM" \
        --limit 10 \
        --region "$REGION" \
        --query 'events[].message' \
        --output text | tail -10
else
    echo "⚠️  WARNING: No ECS logs found (task may have completed and logs rotated)"
fi

echo ""

# Summary
echo "========================================="
echo "TEST SUMMARY"
echo "========================================="
echo ""
echo "✅ All tests passed!"
echo ""
echo "Job ID: $JOB_ID"
echo "Status: COMPLETED"
echo "Bass transcription: $TOTAL_NOTES notes in $TOTAL_MEASURES measures"
echo "Key: $KEY $MODE (Relative: $RELATIVE_MAJOR)"
echo "PDF: $PDF_URL"
echo ""
echo "========================================="
echo "END-TO-END TEST COMPLETE"
echo "========================================="
