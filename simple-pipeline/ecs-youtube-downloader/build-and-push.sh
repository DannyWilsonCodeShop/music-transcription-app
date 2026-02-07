#!/bin/bash
# Build and push Docker image to ECR

set -e

export AWS_PROFILE=production
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
REPO_NAME="music-transcription-youtube-downloader"
IMAGE_TAG="latest"

echo "========================================="
echo "Building and Pushing Docker Image"
echo "========================================="
echo "Account: $ACCOUNT_ID"
echo "Region: $REGION"
echo "Repository: $REPO_NAME"
echo "========================================="
echo ""

# Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository..."
aws ecr describe-repositories --repository-names $REPO_NAME --region $REGION 2>/dev/null || \
  aws ecr create-repository --repository-name $REPO_NAME --region $REGION

# Get ECR login
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build image
echo "🔨 Building Docker image..."
docker build -t $REPO_NAME:$IMAGE_TAG .

# Tag image
echo "🏷️  Tagging image..."
docker tag $REPO_NAME:$IMAGE_TAG $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG

# Push image
echo "☁️  Pushing to ECR..."
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG

echo ""
echo "========================================="
echo "✅ Image pushed successfully!"
echo "========================================="
echo ""
echo "Image URI:"
echo "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG"
echo ""
