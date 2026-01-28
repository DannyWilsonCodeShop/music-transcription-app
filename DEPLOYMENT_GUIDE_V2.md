# ChordScout V2 Deployment Guide
## High-Accuracy Architecture: Deepgram + Madmom

This guide covers deploying the new high-accuracy transcription pipeline.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured
3. **Docker** installed (for Madmom container)
4. **Node.js 18+** and **Python 3.11+**
5. **Deepgram API Key** - Sign up at https://deepgram.com
6. **Apify API Token** (optional, for testing)

## Step 1: Get Deepgram API Key

1. Go to https://deepgram.com and sign up
2. Navigate to API Keys section
3. Create a new API key
4. Copy the key (starts with something like `xxxxxxxxxxxxxxxxxxxxx`)
5. Add to `.env`:
   ```
   DEEPGRAM_API_KEY=your_actual_key_here
   ```

## Step 2: Build Madmom Docker Container

```bash
cd backend/functions-v2/chord-detector-madmom

# Build the Docker image
docker build -t chordscout-madmom .

# Test locally (optional)
docker run -p 9000:8080 chordscout-madmom

# Create ECR repository
aws ecr create-repository --repository-name chordscout-madmom --region us-east-1

# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag chordscout-madmom:latest <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/chordscout-madmom:latest
docker push <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/chordscout-madmom:latest
```

## Step 3: Deploy Infrastructure with CloudFormation

```bash
cd backend/infrastructure-v2

# Deploy the stack
aws cloudformation create-stack \
  --stack-name chordscout-v2-dev \
  --template-body file://cloudformation-new-architecture.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=DeepgramApiKey,ParameterValue=YOUR_DEEPGRAM_KEY \
    ParameterKey=ChordDetectorImageUri,ParameterValue=<YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/chordscout-madmom:latest \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for stack creation
aws cloudformation wait stack-create-complete --stack-name chordscout-v2-dev

# Get outputs
aws cloudformation describe-stacks --stack-name chordscout-v2-dev --query 'Stacks[0].Outputs'
```

## Step 4: Deploy Lambda Functions

### Create Job Function
```bash
cd backend/functions-v2/create-job
npm install
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-create-job-dev \
  --zip-file fileb://function.zip
```

### YouTube Downloader Function
```bash
cd backend/functions-v2/youtube-downloader
pip install -r requirements.txt -t .
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-youtube-downloader-dev \
  --zip-file fileb://function.zip
```

### Lyrics Transcriber Function
```bash
cd backend/functions-v2/lyrics-transcriber
npm install
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-lyrics-transcriber-dev \
  --zip-file fileb://function.zip
```

### PDF Generator Function
```bash
cd backend/functions-v2/pdf-generator
npm install
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-pdf-generator-dev \
  --zip-file fileb://function.zip
```

### Get Job Status Function
```bash
cd backend/functions-v2/get-job-status
npm install
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-get-job-status-dev \
  --zip-file fileb://function.zip
```

## Step 5: Update Frontend

Update your frontend to use the new API endpoints:

```javascript
// src/services/transcriptionService.ts
const API_ENDPOINT = 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev';

export async function createJob(youtubeUrl) {
  const response = await fetch(`${API_ENDPOINT}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ youtubeUrl })
  });
  return response.json();
}

export async function getJobStatus(jobId) {
  const response = await fetch(`${API_ENDPOINT}/jobs/${jobId}`);
  return response.json();
}
```

## Step 6: Test the Pipeline

```bash
# Test creating a job
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/jobs \
  -H "Content-Type: application/json" \
  -d '{"youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Get job status
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/jobs/YOUR_JOB_ID
```

## Architecture Overview

```
User → API Gateway → Create Job Lambda → DynamoDB
                                      ↓
                              Step Functions
                                      ↓
                    ┌─────────────────┴─────────────────┐
                    ↓                                   ↓
          YouTube Downloader                    (stores in S3)
                    ↓
          ┌─────────┴─────────┐
          ↓                   ↓
    Deepgram Nova-3      Madmom CNN+CRF
    (Lyrics)             (Chords)
          ↓                   ↓
          └─────────┬─────────┘
                    ↓
              PDF Generator
                    ↓
              S3 (Final PDF)
                    ↓
              User Download
```

## Cost Estimates

Per 4-minute song:
- Deepgram: ~$0.017
- Lambda compute: ~$0.002
- S3 storage: ~$0.0001
- DynamoDB: ~$0.0001
- **Total: ~$0.02 per song**

## Monitoring

View logs in CloudWatch:
- `/aws/lambda/chordscout-create-job-dev`
- `/aws/lambda/chordscout-youtube-downloader-dev`
- `/aws/lambda/chordscout-lyrics-transcriber-dev`
- `/aws/lambda/chordscout-chord-detector-dev`
- `/aws/lambda/chordscout-pdf-generator-dev`

View Step Functions executions:
```bash
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:ACCOUNT_ID:stateMachine:ChordScout-Transcription-dev
```

## Troubleshooting

### Madmom Container Issues
- Check ECR image exists: `aws ecr describe-images --repository-name chordscout-madmom`
- Check Lambda function configuration: `aws lambda get-function --function-name chordscout-chord-detector-dev`
- Increase memory if needed: `aws lambda update-function-configuration --function-name chordscout-chord-detector-dev --memory-size 4096`

### Deepgram API Errors
- Verify API key is correct
- Check Deepgram dashboard for usage/limits
- Ensure audio file is accessible from Lambda

### Step Functions Failures
- View execution details in AWS Console
- Check CloudWatch logs for each Lambda
- Verify IAM permissions

## Next Steps

1. Set up monitoring and alerts
2. Implement user authentication
3. Add caching for repeated URLs
4. Optimize costs with reserved capacity
5. Add support for direct file uploads
