#!/bin/bash
# Test Simple Pipeline

set -e

# Use production profile for account 8474
export AWS_PROFILE=production

# Load config
if [ ! -f config.json ]; then
    echo "Error: config.json not found. Run ./deploy.sh first"
    exit 1
fi

API_ENDPOINT=$(cat config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['apiEndpoint'])")
AUDIO_BUCKET=$(cat config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['audioBucket'])")
JOBS_TABLE=$(cat config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['jobsTable'])")
REGION=$(cat config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['region'])")

YOUTUBE_URL=${1:-"https://www.youtube.com/watch?v=Q-RKhgsZu64"}

echo "========================================="
echo "Testing Simple Pipeline"
echo "========================================="
echo ""
echo "YouTube URL: $YOUTUBE_URL"
echo "API Endpoint: $API_ENDPOINT"
echo ""

# Generate job ID
JOB_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')

echo "Job ID: $JOB_ID"
echo ""

# Submit job
echo "Submitting job..."
RESPONSE=$(curl -s -X POST "${API_ENDPOINT}/download" \
  -H "Content-Type: application/json" \
  -d "{\"youtubeUrl\": \"$YOUTUBE_URL\", \"jobId\": \"$JOB_ID\"}")

echo "Response: $RESPONSE"
echo ""

# Wait for completion
echo "Waiting for job to complete..."
MAX_ATTEMPTS=60
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    sleep 5
    ATTEMPT=$((ATTEMPT + 1))
    
    # Get job status
    JOB=$(aws dynamodb get-item \
        --table-name $JOBS_TABLE \
        --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
        --region $REGION \
        --output json 2>/dev/null || echo "{}")
    
    if [ "$JOB" = "{}" ]; then
        echo "  Attempt $ATTEMPT: Job not found yet..."
        continue
    fi
    
    STATUS=$(echo $JOB | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('Item', {}).get('status', {}).get('S', 'UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")
    PROGRESS=$(echo $JOB | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('Item', {}).get('progress', {}).get('N', '0'))" 2>/dev/null || echo "0")
    
    echo "  Attempt $ATTEMPT: $STATUS ($PROGRESS%)"
    
    if [ "$STATUS" = "COMPLETE" ]; then
        echo ""
        echo "========================================="
        echo "✅ Job Complete!"
        echo "========================================="
        echo ""
        
        # Get S3 key
        S3_KEY=$(echo $JOB | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('Item', {}).get('s3Key', {}).get('S', ''))" 2>/dev/null || echo "")
        FILE_SIZE=$(echo $JOB | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('Item', {}).get('fileSize', {}).get('N', '0'))" 2>/dev/null || echo "0")
        
        echo "S3 Bucket: $AUDIO_BUCKET"
        echo "S3 Key: $S3_KEY"
        echo "File Size: $FILE_SIZE bytes ($(echo "scale=2; $FILE_SIZE / 1024 / 1024" | bc) MB)"
        echo ""
        
        # Download file
        OUTPUT_FILE="downloaded-audio/${JOB_ID}.mp3"
        mkdir -p downloaded-audio
        
        echo "Downloading audio file..."
        aws s3 cp "s3://${AUDIO_BUCKET}/${S3_KEY}" "$OUTPUT_FILE" --region $REGION
        
        echo ""
        echo "========================================="
        echo "✅ Audio Downloaded!"
        echo "========================================="
        echo ""
        echo "File: $OUTPUT_FILE"
        echo ""
        
        # Get file info
        if [ -f "$OUTPUT_FILE" ]; then
            LOCAL_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
            echo "Local file size: $LOCAL_SIZE bytes ($(echo "scale=2; $LOCAL_SIZE / 1024 / 1024" | bc) MB)"
            echo ""
            echo "========================================="
            echo "🎧 Listen to the audio:"
            echo "========================================="
            echo ""
            echo "  open \"$OUTPUT_FILE\""
            echo ""
            echo "Check for:"
            echo "  - Audio clarity"
            echo "  - Bitrate quality"
            echo "  - All instruments audible"
            echo "  - No compression artifacts"
            echo ""
        fi
        
        exit 0
    fi
    
    if [ "$STATUS" = "FAILED" ]; then
        echo ""
        echo "========================================="
        echo "❌ Job Failed"
        echo "========================================="
        echo ""
        ERROR=$(echo $JOB | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('Item', {}).get('error', {}).get('S', 'Unknown error'))" 2>/dev/null || echo "Unknown error")
        echo "Error: $ERROR"
        echo ""
        exit 1
    fi
done

echo ""
echo "⏱️  Timeout after $MAX_ATTEMPTS attempts"
exit 1
