#!/bin/bash
# Deploy ECS YouTube Downloader

set -e

export AWS_PROFILE=production
REGION="us-east-1"
STACK_NAME="music-transcription-ecs"
ENVIRONMENT="test"

# Get existing resources
AUDIO_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name music-transcription-pipeline \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`AudioBucket`].OutputValue' \
  --output text)

JOBS_TABLE=$(aws cloudformation describe-stacks \
  --stack-name music-transcription-pipeline \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`JobsTable`].OutputValue' \
  --output text)

echo "========================================="
echo "Deploying ECS Infrastructure"
echo "========================================="
echo "Stack: $STACK_NAME"
echo "Audio Bucket: $AUDIO_BUCKET"
echo "Jobs Table: $JOBS_TABLE"
echo "========================================="
echo ""

# Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file cloudformation-ecs.yaml \
  --stack-name $STACK_NAME \
  --parameter-overrides \
      Environment=$ENVIRONMENT \
      AudioBucket=$AUDIO_BUCKET \
      JobsTable=$JOBS_TABLE \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo ""
echo "========================================="
echo "✅ ECS Infrastructure Deployed!"
echo "========================================="
echo ""

# Get outputs
TRIGGER_FUNCTION=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`TriggerFunction`].OutputValue' \
  --output text)

echo "Trigger Function: $TRIGGER_FUNCTION"
echo ""
echo "Next: Update API Gateway to use this Lambda function"
echo ""
