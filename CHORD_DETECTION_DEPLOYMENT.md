# Chord Detection Deployment Guide

This guide covers deploying the Basic Pitch ML-based chord detection system to AWS Lambda.

## Architecture

```
Audio File (S3) → Transcribe Worker Lambda → Basic Pitch Lambda → Chord Results
                                          ↓
                                    OpenAI Whisper (Lyrics)
```

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Docker installed and running
3. AWS ECR repository created
4. IAM roles with necessary permissions

## Step 1: Create ECR Repository

```bash
# Create ECR repository for the chord detector
aws ecr create-repository \
  --repository-name chordscout-chord-detector \
  --region us-east-1

# Get the repository URI (save this for later)
export ECR_REPO_URI=$(aws ecr describe-repositories \
  --repository-names chordscout-chord-detector \
  --region us-east-1 \
  --query 'repositories[0].repositoryUri' \
  --output text)

echo "ECR Repository URI: $ECR_REPO_URI"
```

## Step 2: Build and Push Docker Image

```bash
# Navigate to the chord detector directory
cd backend/functions/chord-detector-ml

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_REPO_URI

# Build the Docker image
docker build --platform linux/amd64 -t chordscout-chord-detector .

# Tag the image
docker tag chordscout-chord-detector:latest $ECR_REPO_URI:latest

# Push to ECR
docker push $ECR_REPO_URI:latest
```

## Step 3: Create IAM Role for Lambda

```bash
# Create trust policy
cat > trust-policy.json <<EOF
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

# Create the role
aws iam create-role \
  --role-name ChordScoutChordDetectorRole \
  --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name ChordScoutChordDetectorRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create custom policy for S3 access
cat > s3-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }
  ]
}
EOF

# Create and attach S3 policy
aws iam create-policy \
  --policy-name ChordScoutS3Access \
  --policy-document file://s3-policy.json

aws iam attach-role-policy \
  --role-name ChordScoutChordDetectorRole \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/ChordScoutS3Access
```

## Step 4: Create Lambda Function

```bash
# Get the role ARN
export ROLE_ARN=$(aws iam get-role \
  --role-name ChordScoutChordDetectorRole \
  --query 'Role.Arn' \
  --output text)

# Create the Lambda function
aws lambda create-function \
  --function-name chordscout-chord-detector \
  --package-type Image \
  --code ImageUri=$ECR_REPO_URI:latest \
  --role $ROLE_ARN \
  --timeout 300 \
  --memory-size 3008 \
  --region us-east-1

# Get the function ARN (save this for the transcribe worker)
export CHORD_DETECTOR_ARN=$(aws lambda get-function \
  --function-name chordscout-chord-detector \
  --query 'Configuration.FunctionArn' \
  --output text)

echo "Chord Detector Lambda ARN: $CHORD_DETECTOR_ARN"
```

## Step 5: Update Transcribe Worker Environment Variables

```bash
# Update the transcribe worker Lambda with the chord detector ARN
aws lambda update-function-configuration \
  --function-name chordscout-transcribe-worker \
  --environment Variables="{
    CHORD_DETECTOR_FUNCTION_ARN=$CHORD_DETECTOR_ARN,
    S3_BUCKET=YOUR-BUCKET-NAME,
    DYNAMODB_TABLE=YOUR-TABLE-NAME,
    OPENAI_SECRET_ARN=YOUR-SECRET-ARN
  }"
```

## Step 6: Grant Invoke Permission

```bash
# Allow transcribe worker to invoke chord detector
aws lambda add-permission \
  --function-name chordscout-chord-detector \
  --statement-id AllowTranscribeWorkerInvoke \
  --action lambda:InvokeFunction \
  --principal lambda.amazonaws.com \
  --source-arn arn:aws:lambda:us-east-1:YOUR-ACCOUNT-ID:function:chordscout-transcribe-worker
```

## Step 7: Test the Function

```bash
# Create a test event
cat > test-event.json <<EOF
{
  "bucket": "YOUR-BUCKET-NAME",
  "key": "test-audio.mp3",
  "jobId": "test-job-123"
}
EOF

# Invoke the function
aws lambda invoke \
  --function-name chordscout-chord-detector \
  --payload file://test-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json

# Check the response
cat response.json
```

## Expected Response

```json
{
  "statusCode": 200,
  "body": {
    "jobId": "test-job-123",
    "key": "C",
    "mode": "major",
    "chords": [
      {
        "timestamp": 0.0,
        "name": "C",
        "confidence": 0.85,
        "duration": 4.2
      },
      {
        "timestamp": 4.2,
        "name": "G",
        "confidence": 0.92,
        "duration": 3.8
      }
    ],
    "totalChords": 15,
    "midiUrl": "s3://bucket/midi/test-job-123.mid"
  }
}
```

## Monitoring and Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/chordscout-chord-detector --follow

# Check function metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=chordscout-chord-detector \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

## Cost Estimation

**Per Transcription:**
- Lambda execution (3GB, ~30-60s): $0.03 - $0.06
- S3 storage (audio + MIDI): $0.001
- Data transfer: $0.001

**Total: ~$0.03 - $0.07 per song**

Compare to Chordify API: ~$0.50 per song (85% cost savings!)

## Troubleshooting

### Issue: Lambda timeout
**Solution:** Increase timeout to 300 seconds and memory to 3008 MB

### Issue: Out of memory
**Solution:** Increase memory allocation or process shorter segments

### Issue: Low accuracy
**Solution:** 
- Adjust `segment_duration` in chord_utils.py (try 1.5-3.0 seconds)
- Increase confidence threshold
- Pre-process audio (normalize, remove noise)

### Issue: Cold start delays
**Solution:** 
- Enable provisioned concurrency
- Use Lambda SnapStart (when available for containers)
- Keep function warm with CloudWatch Events

## Updating the Function

```bash
# Rebuild and push new image
docker build --platform linux/amd64 -t chordscout-chord-detector .
docker tag chordscout-chord-detector:latest $ECR_REPO_URI:latest
docker push $ECR_REPO_URI:latest

# Update Lambda to use new image
aws lambda update-function-code \
  --function-name chordscout-chord-detector \
  --image-uri $ECR_REPO_URI:latest
```

## Next Steps

1. **Add Chordify API Fallback**: For songs where confidence is low
2. **Implement Caching**: Store results in DynamoDB to avoid reprocessing
3. **Add Sheet Music Generation**: Convert MIDI to MusicXML/PDF
4. **Optimize Performance**: Use smaller models or quantization
5. **Add Monitoring**: CloudWatch dashboards and alarms

## Resources

- [Basic Pitch Documentation](https://github.com/spotify/basic-pitch)
- [AWS Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [Music Theory Reference](https://www.musictheory.net/)
