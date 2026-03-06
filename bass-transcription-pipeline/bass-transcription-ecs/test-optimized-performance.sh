#!/bin/bash

# Test optimized v3.0 performance
# Validates that bass-only mode skips stem separation

set -e

AWS_PROFILE=chordscout
AWS_REGION=us-east-1
JOBS_TABLE=ChordScout-Jobs-V2-dev

echo "========================================="
echo "Testing Optimized v3.0 Performance"
echo "========================================="
echo ""

# Test 1: Bass-only mode (should be fast - ~3 minutes)
echo "Test 1: Bass-only mode (optimized)"
echo "Expected: ~3 minutes (stem separation skipped)"
echo ""

JOB_ID="test-optimized-bass-only-$(date +%s)"
echo "Job ID: $JOB_ID"
echo ""

# Upload test file
echo "Uploading test audio..."
aws s3 cp "public/04 That_s What I Like.m4a" \
  "s3://chordscout-audio-temp-dev-090130568474/uploads/$JOB_ID/audio.m4a" \
  --profile $AWS_PROFILE \
  --region $AWS_REGION

# Create job record
echo "Creating job record..."
aws dynamodb put-item \
  --table-name $JOBS_TABLE \
  --item "{
    \"jobId\": {\"S\": \"$JOB_ID\"},
    \"status\": {\"S\": \"PENDING\"},
    \"progress\": {\"N\": \"0\"},
    \"createdAt\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%S.%6NZ)\"},
    \"updatedAt\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%S.%6NZ)\"},
    \"userId\": {\"S\": \"test\"},
    \"filename\": {\"S\": \"audio.m4a\"},
    \"s3Key\": {\"S\": \"uploads/$JOB_ID/audio.m4a\"}
  }" \
  --profile $AWS_PROFILE \
  --region $AWS_REGION

# Trigger ECS task
echo "Triggering ECS task..."
TASK_ARN=$(aws ecs run-task \
  --cluster ChordScout-dev \
  --task-definition chordscout-chord-detector-dev:17 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-0a1b2c3d4e5f6g7h8],securityGroups=[sg-0a1b2c3d4e5f6g7h8],assignPublicIp=ENABLED}" \
  --overrides "{
    \"containerOverrides\": [{
      \"name\": \"chord-detector\",
      \"environment\": [
        {\"name\": \"JOB_ID\", \"value\": \"$JOB_ID\"},
        {\"name\": \"AUDIO_BUCKET\", \"value\": \"chordscout-audio-temp-dev-090130568474\"},
        {\"name\": \"AUDIO_KEY\", \"value\": \"uploads/$JOB_ID/audio.m4a\"}
      ]
    }]
  }" \
  --profile $AWS_PROFILE \
  --region $AWS_REGION \
  --query 'tasks[0].taskArn' \
  --output text)

echo "Task ARN: $TASK_ARN"
echo ""

# Monitor job progress
echo "Monitoring job progress..."
echo "Waiting for PENDING_MODE_SELECTION status..."
echo ""

START_TIME=$(date +%s)

while true; do
  STATUS=$(aws dynamodb get-item \
    --table-name $JOBS_TABLE \
    --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
    --query 'Item.status.S' \
    --output text \
    --profile $AWS_PROFILE \
    --region $AWS_REGION)
  
  PROGRESS=$(aws dynamodb get-item \
    --table-name $JOBS_TABLE \
    --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
    --query 'Item.progress.N' \
    --output text \
    --profile $AWS_PROFILE \
    --region $AWS_REGION)
  
  ELAPSED=$(($(date +%s) - START_TIME))
  
  echo "[$ELAPSED s] Status: $STATUS, Progress: $PROGRESS%"
  
  if [ "$STATUS" = "PENDING_MODE_SELECTION" ]; then
    echo ""
    echo "✓ Reached mode selection in $ELAPSED seconds"
    echo ""
    
    # Confirm bass-only mode
    echo "Confirming bass-only mode..."
    aws dynamodb update-item \
      --table-name $JOBS_TABLE \
      --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
      --update-expression "SET transcriptionMode = :mode, updatedAt = :updated" \
      --expression-attribute-values "{
        \":mode\": {\"S\": \"bass-only\"},
        \":updated\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%S.%6NZ)\"}
      }" \
      --profile $AWS_PROFILE \
      --region $AWS_REGION
    
    echo "✓ Mode confirmed: bass-only"
    echo ""
    echo "Waiting for completion..."
    break
  fi
  
  if [ "$STATUS" = "FAILED" ]; then
    echo ""
    echo "✗ Job failed"
    exit 1
  fi
  
  sleep 5
done

# Wait for completion
while true; do
  STATUS=$(aws dynamodb get-item \
    --table-name $JOBS_TABLE \
    --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
    --query 'Item.status.S' \
    --output text \
    --profile $AWS_PROFILE \
    --region $AWS_REGION)
  
  PROGRESS=$(aws dynamodb get-item \
    --table-name $JOBS_TABLE \
    --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
    --query 'Item.progress.N' \
    --output text \
    --profile $AWS_PROFILE \
    --region $AWS_REGION)
  
  ELAPSED=$(($(date +%s) - START_TIME))
  
  echo "[$ELAPSED s] Status: $STATUS, Progress: $PROGRESS%"
  
  if [ "$STATUS" = "COMPLETED" ]; then
    echo ""
    echo "========================================="
    echo "✓ Test Complete"
    echo "========================================="
    echo "Total time: $ELAPSED seconds (~$((ELAPSED / 60)) minutes)"
    echo ""
    
    # Get processing metrics
    echo "Processing metrics:"
    aws dynamodb get-item \
      --table-name $JOBS_TABLE \
      --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
      --query 'Item.processingMetrics.M' \
      --output json \
      --profile $AWS_PROFILE \
      --region $AWS_REGION | jq '.'
    
    echo ""
    echo "Expected: ~3 minutes for bass-only (stem separation skipped)"
    echo "Previous: ~22 minutes (with stem separation)"
    
    if [ $ELAPSED -lt 300 ]; then
      echo ""
      echo "✓ OPTIMIZATION SUCCESSFUL: Completed in under 5 minutes"
    else
      echo ""
      echo "⚠ WARNING: Took longer than expected"
    fi
    
    break
  fi
  
  if [ "$STATUS" = "FAILED" ]; then
    echo ""
    echo "✗ Job failed"
    exit 1
  fi
  
  sleep 10
done

echo ""
echo "Job ID: $JOB_ID"
echo "View results: https://chordscout-pdfs-dev-090130568474.s3.amazonaws.com/pdfs/$JOB_ID.pdf"
