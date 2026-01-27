# Progress Tracking Deployment Guide

## Changes Summary

### Backend Changes

1. **New Lambda Function: update-job-status**
   - Location: `backend/functions/update-job-status/`
   - Purpose: Write and update job status in DynamoDB at each workflow step
   - Needs to be deployed to AWS Lambda

2. **Updated Step Functions Workflow**
   - File: `backend/step-functions/transcription-workflow-with-progress.json`
   - Adds progress tracking at each step (0% → 10% → 40% → 70% → 100%)
   - Includes error handling with status updates
   - Needs to be deployed to replace current workflow

3. **Lambda Timeout Increased**
   - YouTube downloader: 300s → 900s (15 minutes)
   - Already deployed ✅

### Frontend Changes

1. **Enhanced TranscriptionJob Interface**
   - Added: `currentStep`, `progress` fields
   - File: `src/services/transcriptionService.ts`

2. **New Component: TranscriptionProgressBar**
   - File: `src/components/TranscriptionProgressBar.tsx`
   - Shows real-time progress bar
   - Displays current step and elapsed time
   - Shows debug info (job ID, status, last update)
   - Error messages displayed clearly

3. **Logo Update**
   - Changed to Logo 3
   - File: `src/App-test.tsx`

## Deployment Steps

### Step 1: Deploy update-job-status Lambda

```bash
cd backend/functions/update-job-status
npm install
zip -r update-job-status.zip .
aws lambda create-function \
  --function-name chordscout-update-job-status-dev \
  --runtime nodejs18.x \
  --role arn:aws:iam::090130568474:role/ChordScout-Lambda-dev \
  --handler index.handler \
  --zip-file fileb://update-job-status.zip \
  --timeout 60 \
  --memory-size 256 \
  --environment Variables={JOBS_TABLE_NAME=ChordScout-TranscriptionJobs-dev} \
  --region us-east-1 \
  --profile chordscout
```

### Step 2: Update Step Functions Workflow

```bash
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-Transcription-dev \
  --definition file://backend/step-functions/transcription-workflow-with-progress.json \
  --region us-east-1 \
  --profile chordscout
```

### Step 3: Deploy Frontend

```bash
git add .
git commit -m "Add progress tracking with progress bar, debug info, and Logo 3"
git push
```

## Features After Deployment

### User Experience
- ✅ Real-time progress bar (0-100%)
- ✅ Current step displayed ("Downloading audio", "Transcribing lyrics", etc.)
- ✅ Elapsed time counter
- ✅ No more 404 errors - job exists in DB immediately
- ✅ Clear error messages if something fails
- ✅ Debug info for troubleshooting

### Progress Steps
1. **0%** - Initializing
2. **10%** - Downloading audio from YouTube
3. **40%** - Transcribing lyrics with Whisper AI
4. **70%** - Generating sheet music
5. **100%** - Complete

### Debug Information Shown
- Job ID
- Current status
- Last update timestamp
- Error details (if failed)

## Testing

After deployment, test with:
```bash
curl -X POST https://rzx9drt3z1.execute-api.us-east-1.amazonaws.com/prod/transcription/start \
  -H "Content-Type: application/json" \
  -d '{"youtubeUrl":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","title":"Test Song"}'
```

Then immediately check status - should return PENDING with 0% progress instead of 404.

## Notes

- Chunked upload for file uploads is prepared but not yet implemented (YouTube only for now)
- Progress percentages are estimates based on typical workflow timing
- Debug info can be hidden in production by checking environment variable
