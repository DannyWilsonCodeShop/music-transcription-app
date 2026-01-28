#!/bin/bash

# Build and Deploy YouTube Downloader ECS Solution
echo "🚀 Building YouTube Downloader ECS Solution..."

# Set variables
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="youtube-downloader"
IMAGE_TAG="latest"

echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"

# 1. Build and push Docker image
echo "📦 Building Docker image..."
cd backend/functions-v2/youtube-downloader-ecs

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION

# Get ECR login token
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and tag image
docker build -t $ECR_REPO:$IMAGE_TAG .
docker tag $ECR_REPO:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG

# Push image
echo "📤 Pushing to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG

cd ../../..

# 2. Package Lambda function
echo "📦 Packaging Lambda function..."
cd backend/functions-v2/youtube-downloader-trigger
npm install
zip -r function.zip index.js package.json node_modules/
cd ../../..

echo "✅ Build complete!"
echo "🐳 Docker image: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"
echo "📦 Lambda package: backend/functions-v2/youtube-downloader-trigger/function.zip"
echo ""
echo "Next steps:"
echo "1. Create ECS task definition"
echo "2. Deploy Lambda function"
echo "3. Update Step Function to use new Lambda"