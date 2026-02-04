# Workflow Timing Optimization

**Date:** February 4, 2026  
**Issue:** Transcription taking too long to complete

---

## Current Timing Breakdown

### Total Time: ~5-6 minutes

1. **YouTube Download** (~10s)
   - Fast, no issues

2. **Parallel Processing:**
   - **Lyrics Transcription** (~8s) - Deepgram Nova-3
   - **Chord Detection (ECS)** (~4-5 minutes) ⚠️ BOTTLENECK
     - Fargate cold start: ~3 minutes
     - Audio loading: ~23s
     - Tempo detection: ~21s
     - Chromagram: ~2s
     - Chord detection: ~15s
     - Key detection: ~0.3s
     - Structure detection: ~0.1s
     - DynamoDB update: ~0.5s

3. **PDF Generation** (~0.4s)
   - Fast, no issues

---

## The Problem

### Step Functions Uses `ecs:runTask.sync`

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::ecs:runTask.sync",
  ...
}
```

The `.sync` suffix means **Step Functions waits for the entire ECS task to complete** before proceeding to PDF generation.

### Why This Is Slow

1. **Fargate Cold Start: 3 minutes**
   - ECS needs to provision a new container
   - Download Docker image (4.4 GB)
   - Start container
   - This happens EVERY time (no warm containers)

2. **Step Functions Waits**
   - Blocks on ECS task completion
   - Can't proceed to PDF generation
   - Even though ECS task triggers PDF itself!

---

## Current Architecture (Redundant)

```
Step Functions
  ├─ YouTube Download (10s)
  ├─ Parallel:
  │   ├─ Lyrics (8s) ✓
  │   └─ Chords (ECS .sync) → WAITS 5 minutes ⚠️
  └─ PDF Generation (0.4s)
       ↑
       └─ Also triggered by ECS task! (redundant)
```

The ECS task **already triggers PDF generation** at the end, so Step Functions doesn't need to wait or call it again.

---

## Solution Options

### Option 1: Remove `.sync` (Quick Fix)
Change `ecs:runTask.sync` to `ecs:runTask` (async)

**Pros:**
- Step Functions doesn't wait for ECS
- Workflow completes in ~20s (download + lyrics + trigger ECS)
- ECS continues in background

**Cons:**
- Step Functions shows "complete" before actual completion
- Need to rely on DynamoDB status for true completion

### Option 2: Remove PDF Generation from Step Functions (Better)
Since ECS already triggers PDF, remove it from Step Functions entirely

**Current Flow:**
```
Step Functions → ECS (sync) → Step Functions PDF → Complete
                  ↓
                  ECS also triggers PDF (redundant!)
```

**Optimized Flow:**
```
Step Functions → ECS (async) → Complete
                  ↓
                  ECS → PDF → DynamoDB (COMPLETE)
```

**Pros:**
- No redundant PDF generation
- Step Functions completes in ~20s
- ECS handles everything after audio download
- Cleaner architecture

**Cons:**
- Step Functions doesn't track final completion
- Must check DynamoDB for true status

### Option 3: Keep Warm ECS Tasks (Expensive)
Use ECS Service with minimum 1 task always running

**Pros:**
- No cold start delay
- Faster chord detection (~2 minutes instead of 5)

**Cons:**
- Costs ~$30-50/month for idle container
- Still slower than async approach
- Overkill for dev environment

---

## Recommended Solution

### Use Option 2: Async ECS + Remove Redundant PDF

**Changes Needed:**

1. **Update Step Functions Workflow:**
```json
{
  "ChordDetection": {
    "Type": "Task",
    "Resource": "arn:aws:states:::ecs:runTask",  // Remove .sync
    "Parameters": { ... },
    "End": true  // Don't wait, don't call PDF
  }
}
```

2. **Remove PDFGeneration State:**
```json
{
  "ParallelAnalysis": {
    "Type": "Parallel",
    "Branches": [ ... ],
    "End": true  // End after parallel, no PDF step
  }
}
```

3. **Frontend Polling:**
Frontend already polls DynamoDB for status, so it will see:
- `DOWNLOADING` (10s)
- `TRANSCRIBING_LYRICS` (8s)
- `DETECTING_CHORDS` (5 minutes)
- `GENERATING_PDF` (0.4s)
- `COMPLETE` (with PDF URL)

---

## Expected Results After Optimization

### Step Functions Execution Time
- **Before:** 5-6 minutes (waits for ECS)
- **After:** ~20 seconds (download + lyrics + trigger ECS)

### Actual Completion Time
- **Same:** ~5-6 minutes (ECS still takes time)
- **But:** User sees progress updates throughout
- **And:** Step Functions doesn't block

### User Experience
- Step Functions shows "complete" quickly
- Frontend continues polling DynamoDB
- Progress bar shows real status:
  - 10% - Downloading
  - 40% - Transcribing lyrics
  - 70% - Detecting chords (ECS running)
  - 90% - Generating PDF
  - 100% - Complete

---

## Implementation

### 1. Update Step Functions Definition

```bash
# Edit backend/step-functions-v2/transcription-workflow-new.json
# Change: "ecs:runTask.sync" → "ecs:runTask"
# Remove: PDFGeneration state
# Set: ParallelAnalysis.End = true
```

### 2. Deploy Updated Workflow

```bash
aws stepfunctions update-state-machine \
  --state-machine-arn "arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-V2-Transcription-dev" \
  --definition file://backend/step-functions-v2/transcription-workflow-new.json \
  --profile chordscout \
  --region us-east-1
```

### 3. Test

Submit a new job and verify:
- Step Functions completes in ~20s
- DynamoDB shows progress updates
- ECS task completes chord detection
- PDF is generated
- Final status is COMPLETE

---

## Alternative: Reduce ECS Cold Start

If we want to keep `.sync` but reduce time:

### Use Fargate Spot (50% cheaper, same speed)
```json
{
  "LaunchType": "FARGATE",
  "CapacityProviderStrategy": [
    {
      "capacityProvider": "FARGATE_SPOT",
      "weight": 1
    }
  ]
}
```

### Use Smaller Docker Image
- Current: 4.4 GB
- Optimized: ~2 GB (remove unnecessary dependencies)
- Saves ~1 minute on cold start

### Pre-warm Container (Scheduled Task)
Run a dummy ECS task every 10 minutes to keep container warm
- Costs ~$5/month
- Reduces cold start to ~30s

---

## Recommendation

**For Dev:** Use Option 2 (async ECS, no wait)
- Fast Step Functions execution
- No extra costs
- Clean architecture

**For Production:** Consider warm containers or smaller image
- Better user experience
- Worth the cost for production traffic

---

## Current Status

- ✅ Font size reduced to 36px
- ⚠️ Workflow still uses `.sync` (waits for ECS)
- 📋 Need to update Step Functions to async

**Next Step:** Update Step Functions workflow to remove `.sync` and redundant PDF generation.
