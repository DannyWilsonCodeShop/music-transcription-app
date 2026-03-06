#!/bin/bash

# Test Phase 4 Optimization
# Validates that bass-only mode skips stem separation

set -e

echo "=========================================="
echo "Phase 4 Optimization Test"
echo "=========================================="
echo ""

if [ -z "$1" ]; then
  echo "Usage: ./test-phase4-optimization.sh <audio-file-path>"
  echo "Example: ./test-phase4-optimization.sh \"public/04 That_s What I Like.m4a\""
  exit 1
fi

AUDIO_FILE="$1"
AWS_PROFILE="chordscout"
AWS_REGION="us-east-1"
BUCKET="chordscout-audio-temp-dev-090130568474"
TABLE="ChordScout-Jobs-V2-dev"

# Generate test job ID
JOB_ID="test-phase4-$(date +%s)"
FILENAME=$(basename "$AUDIO_FILE")

echo "Test Configuration:"
echo "  Job ID: $JOB_ID"
echo "  Audio File: $AUDIO_FILE"
echo "  Bucket: $BUCKET"
echo ""

# Step 1: Upload audio file
echo "Step 1: Uploading audio file to S3..."
aws s3 cp "$AUDIO_FILE" "s3://$BUCKET/uploads/$JOB_ID/$FILENAME" \
  --region $AWS_REGION \
  --profile $AWS_PROFILE

echo "✓ Audio uploaded"
echo ""

# Step 2: Create job record
echo "Step 2: Creating job record in DynamoDB..."
aws dynamodb put-item \
  --table-name $TABLE \
  --item "{
    \"jobId\": {\"S\": \"$JOB_ID\"},
    \"status\": {\"S\": \"PENDING\"},
    \"progress\": {\"N\": \"0\"},
    \"s3Key\": {\"S\": \"uploads/$JOB_ID/$FILENAME\"},
    \"filename\": {\"S\": \"$FILENAME\"},
    \"userId\": {\"S\": \"test-user\"},
    \"createdAt\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\"},
    \"updatedAt\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\"}
  }" \
  --region $AWS_REGION \
  --profile $AWS_PROFILE

echo "✓ Job record created"
echo ""

# Step 3: Trigger ECS task
echo "Step 3: Triggering ECS task..."
TASK_ARN=$(aws ecs run-task \
  --cluster ChordScout-dev \
  --task-definition chordscout-chord-detector-dev \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-0a1b2c3d4e5f6g7h8],securityGroups=[sg-0a1b2c3d4e5f6g7h8],assignPublicIp=ENABLED}" \
  --overrides "{
    \"containerOverrides\": [{
      \"name\": \"chordscout-chord-detector\",
      \"environment\": [
        {\"name\": \"JOB_ID\", \"value\": \"$JOB_ID\"},
        {\"name\": \"AUDIO_BUCKET\", \"value\": \"$BUCKET\"},
        {\"name\": \"AUDIO_KEY\", \"value\": \"uploads/$JOB_ID/$FILENAME\"}
      ]
    }]
  }" \
  --region $AWS_REGION \
  --profile $AWS_PROFILE \
  --query 'tasks[0].taskArn' \
  --output text)

echo "✓ ECS task started: $TASK_ARN"
echo ""

# Step 4: Monitor job progress
echo "Step 4: Monitoring job progress..."
echo "  Waiting for PENDING_MODE_SELECTION status..."
echo ""

START_TIME=$(date +%s)
MODE_SELECTION_TIME=0

while true; do
  sleep 5
  
  JOB_STATUS=$(aws dynamodb get-item \
    --table-name $TABLE \
    --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
    --region $AWS_REGION \
    --profile $AWS_PROFILE \
    --query 'Item.{status:status.S,progress:progress.N,message:statusMessage.S}' \
    --output json)
  
  STATUS=$(echo $JOB_STATUS | jq -r '.status')
  PROGRESS=$(echo $JOB_STATUS | jq -r '.progress')
  MESSAGE=$(echo $JOB_STATUS | jq -r '.message // "Processing..."')
  
  ELAPSED=$(($(date +%s) - START_TIME))
  echo "  [$ELAPSED s] Status: $STATUS ($PROGRESS%) - $MESSAGE"
  
  if [ "$STATUS" = "PENDING_MODE_SELECTION" ]; then
    MODE_SELECTION_TIME=$ELAPSED
    echo ""
    echo "✓ Reached PENDING_MODE_SELECTION in $MODE_SELECTION_TIME seconds"
    echo ""
    echo "OPTIMIZATION VALIDATION:"
    if [ $MODE_SELECTION_TIME -lt 120 ]; then
      echo "  ✓ PASS: Mode selection reached in < 2 minutes"
      echo "  ✓ Stem separation was SKIPPED (optimization working!)"
    else
      echo "  ✗ FAIL: Mode selection took > 2 minutes"
      echo "  ✗ Stem separation may have run (optimization not working)"
    fi
    echo ""
    break
  fi
  
  if [ "$STATUS" = "FAILED" ]; then
    echo ""
    echo "✗ Job failed"
    exit 1
  fi
  
  if [ $ELAPSED -gt 300 ]; then
    echo ""
    echo "✗ Timeout: Job did not reach PENDING_MODE_SELECTION in 5 minutes"
    echo "  This suggests stem separation is still running (optimization not working)"
    exit 1
  fi
done

# Step 5: Select bass-only mode
echo "Step 5: Selecting bass-only mode..."
aws dynamodb update-item \
  --table-name $TABLE \
  --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
  --update-expression "SET transcriptionMode = :mode, updatedAt = :updated" \
  --expression-attribute-values "{
    \":mode\": {\"S\": \"bass-only\"},
    \":updated\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\"}
  }" \
  --region $AWS_REGION \
  --profile $AWS_PROFILE

echo "✓ Bass-only mode selected"
echo ""

# Step 6: Monitor completion
echo "Step 6: Monitoring job completion..."
echo ""

while true; do
  sleep 10
  
  JOB_STATUS=$(aws dynamodb get-item \
    --table-name $TABLE \
    --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
    --region $AWS_REGION \
    --profile $AWS_PROFILE \
    --query 'Item.{status:status.S,progress:progress.N,message:statusMessage.S}' \
    --output json)
  
  STATUS=$(echo $JOB_STATUS | jq -r '.status')
  PROGRESS=$(echo $JOB_STATUS | jq -r '.progress')
  MESSAGE=$(echo $JOB_STATUS | jq -r '.message // "Processing..."')
  
  ELAPSED=$(($(date +%s) - START_TIME))
  echo "  [$ELAPSED s] Status: $STATUS ($PROGRESS%) - $MESSAGE"
  
  if [ "$STATUS" = "COMPLETED" ]; then
    TOTAL_TIME=$ELAPSED
    echo ""
    echo "✓ Job completed in $TOTAL_TIME seconds"
    echo ""
    echo "=========================================="
    echo "OPTIMIZATION RESULTS"
    echo "=========================================="
    echo ""
    echo "Total Processing Time: $TOTAL_TIME seconds (~$((TOTAL_TIME / 60)) minutes)"
    echo ""
    if [ $TOTAL_TIME -lt 300 ]; then
      echo "✓ EXCELLENT: Completed in < 5 minutes"
      echo "  Optimization is working perfectly!"
    elif [ $TOTAL_TIME -lt 600 ]; then
      echo "✓ GOOD: Completed in < 10 minutes"
      echo "  Significant improvement over 22 minutes"
    else
      echo "⚠ WARNING: Took > 10 minutes"
      echo "  Optimization may not be fully effective"
    fi
    echo ""
    echo "Expected Times:"
    echo "  - Before optimization: ~22 minutes"
    echo "  - After optimization: ~3-5 minutes"
    echo "  - Improvement: ~85% faster"
    echo ""
    break
  fi
  
  if [ "$STATUS" = "FAILED" ]; then
    echo ""
    echo "✗ Job failed"
    exit 1
  fi
  
  if [ $ELAPSED -gt 1800 ]; then
    echo ""
    echo "✗ Timeout: Job did not complete in 30 minutes"
    exit 1
  fi
done

echo "Test completed successfully!"
echo ""
echo "Job ID: $JOB_ID"
echo "View results: https://chordscout-pdfs-dev-090130568474.s3.amazonaws.com/pdfs/$JOB_ID.pdf"
echo ""
