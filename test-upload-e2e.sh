#!/bin/bash
# End-to-End Upload Test
# Tests the complete pipeline from upload to PDF generation

set -e

export AWS_PROFILE=production
API_ENDPOINT="https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com"
TEST_FILE="public/04 That_s What I Like.m4a"

if [ ! -f "$TEST_FILE" ]; then
    echo "❌ Test file not found: $TEST_FILE"
    exit 1
fi

echo "========================================="
echo "End-to-End Upload Test"
echo "========================================="
echo ""
echo "Test file: $TEST_FILE"
echo "API endpoint: $API_ENDPOINT"
echo ""

# Step 1: Request upload URL
echo "1. Requesting upload URL..."
UPLOAD_RESPONSE=$(curl -s -X POST "$API_ENDPOINT/upload" \
    -H "Content-Type: application/json" \
    -d "{\"filename\":\"test-$(date +%s).m4a\",\"contentType\":\"audio/x-m4a\",\"userId\":\"test-user\"}")

echo "Response: $UPLOAD_RESPONSE"

JOB_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.jobId')
UPLOAD_URL=$(echo "$UPLOAD_RESPONSE" | jq -r '.uploadUrl')

if [ "$JOB_ID" == "null" ] || [ -z "$JOB_ID" ]; then
    echo "❌ Failed to get job ID"
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi

echo "✅ Job ID: $JOB_ID"
echo ""

# Step 2: Upload file to S3
echo "2. Uploading file to S3..."
UPLOAD_STATUS=$(curl -s -w "%{http_code}" -o /dev/null -X PUT "$UPLOAD_URL" \
    -H "Content-Type: audio/x-m4a" \
    --data-binary "@$TEST_FILE")

if [ "$UPLOAD_STATUS" == "200" ]; then
    echo "✅ File uploaded successfully"
else
    echo "❌ Upload failed with status: $UPLOAD_STATUS"
    exit 1
fi
echo ""

# Step 3: Monitor job status
echo "3. Monitoring job status..."
echo ""

MAX_ATTEMPTS=60  # 5 minutes (60 * 5 seconds)
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    # Get job status
    JOB_STATUS=$(curl -s "$API_ENDPOINT/jobs/$JOB_ID")
    
    STATUS=$(echo "$JOB_STATUS" | jq -r '.status')
    PROGRESS=$(echo "$JOB_STATUS" | jq -r '.progress // 0')
    STATUS_MSG=$(echo "$JOB_STATUS" | jq -r '.statusMessage // ""')
    
    # Display progress
    printf "\r[%2d/%2d] Status: %-20s Progress: %3d%% %s" \
        $ATTEMPT $MAX_ATTEMPTS "$STATUS" "$PROGRESS" "$STATUS_MSG"
    
    # Check if complete
    if [ "$STATUS" == "COMPLETED" ] || [ "$STATUS" == "COMPLETE" ]; then
        echo ""
        echo ""
        echo "✅ Job completed successfully!"
        
        # Get PDF URL
        PDF_URL=$(echo "$JOB_STATUS" | jq -r '.pdfUrl // "none"')
        echo "PDF URL: $PDF_URL"
        
        # Get chord data summary
        CHORD_COUNT=$(echo "$JOB_STATUS" | jq -r '.chordsData.chords | length // 0')
        KEY=$(echo "$JOB_STATUS" | jq -r '.chordsData.key // "unknown"')
        DURATION=$(echo "$JOB_STATUS" | jq -r '.chordsData.duration // 0')
        
        echo ""
        echo "Chord Detection Results:"
        echo "  Key: $KEY"
        echo "  Duration: ${DURATION}s"
        echo "  Chords detected: $CHORD_COUNT"
        
        # Check for lyrics
        WORD_COUNT=$(echo "$JOB_STATUS" | jq -r '.lyricsData.words | length // 0')
        if [ "$WORD_COUNT" -gt 0 ]; then
            echo "  Lyrics words: $WORD_COUNT"
        fi
        
        # Check for lead sheet
        LEAD_SHEET=$(echo "$JOB_STATUS" | jq -r '.leadSheet // null')
        if [ "$LEAD_SHEET" != "null" ]; then
            SECTION_COUNT=$(echo "$LEAD_SHEET" | jq -r '.sections | length // 0')
            echo "  Lead sheet sections: $SECTION_COUNT"
        fi
        
        echo ""
        echo "========================================="
        echo "Test PASSED ✅"
        echo "========================================="
        exit 0
    fi
    
    # Check if failed
    if [ "$STATUS" == "FAILED" ]; then
        echo ""
        echo ""
        echo "❌ Job failed!"
        ERROR_MSG=$(echo "$JOB_STATUS" | jq -r '.errorMessage // "Unknown error"')
        echo "Error: $ERROR_MSG"
        echo ""
        echo "========================================="
        echo "Test FAILED ❌"
        echo "========================================="
        exit 1
    fi
    
    # Wait before next check
    sleep 5
done

echo ""
echo ""
echo "⏱️  Timeout: Job did not complete within 5 minutes"
echo "Last status: $STATUS ($PROGRESS%)"
echo ""

# Check ECS tasks
echo "Checking ECS tasks..."
aws ecs list-tasks --cluster ChordScout-dev --query 'taskArns' --output text | while read TASK_ARN; do
    if [ -n "$TASK_ARN" ]; then
        echo "Task: $TASK_ARN"
        aws ecs describe-tasks --cluster ChordScout-dev --tasks "$TASK_ARN" \
            --query 'tasks[0].{Status:lastStatus,StoppedReason:stoppedReason}' --output json
    fi
done

echo ""
echo "========================================="
echo "Test TIMEOUT ⏱️"
echo "========================================="
exit 1
