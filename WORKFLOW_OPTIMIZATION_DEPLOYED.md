# Workflow Optimization - DEPLOYED ✅

**Date:** February 4, 2026 12:56 PM EST  
**Status:** DEPLOYED TO DEV

---

## Changes Made

### 1. Removed `.sync` from ECS Task
**Before:**
```json
{
  "Resource": "arn:aws:states:::ecs:runTask.sync",  // Waits for completion
  ...
}
```

**After:**
```json
{
  "Resource": "arn:aws:states:::ecs:runTask",  // Async, no wait
  ...
}
```

### 2. Removed Redundant PDF Generation State
**Before:**
```
ParallelAnalysis → PDFGeneration → End
```

**After:**
```
ParallelAnalysis → End
```

The ECS task already triggers PDF generation, so Step Functions doesn't need to call it.

### 3. Added PDF_GENERATOR_FUNCTION to ECS Environment
Ensured the ECS task has the Lambda function name to trigger PDF generation:
```json
{
  "Name": "PDF_GENERATOR_FUNCTION",
  "Value": "chordscout-v2-pdf-generator-dev"
}
```

---

## Performance Improvement

### Step Functions Execution Time

| Stage | Before | After | Improvement |
|-------|--------|-------|-------------|
| YouTube Download | 10s | 10s | - |
| Lyrics Transcription | 8s | 8s | - |
| **Chord Detection (ECS)** | **5 min (wait)** | **0s (async)** | **-5 min** |
| PDF Generation | 0.4s | 0s (removed) | -0.4s |
| **Total** | **~5-6 min** | **~20s** | **-5 min** |

### Actual Completion Time
- **Same:** ~5-6 minutes (ECS still processes in background)
- **But:** Step Functions doesn't block
- **User sees:** Real-time progress via DynamoDB polling

---

## How It Works Now

### Workflow Flow
```
1. Step Functions starts
   ├─ Download YouTube audio (10s)
   ├─ Parallel:
   │   ├─ Transcribe lyrics (8s) → Updates DynamoDB
   │   └─ Trigger ECS task (async) → Returns immediately
   └─ Step Functions COMPLETE (~20s)

2. ECS task runs in background (5 min)
   ├─ Fargate cold start (3 min)
   ├─ Load audio (23s)
   ├─ Detect tempo (21s)
   ├─ Detect chords (15s)
   ├─ Detect key & structure (0.4s)
   ├─ Update DynamoDB (0.5s)
   └─ Trigger PDF generation (0.4s)

3. PDF Generator Lambda
   ├─ Generate PDF (0.4s)
   ├─ Upload to S3
   └─ Update DynamoDB → COMPLETE
```

### Frontend Experience
The frontend polls DynamoDB every 2 seconds and sees:
1. `DOWNLOADING` (10s) - Step Functions running
2. `TRANSCRIBING_LYRICS` (8s) - Deepgram processing
3. `DETECTING_CHORDS` (5 min) - ECS task running
4. `GENERATING_PDF` (0.4s) - PDF Lambda running
5. `COMPLETE` - PDF URL available

**User sees continuous progress, no perception of "stuck"**

---

## Benefits

### 1. Faster Step Functions Execution
- **Before:** 5-6 minutes (blocked on ECS)
- **After:** ~20 seconds (async)
- **Benefit:** Lower Step Functions costs, faster workflow completion

### 2. No Redundant PDF Generation
- **Before:** ECS triggers PDF + Step Functions triggers PDF (2x)
- **After:** ECS triggers PDF only (1x)
- **Benefit:** Cleaner architecture, no duplicate work

### 3. Better User Experience
- **Before:** Step Functions shows "running" for 5 minutes
- **After:** Step Functions completes quickly, DynamoDB shows real progress
- **Benefit:** Users see continuous updates, not stuck at one stage

### 4. Simpler Architecture
- **Before:** Step Functions orchestrates everything
- **After:** Step Functions triggers, ECS handles completion
- **Benefit:** Easier to debug, clearer separation of concerns

---

## Verification

### Check Workflow Definition
```bash
aws stepfunctions describe-state-machine \
  --state-machine-arn "arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-V2-Transcription-dev" \
  --profile chordscout \
  --region us-east-1 \
  --output json | jq -r '.definition' | jq '.'
```

**Verify:**
- ✅ `hasSync: false` - No `.sync` in ECS task
- ✅ `hasPDFGen: false` - No PDFGeneration state
- ✅ `ParallelAnalysis.End: true` - Workflow ends after parallel

### Test New Job
1. Submit YouTube URL via frontend
2. Observe Step Functions execution:
   - Should complete in ~20 seconds
   - Status: SUCCEEDED
3. Observe DynamoDB updates:
   - DOWNLOADING → TRANSCRIBING_LYRICS → DETECTING_CHORDS → GENERATING_PDF → COMPLETE
4. Verify PDF is generated and URL is available

---

## Rollback Plan

If issues occur, restore the previous workflow:

```bash
aws stepfunctions update-state-machine \
  --state-machine-arn "arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-V2-Transcription-dev" \
  --definition file://backend/step-functions-v2/current-workflow-backup.json \
  --profile chordscout \
  --region us-east-1
```

Backup saved at: `backend/step-functions-v2/current-workflow-backup.json`

---

## Files Changed

1. **Created:** `backend/step-functions-v2/optimized-workflow.json`
   - New async workflow definition
   - No `.sync`, no PDFGeneration state

2. **Created:** `backend/step-functions-v2/current-workflow-backup.json`
   - Backup of previous workflow
   - For rollback if needed

3. **Updated:** Step Functions state machine
   - ARN: `arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-V2-Transcription-dev`
   - Updated: February 4, 2026 12:56 PM EST

---

## Expected Behavior

### Step Functions Console
- Execution time: ~20 seconds
- Status: SUCCEEDED
- Output: Contains jobId and audio result

### DynamoDB (ChordScout-Jobs-V2-dev)
- Job status updates in real-time
- Progress: 0% → 10% → 40% → 70% → 90% → 100%
- Final status: COMPLETE
- PDF URL: Available when complete

### Frontend
- Progress bar updates smoothly
- No long "stuck" periods
- PDF download available when complete

---

## Monitoring

### CloudWatch Logs

**Step Functions:**
- Should complete in ~20s
- No errors about ECS task

**ECS Task (chord-detector):**
- Logs show full processing
- Triggers PDF generation at end
- Updates DynamoDB with COMPLETE status

**PDF Generator Lambda:**
- Triggered by ECS task
- Generates PDF successfully
- Updates DynamoDB with PDF URL

---

## Success Criteria

The optimization is successful if:
1. ✅ Step Functions completes in ~20 seconds (not 5 minutes)
2. ✅ ECS task runs in background and completes successfully
3. ✅ PDF is generated and URL is available
4. ✅ DynamoDB shows COMPLETE status
5. ✅ Frontend displays PDF download link
6. ✅ No duplicate PDF generation

---

## Additional Optimizations (Future)

### 1. Reduce ECS Cold Start
- Use smaller Docker image (~2 GB instead of 4.4 GB)
- Pre-warm containers with scheduled tasks
- Use Fargate Spot for 50% cost savings

### 2. Optimize Chord Detection
- Cache librosa models
- Use faster algorithms for simple songs
- Parallel processing of audio chunks

### 3. Add Progress Checkpoints
- More granular progress updates (10+ checkpoints)
- Real-time streaming of chord detection results
- WebSocket updates instead of polling

---

**Status: DEPLOYED AND READY FOR TESTING ✅**

The optimized workflow is now live in dev. Step Functions will complete in ~20 seconds instead of 5 minutes, while the actual processing continues in the background with real-time progress updates.
