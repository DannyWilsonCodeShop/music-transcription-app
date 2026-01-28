#!/bin/bash

# Deploy Chord Detector with Madmom to ECS
# This script builds the Docker image and pushes it to ECR

set -e

echo "🎵 Deploying Chord Detector with Madmom to ECS..."

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="090130568474"
ECR_REPOSITORY="chordscout-chord-detector"
IMAGE_TAG="madmom-latest"
AWS_PROFILE="chordscout"

# Full image name
ECR_IMAGE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"

echo "📦 Building Docker image..."
cd backend/functions-v2/chord-detector-ecs
docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} .

echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} --profile ${AWS_PROFILE} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "🏷️  Tagging image..."
docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${ECR_IMAGE}

echo "⬆️  Pushing to ECR..."
docker push ${ECR_IMAGE}

echo "✅ Docker image pushed successfully!"
echo "📍 Image: ${ECR_IMAGE}"

# Update ECS task definition to use new image
echo ""
echo "🔄 Updating ECS task definition..."

# Get current task definition
TASK_FAMILY="ChordScout-ChordDetector-dev"
CURRENT_TASK_DEF=$(aws ecs describe-task-definition \
    --task-definition ${TASK_FAMILY} \
    --region ${AWS_REGION} \
    --profile ${AWS_PROFILE} \
    --query 'taskDefinition' \
    --output json)

# Create new task definition with updated image
NEW_TASK_DEF=$(echo ${CURRENT_TASK_DEF} | jq --arg IMAGE "${ECR_IMAGE}" '
    .containerDefinitions[0].image = $IMAGE |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)
')

# Register new task definition
echo "${NEW_TASK_DEF}" > /tmp/task-def.json
aws ecs register-task-definition \
    --cli-input-json file:///tmp/task-def.json \
    --region ${AWS_REGION} \
    --profile ${AWS_PROFILE} > /dev/null

echo "✅ ECS task definition updated!"
echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📊 To test the chord detector:"
echo "   1. Submit a job via API Gateway"
echo "   2. Monitor ECS task logs:"
echo "      aws logs tail /ecs/chordscout-chord-detector-dev --follow --profile ${AWS_PROFILE}"
echo ""
echo "🔍 Check ECS tasks:"
echo "   aws ecs list-tasks --cluster ChordScout-dev --region ${AWS_REGION} --profile ${AWS_PROFILE}"
