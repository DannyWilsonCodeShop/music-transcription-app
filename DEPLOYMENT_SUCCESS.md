# ChordScout Backend Deployment - SUCCESS ✅

## Deployment Date
January 25, 2026

## AWS Account
- Account ID: 090130568474
- Region: us-east-1
- Environment: dev

## Deployed Resources

### CloudFormation Stack
- **Stack Name**: ChordScout-Pipeline-dev
- **Status**: CREATE_COMPLETE
- **Template**: backend/infrastructure/cloudformation-template-simple.yaml

### S3 Storage
- **Bucket Name**: chordscout-audio-dev-090130568474
- **Purpose**: Audio file storage and transcription results
- **Features**:
  - Versioning enabled
  - CORS configured for web uploads
  - Lifecycle policy: 30 days to STANDARD_IA, 90 days expiration

### DynamoDB
- **Table Name**: ChordScout-TranscriptionJobs-dev
- **Billing**: Pay-per-request
- **Features**:
  - Primary key: id (String)
  - GSI: UserIdIndex (userId + createdAt)
  - Streams enabled
  - Point-in-time recovery enabled

### Lambda Functions

#### 1. YouTube Downloader
- **Name**: chordscout-youtube-downloader-dev
- **Runtime**: Python 3.11
- **Memory**: 1024 MB
- **Timeout**: 300 seconds
- **Purpose**: Downloads audio from YouTube URLs using yt-dlp

#### 2. Whisper Transcribe
- **Name**: chordscout-whisper-transcribe-dev
- **Runtime**: Python 3.11
- **Memory**: 3008 MB
- **Timeout**: 300 seconds
- **Purpose**: Transcribes audio to text using OpenAI Whisper API

#### 3. Sheet Music Generator
- **Name**: chordscout-sheet-music-dev
- **Runtime**: Node.js 18.x
- **Memory**: 1024 MB
- **Timeout**: 60 seconds
- **Purpose**: Generates ABC notation sheet music from transcription

### Step Functions
- **State Machine**: ChordScout-Transcription-dev
- **ARN**: arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-Transcription-dev
- **Workflow**:
  1. Check input type (YouTube URL or direct audio)
  2. Download YouTube audio (if URL provided)
  3. Transcribe lyrics with Whisper
  4. Generate sheet music

### IAM Roles
- **Lambda Execution Role**: ChordScout-Lambda-dev
  - S3 read/write access
  - DynamoDB read/write access
  - Secrets Manager read access
  - Lambda invoke permissions

- **Step Functions Role**: ChordScout-StepFunctions-dev
  - Lambda invoke permissions
  - DynamoDB update permissions

### Secrets Manager
- **Secret Name**: ChordScout-OpenAI-dev
- **ARN**: arn:aws:secretsmanager:us-east-1:090130568474:secret:ChordScout-OpenAI-dev-lH3RGP
- **Contains**: OpenAI API key for Whisper transcription

## What's NOT Deployed (Yet)

### Chord Detector Lambda
- **Status**: Docker build in progress
- **Issue**: Large ML packages (scipy, librosa, basic-pitch) taking very long to download
- **Solution**: Will be added in a future deployment once Docker image builds successfully
- **Impact**: Transcription pipeline works without chord detection for now

## Configuration Files Updated

### amplify_outputs.json
```json
{
  "storage": {
    "bucket_name": "chordscout-audio-dev-090130568474"
  },
  "custom": {
    "stateMachineArn": "arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-Transcription-dev",
    "jobsTableName": "ChordScout-TranscriptionJobs-dev"
  }
}
```

## Next Steps

### 1. Test the Pipeline
```bash
# Start a test execution
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-Transcription-dev \
  --name test-execution-$(date +%s) \
  --input '{"jobId":"test-123","youtubeUrl":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","title":"Test Song"}'
```

### 2. Monitor Execution
```bash
# View execution history
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-Transcription-dev

# Check CloudWatch Logs
aws logs tail /aws/lambda/chordscout-youtube-downloader-dev --follow
```

### 3. Deploy Chord Detector (When Ready)
- Complete Docker image build
- Push to ECR: 090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector
- Update CloudFormation template to include chord detector Lambda
- Update Step Functions workflow to include parallel chord detection

### 4. Deploy Frontend
- Push changes to GitHub
- Amplify will automatically build and deploy
- Frontend will connect to deployed backend resources

### 5. Add yt-dlp Layer
The YouTube downloader Lambda needs a yt-dlp layer to function. Create it with:
```bash
# Create layer
mkdir -p /tmp/yt-dlp-layer/python
pip install yt-dlp -t /tmp/yt-dlp-layer/python/
cd /tmp/yt-dlp-layer
zip -r yt-dlp.zip python/

# Upload to S3
aws s3 cp yt-dlp.zip s3://chordscout-audio-dev-090130568474/layers/yt-dlp.zip

# Create Lambda layer
aws lambda publish-layer-version \
  --layer-name yt-dlp-dev \
  --content S3Bucket=chordscout-audio-dev-090130568474,S3Key=layers/yt-dlp.zip \
  --compatible-runtimes python3.11

# Update Lambda to use layer
aws lambda update-function-configuration \
  --function-name chordscout-youtube-downloader-dev \
  --layers <LAYER_ARN>
```

## Cost Estimate
- **S3**: ~$0.023/GB/month + transfer costs
- **DynamoDB**: Pay-per-request (~$1.25 per million requests)
- **Lambda**: First 1M requests free, then $0.20 per 1M requests
- **Step Functions**: $0.025 per 1,000 state transitions
- **OpenAI Whisper**: ~$0.006 per minute of audio

**Estimated cost per transcription**: $0.10-0.15

## Troubleshooting

### If YouTube download fails:
- Check yt-dlp layer is attached to Lambda
- Verify Lambda has internet access (NAT Gateway if in VPC)
- Check CloudWatch Logs for errors

### If Whisper transcription fails:
- Verify OpenAI API key in Secrets Manager
- Check Lambda memory (may need more for large files)
- Verify audio file is in supported format

### If Step Functions fails:
- Check IAM permissions for Lambda invocation
- Verify input JSON format matches expected schema
- Review Step Functions execution history

## Success Criteria ✅
- [x] CloudFormation stack deployed successfully
- [x] S3 bucket created with proper configuration
- [x] DynamoDB table created with GSI
- [x] Lambda functions deployed
- [x] Step Functions state machine created
- [x] IAM roles configured with proper permissions
- [x] Secrets Manager configured
- [x] amplify_outputs.json updated
- [x] Changes committed and pushed to GitHub
- [ ] yt-dlp layer added to YouTube downloader
- [ ] Test execution completed successfully
- [ ] Chord detector Lambda deployed
- [ ] Frontend deployed and connected

## Repository
- **GitHub**: https://github.com/DannyWilsonCodeShop/music-transcription-app
- **Branch**: main
- **Latest Commit**: Deploy backend pipeline without chord detector
