#!/bin/bash

# Build and push optimized v3.0 Docker image
# Phase 4: Performance optimization - conditional stem separation

set -e

AWS_PROFILE=chordscout
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=090130568474
ECR_REPO=chordscout-chord-detector-v3-dev
IMAGE_TAG=v3.0-optimized

echo "========================================="
echo "Building Optimized v3.0 Docker Image"
echo "========================================="
echo "Profile: $AWS_PROFILE"
echo "Region: $AWS_REGION"
echo "Repository: $ECR_REPO"
echo "Tag: $IMAGE_TAG"
echo ""

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build image for linux/amd64 (ECS Fargate requirement)
# Must build from parent directory to include simple-pipeline
echo ""
echo "Building Docker image..."
cd ../..
docker build \
  --platform linux/amd64 \
  -t $ECR_REPO:$IMAGE_TAG \
  -t $ECR_REPO:latest \
  -f bass-transcription-pipeline/bass-transcription-ecs/Dockerfile \
  .
cd bass-transcription-pipeline/bass-transcription-ecs

# Tag for ECR
echo ""
echo "Tagging image for ECR..."
docker tag $ECR_REPO:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG
docker tag $ECR_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# Push to ECR
echo ""
echo "Pushing image to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

echo ""
echo "========================================="
echo "✓ Optimized v3.0 Image Deployed"
echo "========================================="
echo "Image: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"
echo ""
echo "Optimization: Mode selection before stem separation"
echo "Expected performance:"
echo "  - Bass-only: ~3 minutes (was 22 min) - 85% faster"
echo "  - Multi-stem: ~15 minutes (was 22 min) - 32% faster"
echo ""
echo "Next steps:"
echo "1. Update ECS task definition to use this image"
echo "2. Deploy to development environment"
echo "3. Test with bass-only and multi-stem modes"
