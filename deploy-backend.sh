#!/bin/bash

# ChordScout V2 - Backend Infrastructure Deployment Script
# This script deploys the complete backend infrastructure to AWS

set -e  # Exit on error

echo "🚀 ChordScout V2 - Backend Deployment"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create a .env file with:"
    echo "  DEEPGRAM_API_KEY=your_key"
    echo "  APIFY_API_TOKEN=your_token"
    exit 1
fi

# Load environment variables
echo "📋 Loading environment variables..."
export $(grep -v '^#' .env | xargs)

# Check required variables
if [ -z "$DEEPGRAM_API_KEY" ]; then
    echo -e "${RED}❌ Error: DEEPGRAM_API_KEY not set in .env${NC}"
    exit 1
fi

if [ -z "$APIFY_API_TOKEN" ]; then
    echo -e "${RED}❌ Error: APIFY_API_TOKEN not set in .env${NC}"
    exit 1
fi

# Get AWS account ID and region
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=${AWS_REGION:-us-east-1}
export ENVIRONMENT=${ENVIRONMENT:-dev}

echo -e "${GREEN}✓${NC} AWS Account ID: $AWS_ACCOUNT_ID"
echo -e "${GREEN}✓${NC} AWS Region: $AWS_REGION"
echo -e "${GREEN}✓${NC} Environment: $ENVIRONMENT"
echo ""

# Check if stack already exists
STACK_NAME="chordscout-v2-$ENVIRONMENT"
echo "🔍 Checking if stack '$STACK_NAME' exists..."

if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION &> /dev/null; then
    echo -e "${YELLOW}⚠️  Stack already exists. Updating...${NC}"
    OPERATION="update-stack"
    WAIT_COMMAND="stack-update-complete"
else
    echo -e "${GREEN}✓${NC} Stack does not exist. Creating..."
    OPERATION="create-stack"
    WAIT_COMMAND="stack-create-complete"
fi

# Deploy CloudFormation stack
echo ""
echo "📦 Deploying CloudFormation stack..."
echo "   Template: backend/infrastructure-v2/cloudformation-ecs-architecture.yaml"
echo "   Stack Name: $STACK_NAME"
echo ""

aws cloudformation $OPERATION \
  --stack-name $STACK_NAME \
  --template-body file://backend/infrastructure-v2/cloudformation-ecs-architecture.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
    ParameterKey=DeepgramApiKey,ParameterValue=$DEEPGRAM_API_KEY \
    ParameterKey=ChordDetectorImageUri,ParameterValue=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/chordscout-chord-detector:latest \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region $AWS_REGION

echo ""
echo "⏳ Waiting for stack $OPERATION to complete..."
echo "   This may take 5-10 minutes..."
echo ""

aws cloudformation wait $WAIT_COMMAND \
  --stack-name $STACK_NAME \
  --region $AWS_REGION

# Check if deployment was successful
STACK_STATUS=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].StackStatus' \
  --output text \
  --region $AWS_REGION)

if [[ "$STACK_STATUS" == *"COMPLETE"* ]]; then
    echo -e "${GREEN}✓ Stack deployment successful!${NC}"
else
    echo -e "${RED}❌ Stack deployment failed with status: $STACK_STATUS${NC}"
    exit 1
fi

# Get outputs
echo ""
echo "📊 Stack Outputs:"
echo "================="

API_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text \
  --region $AWS_REGION)

JOBS_TABLE=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`JobsTableName`].OutputValue' \
  --output text \
  --region $AWS_REGION)

AUDIO_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`AudioBucketName`].OutputValue' \
  --output text \
  --region $AWS_REGION)

PDF_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`PdfBucketName`].OutputValue' \
  --output text \
  --region $AWS_REGION)

echo "API Gateway URL: $API_URL"
echo "DynamoDB Table: $JOBS_TABLE"
echo "Audio Bucket: $AUDIO_BUCKET"
echo "PDF Bucket: $PDF_BUCKET"
echo ""

# Update frontend configuration
echo "📝 Updating frontend configuration..."

if [ -f "src/services/transcriptionService.ts" ]; then
    # Backup original file
    cp src/services/transcriptionService.ts src/services/transcriptionService.ts.bak
    
    # Update API URL
    sed -i.tmp "s|const API_BASE_URL = '.*';|const API_BASE_URL = '$API_URL';|" src/services/transcriptionService.ts
    rm src/services/transcriptionService.ts.tmp
    
    echo -e "${GREEN}✓${NC} Updated API_BASE_URL in src/services/transcriptionService.ts"
else
    echo -e "${YELLOW}⚠️  Could not find src/services/transcriptionService.ts${NC}"
fi

# Deploy Lambda function code
echo ""
echo "📦 Deploying Lambda function code..."
echo ""

LAMBDA_FUNCTIONS=(
    "create-job"
    "get-job-status"
    "youtube-downloader"
    "lyrics-transcriber"
    "chord-detector-trigger"
    "pdf-generator"
)

for FUNC in "${LAMBDA_FUNCTIONS[@]}"; do
    FUNC_DIR="backend/functions-v2/$FUNC"
    
    if [ -d "$FUNC_DIR" ]; then
        echo "   Deploying $FUNC..."
        
        cd "$FUNC_DIR"
        
        # Create zip file
        if [ -f "function.zip" ]; then
            rm function.zip
        fi
        
        zip -q -r function.zip . -x "*.git*" -x "*node_modules*" -x "*.pyc" -x "__pycache__/*"
        
        # Update Lambda function
        FUNC_NAME="chordscout-v2-$FUNC-$ENVIRONMENT"
        
        if aws lambda get-function --function-name $FUNC_NAME --region $AWS_REGION &> /dev/null; then
            aws lambda update-function-code \
              --function-name $FUNC_NAME \
              --zip-file fileb://function.zip \
              --region $AWS_REGION \
              --output text > /dev/null
            
            echo -e "      ${GREEN}✓${NC} Updated $FUNC_NAME"
        else
            echo -e "      ${YELLOW}⚠️  Function $FUNC_NAME not found (will be created by CloudFormation)${NC}"
        fi
        
        cd - > /dev/null
    else
        echo -e "      ${YELLOW}⚠️  Directory $FUNC_DIR not found${NC}"
    fi
done

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo "🧪 Test your API:"
echo "   curl -X POST $API_URL/jobs \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"youtubeUrl\": \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}'"
echo ""
echo "📊 Monitor logs:"
echo "   aws logs tail /aws/lambda/chordscout-v2-create-job-$ENVIRONMENT --follow"
echo ""
echo "🌐 Frontend:"
echo "   npm run dev"
echo ""
