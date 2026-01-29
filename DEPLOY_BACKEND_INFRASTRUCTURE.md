# Deploy Backend Infrastructure - ChordScout V2

## Issue Identified

The frontend is trying to connect to the API, but the backend infrastructure (Lambda functions, Step Functions, DynamoDB, ECS tasks) has **not been deployed yet**.

## Current Status

✅ **Deployed:**
- Frontend (Amplify app)
- Docker images pushed to ECR

❌ **Not Deployed:**
- Lambda functions (create-job, get-job-status, youtube-downloader, etc.)
- Step Functions workflow
- DynamoDB jobs table
- API Gateway endpoints
- ECS cluster and task definitions
- VPC and networking

## Deployment Steps

### Prerequisites

1. **AWS Credentials** - Already configured ✅
2. **Deepgram API Key** - Check `.env` file
3. **Apify API Token** - Check `.env` file
4. **Docker Images** - Already pushed to ECR ✅

### Step 1: Set Environment Variables

```bash
# Load from .env file
export DEEPGRAM_API_KEY=$(grep DEEPGRAM_API_KEY .env | cut -d '=' -f2)
export APIFY_API_TOKEN=$(grep APIFY_API_TOKEN .env | cut -d '=' -f2)
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1
```

### Step 2: Deploy CloudFormation Stack

The main infrastructure template is:
`backend/infrastructure-v2/cloudformation-ecs-architecture.yaml`

**Deploy command:**

```bash
aws cloudformation create-stack \
  --stack-name chordscout-v2-dev \
  --template-body file://backend/infrastructure-v2/cloudformation-ecs-architecture.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=DeepgramApiKey,ParameterValue=$DEEPGRAM_API_KEY \
    ParameterKey=ChordDetectorImageUri,ParameterValue=$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

**Monitor deployment:**

```bash
aws cloudformation wait stack-create-complete \
  --stack-name chordscout-v2-dev \
  --region us-east-1

# Check status
aws cloudformation describe-stacks \
  --stack-name chordscout-v2-dev \
  --query 'Stacks[0].StackStatus' \
  --region us-east-1
```

### Step 3: Get API Gateway URL

After deployment completes, get the API Gateway URL:

```bash
aws cloudformation describe-stacks \
  --stack-name chordscout-v2-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text \
  --region us-east-1
```

### Step 4: Update Frontend Configuration

Update `src/services/transcriptionService.ts` with the new API URL:

```typescript
const API_BASE_URL = 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev';
```

### Step 5: Deploy Lambda Functions

The CloudFormation template should create the Lambda functions, but you may need to upload the code:

```bash
# Create-Job Lambda
cd backend/functions-v2/create-job
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-v2-create-job-dev \
  --zip-file fileb://function.zip

# Get-Job-Status Lambda
cd ../get-job-status
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-v2-get-job-status-dev \
  --zip-file fileb://function.zip

# YouTube Downloader Lambda
cd ../youtube-downloader
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-v2-youtube-downloader-dev \
  --zip-file fileb://function.zip

# Lyrics Transcriber Lambda
cd ../lyrics-transcriber
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-v2-lyrics-transcriber-dev \
  --zip-file fileb://function.zip

# Chord Detector Trigger Lambda
cd ../chord-detector-trigger
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-v2-chord-detector-trigger-dev \
  --zip-file fileb://function.zip

# PDF Generator Lambda
cd ../pdf-generator
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-v2-pdf-generator-dev \
  --zip-file fileb://function.zip
```

## Alternative: Use Existing Deployment Script

If there's a deployment script, use it:

```bash
# Check for deployment scripts
ls -la deploy*.sh

# Run the deployment script
./deploy-full-pipeline.sh
```

## Verification

After deployment, verify the infrastructure:

```bash
# Check Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `chordscout`)].FunctionName'

# Check DynamoDB table
aws dynamodb describe-table --table-name chordscout-jobs-dev

# Check Step Functions
aws stepfunctions list-state-machines --query 'stateMachines[?contains(name, `chordscout`)].name'

# Check ECS cluster
aws ecs list-clusters --query 'clusterArns[?contains(@, `chordscout`)]'

# Check API Gateway
aws apigateway get-rest-apis --query 'items[?contains(name, `chordscout`)].{Name:name,Id:id}'
```

## Test the API

Once deployed, test the API:

```bash
# Get API URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name chordscout-v2-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text)

# Create a job
curl -X POST $API_URL/jobs \
  -H "Content-Type: application/json" \
  -d '{"youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Get job status (replace JOB_ID)
curl $API_URL/jobs/JOB_ID
```

## Troubleshooting

### Issue: Stack creation fails

**Check the error:**
```bash
aws cloudformation describe-stack-events \
  --stack-name chordscout-v2-dev \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
```

### Issue: Lambda functions not found

**List all Lambda functions:**
```bash
aws lambda list-functions --query 'Functions[].FunctionName'
```

### Issue: API Gateway not accessible

**Check API Gateway:**
```bash
aws apigateway get-rest-apis
```

### Issue: ECS task fails to start

**Check ECS task logs:**
```bash
aws logs tail /ecs/chordscout-chord-detector --follow
```

## Cost Estimate

**Per deployment:**
- Lambda: ~$0.20 per 1000 invocations
- ECS Fargate: ~$0.04 per hour (only when running)
- DynamoDB: ~$0.25 per GB-month
- S3: ~$0.023 per GB-month
- API Gateway: ~$3.50 per million requests

**Expected monthly cost (100 videos/day):**
- ~$30-50/month

## Next Steps

1. Deploy the CloudFormation stack
2. Update frontend API URL
3. Test with a YouTube video
4. Monitor CloudWatch logs for any errors
5. Add error handling to frontend

---

**Date**: 2026-01-29  
**Status**: ⏳ Awaiting Deployment  
**Priority**: HIGH - Required for app to function
