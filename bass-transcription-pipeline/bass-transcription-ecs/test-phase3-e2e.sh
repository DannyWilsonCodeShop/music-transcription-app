#!/bin/bash
# Phase 3 End-to-End Test
# Tests complete workflow with song identification, lyrics, and key confirmation

set -e

export AWS_PROFILE=chordscout
REGION="us-east-1"
JOBS_TABLE="ChordScout-Jobs-V2-dev"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Phase 3 End-to-End Test"
echo "=========================================="
echo ""

# Check for test audio file
if [ -z "$1" ]; then
  echo -e "${YELLOW}Usage: $0 <path-to-audio-file>${NC}"
  echo ""
  echo "Example:"
  echo "  $0 public/test-song.m4a"
  echo ""
  echo "Recommended test files:"
  echo "  • public/04 That_s What I Like.m4a (Bruno Mars - known song)"
  echo "  • public/08 PLASTIC OFF THE SOFA.m4a (Beyoncé - known song)"
  exit 1
fi

AUDIO_FILE="$1"

if [ ! -f "$AUDIO_FILE" ]; then
  echo -e "${RED}Error: Audio file not found: $AUDIO_FILE${NC}"
  exit 1
fi

FILENAME=$(basename "$AUDIO_FILE")
echo -e "${BLUE}Test Audio: $FILENAME${NC}"
echo ""

# Generate unique job ID
JOB_ID="test-phase3-$(date +%s)"
S3_BUCKET="chordscout-audio-temp-dev-090130568474"
S3_KEY="test/$JOB_ID/$FILENAME"

echo "Step 1: Uploading audio to S3..."
aws s3 cp "$AUDIO_FILE" "s3://$S3_BUCKET/$S3_KEY" --region $REGION
echo -e "${GREEN}✓ Uploaded to s3://$S3_BUCKET/$S3_KEY${NC}"
echo ""

# Create job in DynamoDB
echo "Step 2: Creating job in DynamoDB..."
aws dynamodb put-item \
  --table-name $JOBS_TABLE \
  --region $REGION \
  --item "{
    \"jobId\": {\"S\": \"$JOB_ID\"},
    \"status\": {\"S\": \"CREATED\"},
    \"progress\": {\"N\": \"0\"},
    \"createdAt\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"},
    \"updatedAt\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"},
    \"audioUrl\": {\"S\": \"s3://$S3_BUCKET/$S3_KEY\"},
    \"fileName\": {\"S\": \"$FILENAME\"}
  }" > /dev/null

echo -e "${GREEN}✓ Job created: $JOB_ID${NC}"
echo ""

# Trigger ECS task via Lambda
echo "Step 3: Triggering ECS task..."
LAMBDA_RESPONSE=$(aws lambda invoke \
  --function-name chordscout-v2-chord-detector-trigger-dev \
  --region $REGION \
  --payload "{\"jobId\":\"$JOB_ID\",\"bucket\":\"$S3_BUCKET\",\"key\":\"$S3_KEY\"}" \
  --cli-binary-format raw-in-base64-out \
  /tmp/lambda-response.json 2>&1)

if [ $? -eq 0 ]; then
  TASK_ARN=$(cat /tmp/lambda-response.json | jq -r '.body.taskArn // empty')
  if [ ! -z "$TASK_ARN" ]; then
    echo -e "${GREEN}✓ ECS task started${NC}"
    echo "  Task ARN: $TASK_ARN"
  else
    echo -e "${GREEN}✓ Lambda invoked${NC}"
  fi
else
  echo -e "${RED}✗ Lambda invocation failed${NC}"
  echo "$LAMBDA_RESPONSE"
  exit 1
fi
echo ""

# Monitor job progress
echo "Step 4: Monitoring job progress..."
echo -e "${YELLOW}This may take 3-8 minutes depending on transcription mode...${NC}"
echo ""

LAST_STATUS=""
LAST_PROGRESS=0
START_TIME=$(date +%s)
TIMEOUT=900  # 15 minutes

while true; do
  # Get job status
  JOB_DATA=$(aws dynamodb get-item \
    --table-name $JOBS_TABLE \
    --region $REGION \
    --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
    --output json)
  
  STATUS=$(echo $JOB_DATA | jq -r '.Item.status.S // "UNKNOWN"')
  PROGRESS=$(echo $JOB_DATA | jq -r '.Item.progress.N // "0"')
  
  # Print status updates
  if [ "$STATUS" != "$LAST_STATUS" ] || [ "$PROGRESS" != "$LAST_PROGRESS" ]; then
    TIMESTAMP=$(date +%H:%M:%S)
    echo "[$TIMESTAMP] Status: $STATUS | Progress: $PROGRESS%"
    LAST_STATUS="$STATUS"
    LAST_PROGRESS="$PROGRESS"
  fi
  
  # Check for completion
  if [ "$STATUS" = "COMPLETED" ]; then
    echo ""
    echo -e "${GREEN}✓ Job completed successfully!${NC}"
    break
  fi
  
  if [ "$STATUS" = "FAILED" ]; then
    echo ""
    echo -e "${RED}✗ Job failed${NC}"
    ERROR_MSG=$(echo $JOB_DATA | jq -r '.Item.errorMessage.S // "Unknown error"')
    echo "Error: $ERROR_MSG"
    exit 1
  fi
  
  # Check for user confirmation states
  if [ "$STATUS" = "PENDING_MODE_SELECTION" ]; then
    echo ""
    echo -e "${YELLOW}⚠ Waiting for transcription mode selection${NC}"
    echo "  In production, user would select mode via UI"
    echo "  Auto-selecting 'bass-only' for test..."
    
    # Simulate user confirmation
    aws dynamodb update-item \
      --table-name $JOBS_TABLE \
      --region $REGION \
      --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
      --update-expression "SET transcriptionMode = :mode, updatedAt = :updated" \
      --expression-attribute-values "{
        \":mode\": {\"S\": \"bass-only\"},
        \":updated\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}
      }" > /dev/null
    
    echo -e "${GREEN}✓ Mode selected: bass-only${NC}"
    echo ""
  fi
  
  if [ "$STATUS" = "PENDING_KEY_CONFIRMATION" ]; then
    echo ""
    echo -e "${YELLOW}⚠ Waiting for key confirmation${NC}"
    
    # Get detected key
    DETECTED_KEY=$(echo $JOB_DATA | jq -r '.Item.detectedKey.S // "C major"')
    KEY_CONFIDENCE=$(echo $JOB_DATA | jq -r '.Item.keyConfidence.N // "0"')
    
    echo "  Detected Key: $DETECTED_KEY (confidence: $KEY_CONFIDENCE%)"
    echo "  In production, user would confirm or change key via UI"
    echo "  Auto-confirming detected key for test..."
    
    # Simulate user confirmation
    aws dynamodb update-item \
      --table-name $JOBS_TABLE \
      --region $REGION \
      --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
      --update-expression "SET confirmedKey = :key, updatedAt = :updated" \
      --expression-attribute-values "{
        \":key\": {\"S\": \"$DETECTED_KEY\"},
        \":updated\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}
      }" > /dev/null
    
    echo -e "${GREEN}✓ Key confirmed: $DETECTED_KEY${NC}"
    echo ""
  fi
  
  # Check timeout
  CURRENT_TIME=$(date +%s)
  ELAPSED=$((CURRENT_TIME - START_TIME))
  if [ $ELAPSED -gt $TIMEOUT ]; then
    echo ""
    echo -e "${RED}✗ Timeout after $TIMEOUT seconds${NC}"
    exit 1
  fi
  
  sleep 5
done

# Retrieve final job data
echo ""
echo "Step 5: Retrieving results..."
FINAL_JOB=$(aws dynamodb get-item \
  --table-name $JOBS_TABLE \
  --region $REGION \
  --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
  --output json)

echo ""
echo "=========================================="
echo "Phase 3 Test Results"
echo "=========================================="
echo ""

# Song Metadata
SONG_TITLE=$(echo $FINAL_JOB | jq -r '.Item.songMetadata.M.title.S // "Unknown"')
SONG_ARTIST=$(echo $FINAL_JOB | jq -r '.Item.songMetadata.M.artist.S // "Unknown"')
SONG_ALBUM=$(echo $FINAL_JOB | jq -r '.Item.songMetadata.M.album.S // "Unknown"')

echo "Song Identification:"
if [ "$SONG_TITLE" != "Unknown" ]; then
  echo -e "  ${GREEN}✓ Title: $SONG_TITLE${NC}"
  echo -e "  ${GREEN}✓ Artist: $SONG_ARTIST${NC}"
  echo -e "  ${GREEN}✓ Album: $SONG_ALBUM${NC}"
else
  echo -e "  ${YELLOW}⚠ Song not identified (using filename)${NC}"
fi
echo ""

# Lyrics
HAS_LYRICS=$(echo $FINAL_JOB | jq -r '.Item.lyrics.M.sections // empty' | wc -l)
if [ $HAS_LYRICS -gt 0 ]; then
  LYRICS_SOURCE=$(echo $FINAL_JOB | jq -r '.Item.lyrics.M.source.S // "Unknown"')
  echo -e "Lyrics: ${GREEN}✓ Fetched from $LYRICS_SOURCE${NC}"
else
  echo -e "Lyrics: ${YELLOW}⚠ Not available${NC}"
fi
echo ""

# Key Detection
DETECTED_KEY=$(echo $FINAL_JOB | jq -r '.Item.detectedKey.S // "Unknown"')
CONFIRMED_KEY=$(echo $FINAL_JOB | jq -r '.Item.confirmedKey.S // "Unknown"')
KEY_CONFIDENCE=$(echo $FINAL_JOB | jq -r '.Item.keyConfidence.N // "0"')

echo "Key Detection:"
echo -e "  ${GREEN}✓ Detected: $DETECTED_KEY (confidence: $KEY_CONFIDENCE%)${NC}"
echo -e "  ${GREEN}✓ Confirmed: $CONFIRMED_KEY${NC}"
echo ""

# Transcription Mode
TRANSCRIPTION_MODE=$(echo $FINAL_JOB | jq -r '.Item.transcriptionMode.S // "bass-only"')
echo "Transcription Mode: $TRANSCRIPTION_MODE"
echo ""

# PDF Output
PDF_URL=$(echo $FINAL_JOB | jq -r '.Item.pdfUrl.S // empty')
if [ ! -z "$PDF_URL" ]; then
  echo -e "PDF Output: ${GREEN}✓ Generated${NC}"
  echo "  URL: $PDF_URL"
else
  echo -e "PDF Output: ${RED}✗ Not generated${NC}"
fi
echo ""

# Processing Time
CREATED_AT=$(echo $FINAL_JOB | jq -r '.Item.createdAt.S')
UPDATED_AT=$(echo $FINAL_JOB | jq -r '.Item.updatedAt.S')
CREATED_TS=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$CREATED_AT" +%s 2>/dev/null || echo "0")
UPDATED_TS=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$UPDATED_AT" +%s 2>/dev/null || echo "0")
PROCESSING_TIME=$((UPDATED_TS - CREATED_TS))

if [ $PROCESSING_TIME -gt 0 ]; then
  MINUTES=$((PROCESSING_TIME / 60))
  SECONDS=$((PROCESSING_TIME % 60))
  echo "Processing Time: ${MINUTES}m ${SECONDS}s"
fi
echo ""

echo "=========================================="
echo -e "${GREEN}Phase 3 End-to-End Test Complete!${NC}"
echo "=========================================="
echo ""
echo "Job ID: $JOB_ID"
echo ""
echo "To view full job data:"
echo "  aws dynamodb get-item --table-name $JOBS_TABLE --key '{\"jobId\": {\"S\": \"$JOB_ID\"}}' --region $REGION"
echo ""
