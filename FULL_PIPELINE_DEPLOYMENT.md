# ChordScout Full Pipeline Deployment Guide

Complete guide to deploy the end-to-end music transcription pipeline from YouTube link to sheet music.

## Architecture Overview

```
User Upload (YouTube/Audio)
    ↓
Amplify API Gateway
    ↓
AWS Step Functions State Machine
    ├─→ YouTube Downloader Lambda (if YouTube URL)
    ├─→ Parallel Processing:
    │   ├─→ OpenAI Whisper (Lyrics)
    │   └─→ Basic Pitch ML (Chords)
    ├─→ Combine Results Lambda
    ├─→ Sheet Music Generator Lambda
    └─→ Update DynamoDB (completed)
    ↓
Frontend displays results with abcjs
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured (`aws configure`)
3. **Docker** installed and running
4. **OpenAI API Key** for Whisper transcription
5. **Node.js 18+** and npm
6. **Git** for version control

## Cost Estimate

**Per Transcription:**
- Step Functions: $0.000025 per state transition (~10 transitions) = $0.00025
- Lambda (YouTube Download): $0.01
- Lambda (Whisper): $0.02
- Lambda (Chord Detection): $0.05
- Lambda (Combine/Sheet Music): $0.001
- S3 Storage: $0.001
- DynamoDB: $0.001

**Total: ~$0.08-0.12 per song**

Compare to:
- Chordify API: $0.50/song
- Manual transcription: $5-10/song

## Quick Start (Automated)

```bash
# Clone the repository
git clone https://github.com/DannyWilsonCodeShop/music-transcription-app
cd music-transcription-app

# Run the deployment script
./deploy-full-pipeline.sh
```

The script will:
1. ✅ Create OpenAI API secret in Secrets Manager
2. ✅ Build and push Docker image for chord detection
3. ✅ Create yt-dlp Lambda layer
4. ✅ Deploy CloudFormation stack with all resources
5. ✅ Configure Amplify backend
6. ✅ Run a test execution

## Manual Deployment (Step-by-Step)

### Step 1: Store OpenAI API Key

```bash
aws secretsmanager create-secret \
  --name ChordScout-OpenAI-dev \
  --description "OpenAI API Key for ChordScout" \
  --secret-string '{"OPENAI_API_KEY":"sk-your-key-here"}' \
  --region us-east-1
```

### Step 2: Build Chord Detector Image

```bash
# Create ECR repository
aws ecr create-repository \
  --repository-name chordscout-chord-detector \
  --region us-east-1

# Get repository URI
ECR_URI=$(aws ecr describe-repositories \
  --repository-names chordscout-chord-detector \
  --query 'repositories[0].repositoryUri' \
  --output text)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URI

# Build and push
cd backend/functions/chord-detector-ml
docker build --platform linux/amd64 -t chordscout-chord-detector .
docker tag chordscout-chord-detector:latest $ECR_URI:latest
docker push $ECR_URI:latest
cd ../../..
```

### Step 3: Create yt-dlp Lambda Layer

```bash
# Create layer directory
mkdir -p /tmp/yt-dlp-layer/python
cd /tmp/yt-dlp-layer

# Install yt-dlp
pip install yt-dlp -t python/

# Create zip
zip -r yt-dlp.zip python/

# Create S3 bucket for layers
aws s3 mb s3://chordscout-layers-dev-YOUR-ACCOUNT-ID

# Upload layer
aws s3 cp yt-dlp.zip s3://chordscout-layers-dev-YOUR-ACCOUNT-ID/layers/
```

### Step 4: Deploy CloudFormation Stack

```bash
aws cloudformation deploy \
  --template-file backend/infrastructure/cloudformation-template.yaml \
  --stack-name ChordScout-Pipeline-dev \
  --parameter-overrides \
      Environment=dev \
      OpenAISecretArn=arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:ChordScout-OpenAI-dev \
      ChordDetectorImageUri=$ECR_URI:latest \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Step 5: Get Stack Outputs

```bash
# Get State Machine ARN
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
  --stack-name ChordScout-Pipeline-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
  --output text)

# Get Audio Bucket
AUDIO_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name ChordScout-Pipeline-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`AudioBucketName`].OutputValue' \
  --output text)

# Get Jobs Table
JOBS_TABLE=$(aws cloudformation describe-stacks \
  --stack-name ChordScout-Pipeline-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`TranscriptionJobsTableName`].OutputValue' \
  --output text)

echo "State Machine: $STATE_MACHINE_ARN"
echo "Audio Bucket: $AUDIO_BUCKET"
echo "Jobs Table: $JOBS_TABLE"
```

### Step 6: Update Amplify Configuration

Update `amplify_outputs.json`:

```json
{
  "version": "1",
  "storage": {
    "aws_region": "us-east-1",
    "bucket_name": "YOUR-AUDIO-BUCKET"
  },
  "custom": {
    "stateMachineArn": "YOUR-STATE-MACHINE-ARN",
    "jobsTableName": "YOUR-JOBS-TABLE"
  }
}
```

### Step 7: Deploy Amplify Backend

```bash
# Install Amplify dependencies
cd amplify/functions/transcribe-audio
npm install
cd ../../..

# Deploy Amplify
npx ampx sandbox
```

## Testing the Pipeline

### Test with YouTube URL

```bash
# Create test input
cat > test-input.json <<EOF
{
  "jobId": "test-$(date +%s)",
  "youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Test Song"
}
EOF

# Start execution
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --name test-$(date +%s) \
  --input file://test-input.json

# Monitor execution
aws stepfunctions list-executions \
  --state-machine-arn $STATE_MACHINE_ARN \
  --max-results 1
```

### Test from Frontend

```javascript
// In your React app
const handleUpload = async (youtubeUrl) => {
  const response = await fetch('YOUR-API-GATEWAY-URL/transcribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      youtubeUrl,
      title: 'My Song'
    })
  });
  
  const { jobId } = await response.json();
  
  // Poll for results
  const checkStatus = setInterval(async () => {
    const job = await fetchJob(jobId);
    if (job.status === 'completed') {
      clearInterval(checkStatus);
      displayResults(job);
    }
  }, 5000);
};
```

## Monitoring

### CloudWatch Logs

```bash
# YouTube Downloader logs
aws logs tail /aws/lambda/chordscout-youtube-downloader-dev --follow

# Whisper Transcribe logs
aws logs tail /aws/lambda/chordscout-whisper-transcribe-dev --follow

# Chord Detector logs
aws logs tail /aws/lambda/chordscout-chord-detector-dev --follow

# Step Functions execution logs
aws logs tail /aws/stepfunctions/ChordScout-Transcription-dev --follow
```

### Step Functions Console

View executions in the AWS Console:
https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines

### DynamoDB Console

View job records:
https://console.aws.amazon.com/dynamodbv2/home?region=us-east-1#tables

## Troubleshooting

### Issue: YouTube download fails

**Symptoms:** Step Functions execution fails at DownloadYouTubeAudio step

**Solutions:**
1. Check yt-dlp layer is attached to Lambda
2. Verify Lambda has internet access (NAT Gateway if in VPC)
3. Update yt-dlp: `pip install --upgrade yt-dlp`
4. Check YouTube URL is valid and accessible

### Issue: Whisper transcription timeout

**Symptoms:** Lambda timeout after 300 seconds

**Solutions:**
1. Increase Lambda timeout to 900 seconds
2. Increase memory to 10GB (faster processing)
3. Split long audio files into chunks
4. Use Whisper API instead of local model

### Issue: Chord detection low accuracy

**Symptoms:** Incorrect chords detected

**Solutions:**
1. Adjust segment_duration in chord_utils.py
2. Increase confidence threshold
3. Pre-process audio (normalize, remove noise)
4. Use Chordify API as fallback for low confidence

### Issue: Step Functions execution fails

**Symptoms:** Execution shows "Failed" status

**Solutions:**
1. Check CloudWatch Logs for specific error
2. Verify IAM roles have correct permissions
3. Check Lambda function environment variables
4. Test individual Lambdas separately

## Updating the Pipeline

### Update Lambda Code

```bash
# Update and redeploy
aws lambda update-function-code \
  --function-name chordscout-youtube-downloader-dev \
  --zip-file fileb://function.zip
```

### Update Chord Detector Image

```bash
# Rebuild and push
cd backend/functions/chord-detector-ml
docker build --platform linux/amd64 -t chordscout-chord-detector .
docker tag chordscout-chord-detector:latest $ECR_URI:latest
docker push $ECR_URI:latest

# Update Lambda
aws lambda update-function-code \
  --function-name chordscout-chord-detector-dev \
  --image-uri $ECR_URI:latest
```

### Update Step Functions State Machine

```bash
aws stepfunctions update-state-machine \
  --state-machine-arn $STATE_MACHINE_ARN \
  --definition file://backend/step-functions/transcription-workflow.json
```

## Scaling Considerations

### For 100 transcriptions/day:
- Cost: ~$10/day
- No infrastructure changes needed
- Default Lambda concurrency sufficient

### For 1,000 transcriptions/day:
- Cost: ~$100/day
- Increase Lambda reserved concurrency
- Consider provisioned concurrency for Whisper
- Enable DynamoDB auto-scaling

### For 10,000+ transcriptions/day:
- Cost: ~$1,000/day
- Use SQS for buffering
- Implement caching for popular songs
- Consider batch processing
- Use Spot instances for chord detection

## Security Best Practices

1. **API Keys:** Store in Secrets Manager, rotate regularly
2. **IAM Roles:** Use least privilege principle
3. **S3 Buckets:** Enable encryption at rest
4. **VPC:** Run Lambdas in private subnets
5. **Logging:** Enable CloudTrail for audit logs
6. **Access:** Use API Gateway with authentication

## Next Steps

1. ✅ Deploy the pipeline
2. ✅ Test with sample songs
3. ⬜ Add user authentication (Cognito)
4. ⬜ Implement caching for popular songs
5. ⬜ Add PDF export for sheet music
6. ⬜ Create admin dashboard for monitoring
7. ⬜ Set up CI/CD pipeline
8. ⬜ Add error notifications (SNS)

## Support

- GitHub Issues: https://github.com/DannyWilsonCodeShop/music-transcription-app/issues
- Documentation: See README.md
- AWS Support: https://console.aws.amazon.com/support/

## Resources

- [AWS Step Functions](https://docs.aws.amazon.com/step-functions/)
- [AWS Lambda](https://docs.aws.amazon.com/lambda/)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [Spotify Basic Pitch](https://github.com/spotify/basic-pitch)
- [abcjs Documentation](https://github.com/paulrosen/abcjs)
