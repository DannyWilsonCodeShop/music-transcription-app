#!/bin/bash

# ChordScout Full Pipeline Deployment Script
# Deploys the complete end-to-end transcription pipeline

set -e

echo "🎵 ChordScout Full Pipeline Deployment"
echo "======================================="
echo ""

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
ENVIRONMENT=${ENVIRONMENT:-dev}
STACK_NAME="ChordScout-Pipeline-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "✓ Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"
echo "📋 Region: $AWS_REGION"
echo "📋 Environment: $ENVIRONMENT"
echo ""

# Step 1: Create/Update OpenAI Secret
echo "🔐 Step 1: Setting up OpenAI API Key..."
SECRET_NAME="ChordScout-OpenAI-${ENVIRONMENT}"

if aws secretsmanager describe-secret --secret-id $SECRET_NAME --region $AWS_REGION &> /dev/null; then
    echo "✓ Secret already exists"
else
    echo "Creating new secret..."
    echo -e "${YELLOW}Please enter your OpenAI API Key:${NC}"
    read -s OPENAI_API_KEY
    
    aws secretsmanager create-secret \
        --name $SECRET_NAME \
        --description "OpenAI API Key for ChordScout" \
        --secret-string "{\"OPENAI_API_KEY\":\"$OPENAI_API_KEY\"}" \
        --region $AWS_REGION
    
    echo -e "${GREEN}✓ Secret created${NC}"
fi

OPENAI_SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id $SECRET_NAME \
    --region $AWS_REGION \
    --query ARN \
    --output text)

echo "✓ Secret ARN: $OPENAI_SECRET_ARN"
echo ""

# Step 2: Build and Push Chord Detector Image
echo "🐳 Step 2: Building Chord Detector Docker image..."

# Create ECR repository if it doesn't exist
ECR_REPO_NAME="chordscout-chord-detector"
if aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION &> /dev/null; then
    echo "✓ ECR repository exists"
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

# Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REPO_URI

# Build and push image
echo "🔨 Building Docker image..."
cd backend/functions/chord-detector-ml
docker build --platform linux/amd64 -t $ECR_REPO_NAME .
docker tag $ECR_REPO_NAME:latest $ECR_REPO_URI:latest
echo "📤 Pushing to ECR..."
docker push $ECR_REPO_URI:latest
cd ../../..

echo -e "${GREEN}✓ Docker image pushed${NC}"
echo ""

# Step 3: Create yt-dlp Lambda Layer
echo "📦 Step 3: Creating yt-dlp Lambda Layer..."

# Create temporary directory
mkdir -p /tmp/yt-dlp-layer/python
cd /tmp/yt-dlp-layer

# Install yt-dlp
pip install yt-dlp -t python/

# Create zip
zip -r yt-dlp.zip python/

# Create S3 bucket for layers if it doesn't exist
LAYER_BUCKET="chordscout-layers-${ENVIRONMENT}-${AWS_ACCOUNT_ID}"
if aws s3 ls "s3://${LAYER_BUCKET}" 2>&1 | grep -q 'NoSuchBucket'; then
    aws s3 mb "s3://${LAYER_BUCKET}" --region $AWS_REGION
fi

# Upload layer
aws s3 cp yt-dlp.zip "s3://${LAYER_BUCKET}/layers/yt-dlp.zip"

cd -
echo -e "${GREEN}✓ yt-dlp layer created${NC}"
echo ""

# Step 4: Deploy CloudFormation Stack
echo "☁️  Step 4: Deploying CloudFormation stack..."

aws cloudformation deploy \
    --template-file backend/infrastructure/cloudformation-template.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        Environment=$ENVIRONMENT \
        OpenAISecretArn=$OPENAI_SECRET_ARN \
        ChordDetectorImageUri=$ECR_REPO_URI:latest \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $AWS_REGION

echo -e "${GREEN}✓ CloudFormation stack deployed${NC}"
echo ""

# Step 5: Get Stack Outputs
echo "📊 Step 5: Retrieving stack outputs..."

AUDIO_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`AudioBucketName`].OutputValue' \
    --output text)

JOBS_TABLE=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`TranscriptionJobsTableName`].OutputValue' \
    --output text)

STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
    --output text)

echo "✓ Audio Bucket: $AUDIO_BUCKET"
echo "✓ Jobs Table: $JOBS_TABLE"
echo "✓ State Machine: $STATE_MACHINE_ARN"
echo ""

# Step 6: Create Amplify Backend Configuration
echo "⚡ Step 6: Updating Amplify configuration..."

cat > amplify_outputs.json <<EOF
{
  "version": "1",
  "storage": {
    "aws_region": "$AWS_REGION",
    "bucket_name": "$AUDIO_BUCKET"
  },
  "data": {
    "url": "https://mock-api.amplify.aws/graphql",
    "aws_region": "$AWS_REGION",
    "default_authorization_type": "API_KEY",
    "api_key": "mock-api-key-for-local-dev"
  },
  "auth": {
    "user_pool_id": "us-east-1_mock",
    "aws_region": "$AWS_REGION",
    "user_pool_client_id": "mock-client-id",
    "identity_pool_id": "us-east-1:mock-identity-pool"
  },
  "custom": {
    "stateMachineArn": "$STATE_MACHINE_ARN",
    "jobsTableName": "$JOBS_TABLE"
  }
}
EOF

echo -e "${GREEN}✓ Amplify configuration updated${NC}"
echo ""

# Step 7: Test the Pipeline
echo "🧪 Step 7: Testing the pipeline..."

TEST_JOB_ID="test-$(date +%s)"

cat > /tmp/test-input.json <<EOF
{
  "jobId": "$TEST_JOB_ID",
  "youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Test Song"
}
EOF

echo "Starting test execution..."
EXECUTION_ARN=$(aws stepfunctions start-execution \
    --state-machine-arn $STATE_MACHINE_ARN \
    --name $TEST_JOB_ID \
    --input file:///tmp/test-input.json \
    --region $AWS_REGION \
    --query 'executionArn' \
    --output text)

echo "✓ Execution started: $EXECUTION_ARN"
echo ""

# Summary
echo "✅ Deployment Complete!"
echo "======================="
echo ""
echo "📋 Summary:"
echo "  - Stack Name: $STACK_NAME"
echo "  - Audio Bucket: $AUDIO_BUCKET"
echo "  - Jobs Table: $JOBS_TABLE"
echo "  - State Machine: $STATE_MACHINE_ARN"
echo "  - Test Execution: $EXECUTION_ARN"
echo ""
echo "💡 Next Steps:"
echo "  1. Monitor test execution:"
echo "     aws stepfunctions describe-execution --execution-arn $EXECUTION_ARN"
echo ""
echo "  2. View execution history:"
echo "     aws stepfunctions get-execution-history --execution-arn $EXECUTION_ARN"
echo ""
echo "  3. Check CloudWatch Logs:"
echo "     aws logs tail /aws/lambda/chordscout-youtube-downloader-${ENVIRONMENT} --follow"
echo ""
echo "  4. Update your frontend to use the State Machine ARN"
echo ""
echo "📊 Estimated Cost: ~\$0.10-0.15 per transcription"
echo ""
