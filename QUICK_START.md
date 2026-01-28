# ChordScout V2 - Quick Start

## ✅ Completed Steps

1. ✅ Deepgram API key configured
2. ✅ Apify API token configured  
3. ✅ Docker container built successfully

## 📦 What We Built

**New Backend Architecture:**
- `create-job` - Creates transcription jobs
- `youtube-downloader` - Downloads audio from YouTube
- `lyrics-transcriber` - Uses Deepgram Nova-3 for lyrics
- `chord-detector` - Chord detection (currently mock, can be enhanced)
- `pdf-generator` - Creates PDF with jsPDF
- `get-job-status` - Status polling API

**Infrastructure:**
- CloudFormation template ready
- DynamoDB tables for jobs
- S3 buckets for audio + PDFs
- Step Functions workflow
- API Gateway endpoints

## 🚀 Next Steps to Deploy

### 1. Push Docker Container to ECR

```bash
# Get your AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-east-1

# Create ECR repository
aws ecr create-repository \
  --repository-name chordscout-chord-detector \
  --region $AWS_REGION

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag and push
docker tag chordscout-madmom:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/chordscout-chord-detector:latest

docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/chordscout-chord-detector:latest
```

### 2. Deploy CloudFormation Stack

```bash
# Get your Deepgram API key from .env
DEEPGRAM_KEY=$(grep DEEPGRAM_API_KEY .env | cut -d'=' -f2)

# Deploy the stack
aws cloudformation create-stack \
  --stack-name chordscout-v2-dev \
  --template-body file://backend/infrastructure-v2/cloudformation-new-architecture.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=DeepgramApiKey,ParameterValue=$DEEPGRAM_KEY \
    ParameterKey=ChordDetectorImageUri,ParameterValue=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/chordscout-chord-detector:latest \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $AWS_REGION

# Wait for completion (takes ~5 minutes)
aws cloudformation wait stack-create-complete \
  --stack-name chordscout-v2-dev \
  --region $AWS_REGION

# Get API endpoint
aws cloudformation describe-stacks \
  --stack-name chordscout-v2-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text \
  --region $AWS_REGION
```

### 3. Deploy Lambda Functions

```bash
# Create Job
cd backend/functions-v2/create-job
npm install
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-create-job-dev \
  --zip-file fileb://function.zip \
  --region $AWS_REGION

# YouTube Downloader
cd ../youtube-downloader
pip3 install -r requirements.txt -t .
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-youtube-downloader-dev \
  --zip-file fileb://function.zip \
  --region $AWS_REGION

# Lyrics Transcriber
cd ../lyrics-transcriber
npm install
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-lyrics-transcriber-dev \
  --zip-file fileb://function.zip \
  --region $AWS_REGION

# PDF Generator
cd ../pdf-generator
npm install
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-pdf-generator-dev \
  --zip-file fileb://function.zip \
  --region $AWS_REGION

# Get Job Status
cd ../get-job-status
npm install
zip -r function.zip .
aws lambda update-function-code \
  --function-name chordscout-get-job-status-dev \
  --zip-file fileb://function.zip \
  --region $AWS_REGION
```

### 4. Test the API

```bash
# Get your API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name chordscout-v2-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text \
  --region $AWS_REGION)

# Create a job
curl -X POST $API_ENDPOINT/jobs \
  -H "Content-Type: application/json" \
  -d '{"youtubeUrl": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'

# Check job status (replace JOB_ID with the ID from above)
curl $API_ENDPOINT/jobs/JOB_ID
```

## 📊 Architecture Flow

```
User → API Gateway → Create Job
                         ↓
                    DynamoDB (Job Record)
                         ↓
                  Step Functions
                         ↓
              ┌──────────┴──────────┐
              ↓                     ↓
    YouTube Downloader      (stores to S3)
              ↓
      ┌───────┴───────┐
      ↓               ↓
  Deepgram        Chord Detector
  (Lyrics)        (Mock/Basic)
      ↓               ↓
      └───────┬───────┘
              ↓
        PDF Generator
              ↓
        S3 (Final PDF)
              ↓
        User Download
```

## 💰 Cost Estimate

Per 4-minute song:
- Deepgram Nova-3: ~$0.017
- Lambda compute: ~$0.002
- S3 + DynamoDB: ~$0.0002
- **Total: ~$0.02 per song**

## 🔧 Enhancing Chord Detection

The current chord detector uses mock data. To add real chord detection:

**Option 1: Use a third-party API**
- Chordify API (if available)
- ACRCloud Music Recognition
- Custom ML model

**Option 2: Build Madmom container properly**
- Use Amazon Linux 2023 base image
- Install proper build tools
- Compile Madmom from source

**Option 3: Use Essentia**
- Lighter weight than Madmom
- Easier to build
- ~60-70% accuracy

## 📝 Notes

- Deepgram provides excellent lyrics transcription
- PDF generation works with any chord data
- Mock chords follow common progressions (C-Am-F-G)
- All infrastructure is serverless and scales automatically

## 🐛 Troubleshooting

**CloudFormation fails:**
- Check IAM permissions
- Verify Deepgram API key is valid
- Ensure ECR image was pushed successfully

**Lambda timeouts:**
- Increase timeout in CloudFormation template
- Check CloudWatch logs for errors

**No PDF generated:**
- Verify S3 bucket permissions
- Check Step Functions execution in AWS Console
- Review Lambda logs in CloudWatch

## 📚 Documentation

- Full deployment guide: `DEPLOYMENT_GUIDE_V2.md`
- Architecture details: `NEW_ARCHITECTURE.md`
- Original plan: See conversation history

Ready to deploy? Run the commands in order from "Next Steps to Deploy" above!
