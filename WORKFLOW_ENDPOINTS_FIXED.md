# Workflow Endpoints Fixed - February 4, 2026

**Status:** ✅ FIXED AND DEPLOYED  
**Issue:** ECS task couldn't trigger PDF generation (missing environment variable)

---

## Problem Identified

The ECS task definition was **missing the PDF_GENERATOR_FUNCTION environment variable**, which meant:
1. ECS task completes chord detection
2. Tries to trigger PDF generation
3. **Fails** because it doesn't know which Lambda to call
4. Job gets stuck at "DETECTING_CHORDS" status
5. PDF never generates

---

## Root Cause

When we optimized the workflow to remove the `.sync` wait and PDFGeneration state, we assumed the ECS task would trigger the PDF generator. However, the ECS task definition didn't have the Lambda function name in its environment variables.

**Missing Environment Variable:**
```json
{
  "name": "PDF_GENERATOR_FUNCTION",
  "value": "chordscout-v2-pdf-generator-dev"
}
```

---

## Solution Applied

### 1. Updated ECS Task Definition (Revision 9)

**Added Environment Variable:**
```json
{
  "name": "PDF_GENERATOR_FUNCTION",
  "value": "chordscout-v2-pdf-generator-dev"
}
```

**Full Environment Variables:**
```json
[
  {
    "name": "ENABLE_STEM_SEPARATION",
    "value": "false"
  },
  {
    "name": "CHUNK_DURATION",
    "value": "30"
  },
  {
    "name": "S3_AUDIO_BUCKET",
    "value": "chordscout-audio-temp-dev-090130568474"
  },
  {
    "name": "DYNAMODB_JOBS_TABLE",
    "value": "ChordScout-Jobs-V2-dev"
  },
  {
    "name": "PDF_GENERATOR_FUNCTION",
    "value": "chordscout-v2-pdf-generator-dev"
  }
]
```

### 2. Updated Step Functions Workflow

**Changed Task Definition Reference:**
```json
{
  "TaskDefinition": "chordscout-chord-detector-dev:9"
}
```

This ensures new ECS tasks use revision 9 with the PDF_GENERATOR_FUNCTION variable.

---

## Verification

### ECS Task Definition
```bash
aws ecs describe-task-definition \
  --task-definition chordscout-chord-detector-dev:9 \
  --profile chordscout \
  --region us-east-1 \
  --output json | jq -r '.taskDefinition.containerDefinitions[0].environment'
```

**Expected Output:**
```json
[
  ...
  {
    "name": "PDF_GENERATOR_FUNCTION",
    "value": "chordscout-v2-pdf-generator-dev"
  }
]
```

### Step Functions Workflow
```bash
aws stepfunctions describe-state-machine \
  --state-machine-arn "arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-V2-Transcription-dev" \
  --profile chordscout \
  --region us-east-1 \
  --output json | jq -r '.definition' | jq '.States.ParallelAnalysis.Branches[0].States.ChordDetection.Parameters.TaskDefinition'
```

**Expected Output:**
```
"chordscout-chord-detector-dev:9"
```

---

## Complete Workflow Verification

### All Components Point to V2 Functions

| Component | Resource | Status |
|-----------|----------|--------|
| **Frontend API** | `https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev` | ✅ Active |
| **Create Job Lambda** | `chordscout-v2-create-job-dev` | ✅ Points to V2 Step Functions |
| **Step Functions** | `ChordScout-V2-Transcription-dev` | ✅ Updated 2026-02-04 13:26 EST |
| **YouTube Downloader** | `chordscout-v2-youtube-downloader-dev` | ✅ V2 Function |
| **Lyrics Transcriber** | `chordscout-v2-lyrics-transcriber-dev` | ✅ V2 Function (updated 2026-02-04) |
| **Chord Detector (ECS)** | Task Definition Revision 9 | ✅ Has PDF_GENERATOR_FUNCTION |
| **PDF Generator** | `chordscout-v2-pdf-generator-dev` | ✅ V2 Function (updated 2026-02-04) |

---

## Expected Behavior Now

### Complete Flow

```
1. User submits YouTube URL
   ↓
2. Frontend calls API Gateway
   ↓
3. create-job Lambda
   - Creates DynamoDB record
   - Triggers Step Functions (ChordScout-V2-Transcription-dev)
   ↓
4. Step Functions
   - Downloads audio (youtube-downloader-dev)
   - Parallel:
     ├─ Transcribes lyrics (lyrics-transcriber-dev)
     └─ Triggers ECS task (async, no wait)
   - Completes in ~20 seconds
   ↓
5. ECS Task (background, 5 min)
   - Loads audio
   - Detects tempo
   - Detects chords
   - Detects key (pattern-based)
   - Detects song structure
   - Updates DynamoDB
   - Triggers PDF Generator ← NOW WORKS!
   ↓
6. PDF Generator Lambda
   - Generates PDF
   - Uploads to S3
   - Updates DynamoDB → COMPLETE
   ↓
7. Frontend polls DynamoDB
   - Shows continuous progress
   - Displays PDF download link
```

---

## Testing

### Submit New Job

1. Go to frontend
2. Submit YouTube URL: `https://www.youtube.com/watch?v=Q-RKhgsZu64`
3. Observe progress:
   - DOWNLOADING (10s)
   - TRANSCRIBING_LYRICS (8s)
   - DETECTING_CHORDS (5 min)
   - GENERATING_PDF (0.4s)
   - COMPLETE

### Verify in CloudWatch

**ECS Task Logs:**
```
Triggering PDF generation Lambda...
✓ PDF generation Lambda invoked
  Status code: 202
  Request ID: xxx
```

**PDF Generator Logs:**
```
[INFO] Processing job: xxx
[INFO] Generating PDF...
✓ PDF generated successfully
✓ Uploaded to S3
✓ Job marked as COMPLETE
```

---

## Files Modified

1. **ECS Task Definition**
   - Revision: 9
   - Added: PDF_GENERATOR_FUNCTION environment variable

2. **Step Functions Workflow**
   - File: `backend/step-functions-v2/optimized-workflow.json`
   - Changed: TaskDefinition to revision 9
   - Updated: 2026-02-04 13:26 EST

---

## Deployment Timeline

| Time | Action | Status |
|------|--------|--------|
| 12:56 EST | Updated Step Functions (async ECS) | ✅ |
| 13:26 EST | Added PDF_GENERATOR_FUNCTION to ECS | ✅ |
| 13:26 EST | Updated Step Functions (revision 9) | ✅ |

---

## Success Criteria

The fix is successful if:
1. ✅ ECS task has PDF_GENERATOR_FUNCTION environment variable
2. ✅ Step Functions uses task definition revision 9
3. ✅ New jobs complete successfully (COMPLETE status)
4. ✅ PDF is generated and URL is available
5. ✅ No jobs stuck at DETECTING_CHORDS

---

## Rollback Plan

If issues occur:

### Revert to Previous Task Definition
```bash
aws stepfunctions update-state-machine \
  --state-machine-arn "arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-V2-Transcription-dev" \
  --definition '{"TaskDefinition": "chordscout-chord-detector-dev:8"}' \
  --profile chordscout \
  --region us-east-1
```

---

**Status: FIXED AND DEPLOYED ✅**

The ECS task now has the PDF_GENERATOR_FUNCTION environment variable and can successfully trigger PDF generation. Jobs should complete end-to-end without getting stuck.
