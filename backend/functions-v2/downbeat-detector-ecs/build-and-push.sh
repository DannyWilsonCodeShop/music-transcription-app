#!/bin/bash
set -e

echo "Building and pushing downbeat-detector-ecs Docker image..."

# Configuration
AWS_PROFILE=chordscout
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=090130568474
ECR_REPO=chordscout-downbeat-detector
IMAGE_TAG=latest

# Create ECR repository if it doesn't exist
echo "Ensuring ECR repository exists..."
aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION --profile $AWS_PROFILE 2>/dev/null || \
  aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION --profile $AWS_PROFILE

# Copy simple-pipeline to build context
echo "Copying simple-pipeline to build context..."
rm -rf simple-pipeline
cp -r ../../../simple-pipeline .

# Build Docker image
echo "Building Docker image..."
docker build -t $ECR_REPO:$IMAGE_TAG .

# Tag for ECR
echo "Tagging image for ECR..."
docker tag $ECR_REPO:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Push to ECR
echo "Pushing image to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG

# Clean up
echo "Cleaning up..."
rm -rf simple-pipeline

echo "✓ Docker image built and pushed successfully!"
echo "Image: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"
