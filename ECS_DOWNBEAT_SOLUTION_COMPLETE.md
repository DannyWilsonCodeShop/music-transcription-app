# ECS-Based Downbeat Detection Solution - Complete

## Problem Solved

Lambda layers have a 250MB unzipped size limit. Librosa + dependencies exceed this limit, making it impossible to run Python audio processing in Lambda directly.

## Solution: ECS-Based Architecture

Instead of trying to fit librosa into a Lambda layer, we moved the heavy processing to ECS where we already have all Python libraries installed.

### Architecture Flow

```
User Upload → Lambda (downbeat-detector) → ECS Task (downbeat-detector-ecs)
                                              ↓
                                         DynamoDB (downbeatData)
                                              ↓
Frontend Polls → Shows Confirmation Modal → User Confirms
                                              ↓
                                         Lambda (confirm-downbeat)
                                              ↓
                                         ECS Task (chord-detector-ecs)
                                              ↓
                                         Uses Confirmed Downbeat
```

## What Was Implemented

### 1. Updated downbeat-detector Lambda
**File**: `backend/functions-v2/downbeat-detector/index.js`

- **Before**: Tried to run Python script with librosa (impossible due to layer size)
- **After**: Triggers ECS task for downbeat detection
- **Returns**: 202 Accepted (async processing)
- **Environment Variables**:
  - `ECS_CLUSTER=ChordScout-dev`
  - `ECS_TASK_DEFINITION=chordscout-downbeat-detector-dev`
  - `ECS_SUBNETS=subnet-01a9aca5a7a25f7b4,subnet-025cbdacce40039e8`
  - `ECS_SECURITY_GROUPS=sg-0f34e2bad6dda9b0f`

### 2. Created downbeat-detector-ecs Task
**Files**:
- `backend/functions-v2/downbeat-detector-ecs/app.py`
- `backend/functions-v2/downbeat-detector-ecs/Dockerfile`
- `backend/functions-v2/downbeat-detector-ecs/requirements.txt`

**Purpose**: Runs downbeat detection in ECS with full Python environment

**Process**:
1. Downloads audio from S3
2. Calls `downbeat_detection.detect_downbeats_complete()`
3. Saves results to DynamoDB `downbeatData` field:
   ```json
   {
     "tempo": 120.5,
     "timeSignature": "4/4",
     "detectedDownbeat": 2.090,
     "confidence": 0.85,
     "beatTimes": [0.5, 1.0, 1.5, ...],
     "downbeats": [2.090, 4.090, 6.090, ...],
     "totalBeats": 256,
     "totalMeasures": 64
   }
   ```

### 3. Updated chord-detector-ecs to Use Confirmed Downbeat
**File**: `backend/functions-v2/chord-detector-ecs/app.py`

**Changes**:
- Reads `CONFIRMED_DOWNBEAT` from environment
- Reads `CONFIRMED_TIME_SIGNATURE` from environment
- Adjusts beat alignment to match confirmed downbeat
- Logs confirmed values for debugging

**Code Added**:
```python
# Get confirmed downbeat values (if provided by user)
confirmed_downbeat = os.environ.get('CONFIRMED_DOWNBEAT')
confirmed_time_signature = os.environ.get('CONFIRMED_TIME_SIGNATURE')

if confirmed_downbeat:
    confirmed_downbeat = float(confirmed_downbeat)
    log(f"✓ Using CONFIRMED downbeat: {confirmed_downbeat}s")
```

**Beat Alignment Logic**:
```python
if confirmed_downbeat is not None:
    # Find the beat closest to the confirmed downbeat
    closest_beat_idx = np.argmin(np.abs(beat_times - confirmed_downbeat))
    
    # Calculate beats per measure from time signature
    beats_per_measure = int(time_signature.split('/')[0])
    
    # Adjust beats so confirmed downbeat aligns with measure start
    beat_offset = closest_beat_idx % beats_per_measure
    if beat_offset != 0:
        beats = beats[beat_offset:]
```

## Benefits of This Approach

### 1. No Size Limits
- ECS containers can be any size
- Full Python environment with all libraries
- No need to optimize or strip dependencies

### 2. Consistent Environment
- Same Python environment for downbeat detection and chord detection
- No version mismatches between Lambda layer and ECS
- Easier to maintain and debug

### 3. Better Performance
- No Lambda cold start for Python libraries
- ECS tasks stay warm longer
- Can scale independently

### 4. Clean Separation
- **Lambda**: Lightweight orchestration, API handling
- **ECS**: Heavy processing, audio analysis
- Each component does what it's best at

### 5. Cost Effective
- Lambda only runs for seconds (orchestration)
- ECS only runs when needed (processing)
- No need to keep Lambda warm

## Next Steps

### 1. Build and Deploy downbeat-detector-ecs Docker Image

```bash
# Build Docker image
cd backend/functions-v2/downbeat-detector-ecs
docker build -t chordscout-downbeat-detector:latest .

# Tag for ECR
docker tag chordscout-downbeat-detector:latest \
  090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-downbeat-detector:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 --profile chordscout | \
  docker login --username AWS --password-stdin \
  090130568474.dkr.ecr.us-east-1.amazonaws.com

docker push 090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-downbeat-detector:latest
```

### 2. Create ECS Task Definition

```bash
aws ecs register-task-definition \
  --family chordscout-downbeat-detector-dev \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu 1024 \
  --memory 2048 \
  --execution-role-arn arn:aws:iam::090130568474:role/ecsTaskExecutionRole \
  --task-role-arn arn:aws:iam::090130568474:role/ChordScout-ECS-Task-Role \
  --container-definitions '[
    {
      "name": "downbeat-detector",
      "image": "090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-downbeat-detector:latest",
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/chordscout-downbeat-detector-dev",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]' \
  --profile chordscout
```

### 3. Update Frontend to Poll for Downbeat Results

The frontend currently expects immediate results from `/api/detect-downbeat`. Update it to poll:

```typescript
// After calling /api/detect-downbeat (which returns 202)
const pollForDownbeat = async (jobId: string) => {
  const maxAttempts = 30; // 30 seconds
  for (let i = 0; i < maxAttempts; i++) {
    const status = await getJobStatus(jobId);
    
    if (status.downbeatData && status.downbeatStatus === 'COMPLETED') {
      return status.downbeatData;
    }
    
    if (status.downbeatStatus === 'FAILED') {
      throw new Error('Downbeat detection failed');
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  throw new Error('Downbeat detection timed out');
};
```

### 4. Test End-to-End

1. Upload audio file
2. Verify ECS task starts for downbeat detection
3. Check CloudWatch logs for downbeat-detector-ecs
4. Verify downbeatData appears in DynamoDB
5. Verify frontend shows confirmation modal
6. Confirm downbeat
7. Verify chord-detector-ecs receives CONFIRMED_DOWNBEAT
8. Verify measure alignment is correct

## Files Modified

- `backend/functions-v2/downbeat-detector/index.js` - ECS trigger instead of Python
- `backend/functions-v2/chord-detector-ecs/app.py` - Confirmed downbeat support
- `.gitignore` - Added *.zip to ignore large deployment packages

## Files Created

- `backend/functions-v2/downbeat-detector-ecs/app.py` - ECS downbeat detection
- `backend/functions-v2/downbeat-detector-ecs/Dockerfile` - Container definition
- `backend/functions-v2/downbeat-detector-ecs/requirements.txt` - Python dependencies

## Git Commit

**Branch**: `dev`
**Commit**: `2739acd`
**Message**: "Implement ECS-based downbeat detection and confirmed downbeat support"

## Why This Is Better

### Original Approach (Failed)
- ❌ Lambda layer with librosa (144MB compressed, >250MB unzipped)
- ❌ Hit AWS size limits
- ❌ Would need to strip dependencies
- ❌ Potential version conflicts

### New Approach (Success)
- ✅ ECS task with full Python environment
- ✅ No size limits
- ✅ Consistent with chord detection
- ✅ Better architecture
- ✅ Easier to maintain

## Status

- ✅ Lambda updated to trigger ECS
- ✅ ECS task code written
- ✅ Dockerfile created
- ✅ Chord detector updated for confirmed downbeat
- ✅ Code committed and pushed
- ⏳ Docker image needs to be built and pushed to ECR
- ⏳ ECS task definition needs to be registered
- ⏳ Frontend needs polling logic update
- ⏳ End-to-end testing needed

---

**Next Action**: Build and deploy the downbeat-detector-ecs Docker image to ECR
