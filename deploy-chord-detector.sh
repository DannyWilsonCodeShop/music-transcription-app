#!/bin/bash

# ChordScout Chord Detector Deployment Script
# This script automates the deployment of the Basic Pitch chord detection Lambda

set -e

echo "🎵 ChordScout Chord Detector Deployment"
echo "========================================"
echo ""

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
FUNCTION_NAME="chordscout-chord-detector"
ROLE_NAME="ChordScoutChordDetectorRole"
ECR_REPO_NAME="chordscout-chord-detector"

# Check prerequisites
echo "✓ Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install it first."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon not running. Please start Docker."
    exit 1
fi

echo "✓ Prerequisites check passed"
echo ""

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"
echo "📋 Region: $AWS_REGION"
echo ""

# Step 1: Create ECR Repository
echo "📦 Step 1: Creating ECR repository..."
if aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION &> /dev/null; then
    echo "✓ ECR repository already exists"
else
    aws ecr create-repository \
        --repository-name $ECR_REPO_NAME \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true
    echo "✓ ECR repository created"
fi

ECR_REPO_URI=$(aws ecr describe-repositories \
    --repository-names $ECR_REPO_NAME \
    --region $AWS_REGION \
    --query 'repositories[0].repositoryUri' \
    --output text)

echo "✓ ECR Repository URI: $ECR_REPO_URI"
echo ""

# Step 2: Build and Push Docker Image
echo "🐳 Step 2: Building Docker image..."
cd backend/functions/chord-detector-ml

# Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REPO_URI

# Build image
echo "🔨 Building Docker image (this may take 5-10 minutes)..."
docker build --platform linux/amd64 -t $ECR_REPO_NAME .

# Tag and push
echo "📤 Pushing image to ECR..."
docker tag $ECR_REPO_NAME:latest $ECR_REPO_URI:latest
docker push $ECR_REPO_URI:latest

echo "✓ Docker image pushed successfully"
cd ../../..
echo ""

# Step 3: Create IAM Role
echo "🔑 Step 3: Creating IAM role..."
if aws iam get-role --role-name $ROLE_NAME &> /dev/null; then
    echo "✓ IAM role already exists"
else
    # Create trust policy
    cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file:///tmp/trust-policy.json

    # Attach basic execution policy
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    echo "✓ IAM role created"
    echo "⏳ Waiting 10 seconds for IAM role to propagate..."
    sleep 10
fi

ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
echo "✓ Role ARN: $ROLE_ARN"
echo ""

# Step 4: Create or Update Lambda Function
echo "⚡ Step 4: Creating/updating Lambda function..."
if aws lambda get-function --function-name $FUNCTION_NAME --region $AWS_REGION &> /dev/null; then
    echo "📝 Updating existing function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --image-uri $ECR_REPO_URI:latest \
        --region $AWS_REGION
    
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout 300 \
        --memory-size 3008 \
        --region $AWS_REGION
    
    echo "✓ Lambda function updated"
else
    echo "🆕 Creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --package-type Image \
        --code ImageUri=$ECR_REPO_URI:latest \
        --role $ROLE_ARN \
        --timeout 300 \
        --memory-size 3008 \
        --region $AWS_REGION
    
    echo "✓ Lambda function created"
fi

FUNCTION_ARN=$(aws lambda get-function \
    --function-name $FUNCTION_NAME \
    --region $AWS_REGION \
    --query 'Configuration.FunctionArn' \
    --output text)

echo "✓ Function ARN: $FUNCTION_ARN"
echo ""

# Step 5: Summary
echo "✅ Deployment Complete!"
echo "======================="
echo ""
echo "📋 Summary:"
echo "  - Function Name: $FUNCTION_NAME"
echo "  - Function ARN: $FUNCTION_ARN"
echo "  - Memory: 3008 MB"
echo "  - Timeout: 300 seconds"
echo "  - Region: $AWS_REGION"
echo ""
echo "💡 Next Steps:"
echo "  1. Update your transcribe worker with this ARN:"
echo "     export CHORD_DETECTOR_FUNCTION_ARN=$FUNCTION_ARN"
echo ""
echo "  2. Test the function:"
echo "     aws lambda invoke --function-name $FUNCTION_NAME \\"
echo "       --payload '{\"bucket\":\"YOUR-BUCKET\",\"key\":\"test.mp3\",\"jobId\":\"test\"}' \\"
echo "       response.json"
echo ""
echo "  3. View logs:"
echo "     aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
echo ""
echo "📊 Estimated Cost: ~$0.03-0.07 per transcription"
echo ""
