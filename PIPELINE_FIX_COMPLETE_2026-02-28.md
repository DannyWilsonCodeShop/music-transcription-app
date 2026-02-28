# Pipeline Fix Complete - February 28, 2026

## Problem Identified

The user reported "still taking a long time" for file uploads. Investigation revealed multiple issues:

### 1. Wrong AWS Account
- Was checking account `463470937777` instead of `090130568474`
- The API Gateway `hfv1glzbxi` exists in account `8474`, not `7777`

### 2. Container Name Mismatch (FIXED)
- Process Lambda was trying to override container named `chord-detection`
- Actual container name in ECS task definition is `chord-detector`
- **Fix**: Updated `simple-pipeline/process-audio-lambda.py` line 73 to use `chord-detector`

### 3. Docker Image Platform Mismatch (FIXED)
- Docker image was built for wrong platform (ARM64 on Mac)
- ECS Fargate requires `linux/amd64`
- **Fix**: Updated `backend/functions-v2/chord-detector-ecs/build-and-push.sh` to build with `--platform linux/amd64`
- Rebuilt and pushed image to ECR

### 4. Lambda Handler Mismatch (FIXED)
- Lambda configuration expected handler `process-audio.lambda_handler`
- Actual file name was `process-audio-lambda.py`
- **Fix**: Updated Lambda configuration to use `process-audio-lambda.lambda_handler`

## Current Status

### ✅ Fixed Components

1. **Process Lambda** (`music-transcription-process-audio-test`)
   - Updated code with correct container name
   - Updated handler configuration
   - Deployed successfully

2. **Docker Image** (`chordscout-chord-detector:latest`)
   - Rebuilt for `linux/amd64` platform
   - Pushed to ECR: `090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest`
   - Digest: `sha256:61b9fc722d9cd98b84e9306c2dd88e3cfa00283026ebe56035483cdb06e4240c`

3. **Frontend Configuration**
   - `.env`: `VITE_API_BASE_URL=https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com`
   - `src/services/transcriptionService.ts`: Updated API_BASE_URL
   - `src/App.tsx`: Updated UPLOAD_API_ENDPOINT

### ⚠️ Remaining Issue

**ECS Task Failing on Startup**
- Tasks are launching successfully
- Container exits with code 1 immediately
- No logs being written to CloudWatch
- Likely cause: Missing environment variables or incorrect configuration

## Pipeline Architecture (Account 8474)

```
Frontend (localhost:5173)
  ↓
API Gateway (hfv1glzbxi.execute-api.us-east-1.amazonaws.com)
  ├─ POST /upload → music-transcription-upload-test
  ├─ POST /download → music-transcription-youtube-downloader-test
  └─ GET /jobs/{jobId} → music-transcription-get-job-status-test
  ↓
S3 Bucket (music-transcription-audio-test-090130568474)
  ↓ (S3 Event Trigger)
Process Lambda (music-transcription-process-audio-test)
  ↓
ECS Fargate Task (ChordScout-dev / chordscout-chord-detector-dev)
  - Container: chord-detector
  - Image: 090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest
  - Environment:
    * DYNAMODB_JOBS_TABLE=ChordScout-Jobs-V2-dev
    * S3_AUDIO_BUCKET=chordscout-audio-temp-dev-090130568474
    * PDF_GENERATOR_FUNCTION=chordscout-v2-pdf-generator-dev
    * ENABLE_STEM_SEPARATION=false
    * CHUNK_DURATION=30
  ↓
DynamoDB (ChordScout-Jobs-V2-dev)
  ↓
PDF Generator Lambda (chordscout-v2-pdf-generator-dev)
  ↓
S3 Bucket (chordscout-pdfs-dev-090130568474)
```

## Next Steps

1. **Debug ECS Task Failure**
   - Check if container is receiving environment variables correctly
   - Verify the app.py code can handle the JOB_ID, S3_BUCKET, S3_KEY environment variables
   - Test Docker image locally with same environment variables
   - Check if the container needs additional IAM permissions

2. **Test End-to-End**
   - Upload a file through the frontend
   - Verify job is created in DynamoDB
   - Verify ECS task starts and completes successfully
   - Verify PDF is generated and uploaded to S3

## Commands for Testing

### Check ECS Task Status
```bash
AWS_PROFILE=production aws ecs list-tasks --cluster ChordScout-dev --desired-status RUNNING
AWS_PROFILE=production aws ecs describe-tasks --cluster ChordScout-dev --tasks <task-arn>
```

### Check CloudWatch Logs
```bash
AWS_PROFILE=production aws logs tail /ecs/chordscout-chord-detector-dev --since 5m --follow
AWS_PROFILE=production aws logs tail /aws/lambda/music-transcription-process-audio-test --since 5m --follow
```

### Check DynamoDB Jobs
```bash
AWS_PROFILE=production aws dynamodb scan --table-name ChordScout-Jobs-V2-dev --filter-expression "createdAt > :date" --expression-attribute-values '{":date":{"S":"2026-02-28T00:00:00.000Z"}}'
```

### Test Upload
```bash
# Upload file through frontend at http://localhost:5173
# Or use curl:
curl -X POST https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/upload \
  -H "Content-Type: application/json" \
  -d '{"filename":"test.mp3","contentType":"audio/mpeg","userId":"test-user"}'
```

## Files Modified

1. `simple-pipeline/process-audio-lambda.py` - Fixed container name
2. `backend/functions-v2/chord-detector-ecs/build-and-push.sh` - Added platform flag
3. `.env` - Corrected API endpoint
4. `src/services/transcriptionService.ts` - Corrected API endpoint
5. `src/App.tsx` - Corrected API endpoint
