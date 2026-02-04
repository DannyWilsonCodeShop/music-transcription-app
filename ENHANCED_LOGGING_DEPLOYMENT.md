# Enhanced Logging Deployment - Debugging 60% Stuck Issue

**Date**: February 4, 2026  
**AWS Account**: 090130568474 (chordscout profile)  
**Status**: ✅ DEPLOYED

## Problem

Jobs were completing successfully (status: COMPLETE, progress: 100%) in DynamoDB, but users were seeing them stuck at 60% in the frontend. This suggests either:
1. A frontend polling issue
2. Status updates not being properly reflected
3. A timing issue in the workflow

## Solution

Added comprehensive logging to all components to identify the exact bottleneck:

### 1. Chord Detector ECS Task (Enhanced Logging)

**File**: `backend/functions-v2/chord-detector-ecs/app.py`

**Changes**:
- Replaced complex implementation with simpler, more focused version
- Added timestamped logging at every step
- Explicit logging of:
  - Environment variables
  - File downloads (size, time)
  - Chord detection progress
  - DynamoDB updates
  - PDF Lambda triggers
- Uses `flush=True` to ensure logs appear immediately

**Docker Image**: 
- Built: `chordscout-chord-detector:latest`
- Pushed to: `090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest`
- Digest: `sha256:c3f6bec391598ace705d0fb8763862637ada3107d74fe240b445031a6bc5152f`

### 2. PDF Generator Lambda (Enhanced Logging)

**File**: `backend/functions-v2/pdf-generator/index.js`

**Changes**:
- Added step-by-step logging with `[STEP X]` markers
- Logs job data retrieval details
- Logs chord and lyrics data extraction
- Logs PDF generation progress
- Logs S3 upload status
- Logs DynamoDB status updates
- Enhanced error logging with stack traces

**Deployed**: `chordscout-v2-pdf-generator-dev`
- Size: 12,021,479 bytes (~12MB)
- Last Modified: 2026-02-04T05:54:03Z

### 3. Get Job Status Lambda (Enhanced Logging)

**File**: `backend/functions-v2/get-job-status/index.js`

**Changes**:
- Added detailed logging for every status request
- Logs job details (status, progress, PDF URL, etc.)
- Logs when job is not found
- Enhanced error logging

**Deployed**: `chordscout-v2-get-job-status-dev`
- Size: 3,435,554 bytes (~3.4MB)
- Last Modified: 2026-02-04T05:54:05Z

## How to Debug

### 1. Monitor CloudWatch Logs

**ECS Task Logs** (Chord Detector):
```bash
export AWS_PROFILE=chordscout
aws logs tail /ecs/ChordScout-dev --follow
```

**PDF Generator Logs**:
```bash
export AWS_PROFILE=chordscout
aws logs tail /aws/lambda/chordscout-v2-pdf-generator-dev --follow
```

**Get Job Status Logs**:
```bash
export AWS_PROFILE=chordscout
aws logs tail /aws/lambda/chordscout-v2-get-job-status-dev --follow
```

### 2. Test a New Job

1. Submit a new transcription job through the frontend
2. Watch the logs in real-time
3. Look for:
   - Where the job gets stuck (last log message)
   - Any error messages
   - Status update patterns
   - Timing between steps

### 3. Check DynamoDB Directly

```bash
export AWS_PROFILE=chordscout
aws dynamodb get-item \
  --table-name ChordScout-Jobs-V2-dev \
  --key '{"jobId": {"S": "YOUR_JOB_ID"}}'
```

## Expected Log Flow

### Successful Job Flow:

1. **Chord Detector ECS Task**:
   ```
   [TIMESTAMP] [INFO] STARTING CHORD DETECTION ECS TASK
   [TIMESTAMP] [INFO] Step 1: Updating job status to DETECTING_CHORDS (70%)
   [TIMESTAMP] [INFO] Step 2: Downloading audio from s3://...
   [TIMESTAMP] [INFO] Step 3: Starting chord detection...
   [TIMESTAMP] [INFO] Step 4: Updating job with chord data...
   [TIMESTAMP] [INFO] Step 5: Triggering PDF generation Lambda...
   [TIMESTAMP] [INFO] CHORD DETECTION TASK COMPLETED SUCCESSFULLY
   ```

2. **PDF Generator Lambda**:
   ```
   [TIMESTAMP] [INFO] PDF GENERATOR STARTING
   [TIMESTAMP] [INFO] [STEP 1] Updating job status to GENERATING_PDF (90%)
   [TIMESTAMP] [INFO] [STEP 2] Fetching job data from DynamoDB
   [TIMESTAMP] [INFO] [STEP 3] Extracting chord and lyrics data
   [TIMESTAMP] [INFO] [STEP 4] Generating PDF document
   [TIMESTAMP] [INFO] [STEP 5] Uploading PDF to S3
   [TIMESTAMP] [INFO] [STEP 6] Updating job status to COMPLETE (100%)
   [TIMESTAMP] [INFO] PDF GENERATION COMPLETED SUCCESSFULLY
   ```

3. **Get Job Status Lambda** (polled by frontend):
   ```
   [TIMESTAMP] [INFO] GET JOB STATUS REQUEST
   [TIMESTAMP] [INFO] Fetching job: job-123
   [TIMESTAMP] [INFO] Job found: job-123
   [TIMESTAMP] [INFO]   Status: COMPLETE
   [TIMESTAMP] [INFO]   Progress: 100%
   [TIMESTAMP] [INFO]   Has PDF: Yes
   ```

## Next Steps

1. **Test a new job** and monitor the logs
2. **Identify the bottleneck** by finding where logs stop
3. **Check frontend polling** in `src/services/transcriptionService.ts` if backend completes successfully
4. **Verify status mapping** between backend and frontend status codes

## Files Modified

- ✅ `backend/functions-v2/chord-detector-ecs/app.py` (replaced with enhanced logging version)
- ✅ `backend/functions-v2/pdf-generator/index.js` (added comprehensive logging)
- ✅ `backend/functions-v2/get-job-status/index.js` (added detailed logging)

## Deployment Commands Used

```bash
# Switch to correct AWS account
export AWS_PROFILE=chordscout

# Build and push Docker image
cd backend/functions-v2/chord-detector-ecs
docker buildx build --platform linux/amd64 -t chordscout-chord-detector:latest .
docker tag chordscout-chord-detector:latest 090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 090130568474.dkr.ecr.us-east-1.amazonaws.com
docker push 090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest

# Deploy Lambda functions
cd backend/functions-v2/pdf-generator
zip -r function.zip index.js node_modules package.json package-lock.json
aws lambda update-function-code --function-name chordscout-v2-pdf-generator-dev --zip-file fileb://function.zip

cd ../get-job-status
zip -r function.zip index.js node_modules package.json package-lock.json
aws lambda update-function-code --function-name chordscout-v2-get-job-status-dev --zip-file fileb://function.zip
```
