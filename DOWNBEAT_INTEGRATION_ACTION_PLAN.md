# Downbeat Integration Action Plan

## Current Status

✅ **Frontend Deployed**: The DownbeatConfirmation component is live at https://dev.dqg97bbmmprz.amplifyapp.com/
✅ **Code Pushed**: All code is in the dev branch on GitHub
❌ **Not Integrated**: Component exists but isn't being called in the upload workflow
❌ **Backend Not Deployed**: Lambda functions need to be deployed to AWS

## Why It's Not Showing

The DownbeatConfirmation component was deployed, but it's not integrated into the upload workflow in `src/App.tsx`. The component needs to be:
1. Imported
2. Called after file upload
3. Connected to backend API endpoints (which don't exist yet)

## What Needs to Happen

### Step 1: Deploy Backend Lambda Functions (REQUIRED FIRST)

The downbeat confirmation feature requires two Lambda functions that aren't deployed yet:

#### A. Deploy downbeat-detector Lambda

```bash
cd backend/functions-v2/downbeat-detector
npm install

# Create deployment package
zip -r downbeat-detector.zip index.js detect_downbeat.py package.json node_modules/

# Deploy to AWS (using chordscout profile)
export AWS_PROFILE=chordscout
aws lambda create-function \
  --function-name chordscout-downbeat-detector-dev \
  --runtime nodejs18.x \
  --role arn:aws:iam::090130568474:role/lambda-execution-role \
  --handler index.handler \
  --zip-file fileb://downbeat-detector.zip \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables="{JOBS_TABLE=ChordScout-Jobs-V2-dev}"
```

#### B. Deploy confirm-downbeat Lambda

```bash
cd backend/functions-v2/confirm-downbeat
npm install

# Create deployment package
zip -r confirm-downbeat.zip index.js package.json node_modules/

# Deploy to AWS
export AWS_PROFILE=chordscout
aws lambda create-function \
  --function-name chordscout-confirm-downbeat-dev \
  --runtime nodejs18.x \
  --role arn:aws:iam::090130568474:role/lambda-execution-role \
  --handler index.handler \
  --zip-file fileb://confirm-downbeat.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables="{JOBS_TABLE=ChordScout-Jobs-V2-dev,ECS_CLUSTER=chord-detection-cluster,ECS_TASK_DEFINITION=chord-detector,ECS_SUBNETS=subnet-xxx,ECS_SECURITY_GROUPS=sg-xxx}"
```

### Step 2: Add API Gateway Routes

Add these routes to your API Gateway (https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com):

1. **POST /api/detect-downbeat**
   - Integration: Lambda proxy to `chordscout-downbeat-detector-dev`
   - CORS enabled

2. **POST /api/confirm-downbeat**
   - Integration: Lambda proxy to `chordscout-confirm-downbeat-dev`
   - CORS enabled

### Step 3: Update App.tsx to Integrate Component

Once the backend is deployed, update `src/App.tsx`:

```typescript
import { DownbeatConfirmation } from './components/DownbeatConfirmation';

// Add state for downbeat confirmation
const [showDownbeatConfirmation, setShowDownbeatConfirmation] = useState(false);
const [downbeatData, setDownbeatData] = useState<any>(null);

// After successful upload, detect downbeat
const handleUpload = async () => {
  // ... existing upload code ...
  
  // After upload completes:
  console.log('Upload complete, detecting downbeat...');
  
  try {
    const downbeatResponse = await axios.post(`${API_ENDPOINT}/api/detect-downbeat`, {
      jobId: newJobId,
      bucket: 'your-bucket-name',
      key: `uploads/${newJobId}/${file.name}`
    });
    
    setDownbeatData({
      audioUrl: uploadUrl, // Or generate presigned URL
      downbeat: downbeatResponse.data.detectedDownbeat,
      tempo: downbeatResponse.data.tempo,
      timeSignature: downbeatResponse.data.timeSignature,
      beatTimes: downbeatResponse.data.beatTimes
    });
    
    setShowDownbeatConfirmation(true);
  } catch (error) {
    console.error('Downbeat detection failed:', error);
    // Continue without confirmation (fallback)
  }
};

// Handle downbeat confirmation
const handleDownbeatConfirm = async (downbeat: number, timeSignature: string) => {
  try {
    await axios.post(`${API_ENDPOINT}/api/confirm-downbeat`, {
      jobId,
      downbeat,
      timeSignature
    });
    
    setShowDownbeatConfirmation(false);
    // Chord detection will start automatically via ECS
  } catch (error) {
    console.error('Failed to confirm downbeat:', error);
    setError('Failed to confirm downbeat');
  }
};

// Add to JSX (before closing div):
{showDownbeatConfirmation && downbeatData && (
  <DownbeatConfirmation
    audioUrl={downbeatData.audioUrl}
    detectedDownbeat={downbeatData.downbeat}
    detectedTempo={downbeatData.tempo}
    detectedTimeSignature={downbeatData.timeSignature}
    beatTimes={downbeatData.beatTimes}
    onConfirm={handleDownbeatConfirm}
    onCancel={() => setShowDownbeatConfirmation(false)}
  />
)}
```

### Step 4: Update ECS Task to Use Confirmed Downbeat

Update the chord-detector ECS task to read confirmed downbeat:

```python
# In simple-pipeline/chord-detection/app.py or backend/functions-v2/chord-detector-ecs/app.py

# Get confirmed values from environment
confirmed_downbeat = os.environ.get('CONFIRMED_DOWNBEAT')
confirmed_time_signature = os.environ.get('CONFIRMED_TIME_SIGNATURE')

# Convert to proper types
if confirmed_downbeat:
    confirmed_downbeat = float(confirmed_downbeat)
if not confirmed_time_signature:
    confirmed_time_signature = None

# Run chord detection with confirmed values
from chord_detection_v2 import detect_chords_complete

results = detect_chords_complete(
    audio_path,
    confirmed_downbeat=confirmed_downbeat,
    confirmed_time_signature=confirmed_time_signature
)
```

### Step 5: Test End-to-End

1. Upload audio file
2. Verify downbeat detection modal appears
3. Play audio with click track
4. Confirm or adjust downbeat
5. Verify chord detection uses confirmed values
6. Check that measure numbers are correct in results

## Quick Test (Without Full Integration)

If you want to test the component in isolation:

1. Open browser console on https://dev.dqg97bbmmprz.amplifyapp.com/
2. Manually trigger the component:

```javascript
// This won't work yet because the component isn't imported in App.tsx
// But shows what the integration would look like
```

## Why This Matters

**Without downbeat confirmation**:
- Auto-detected first beat was 3.1 beats off (beat 4 instead of beat 1)
- ALL 1024 chords placed in wrong measures
- Measure numbers incorrect throughout

**With downbeat confirmation**:
- User verifies the downbeat is correct
- All chords placed in correct measures
- Accurate measure numbers for musicians
- Professional-quality output

## Summary

The component is deployed but dormant. To activate it:

1. ✅ Code is in dev branch
2. ✅ Component is deployed to Amplify
3. ❌ Backend Lambda functions need deployment
4. ❌ API Gateway routes need to be added
5. ❌ App.tsx needs integration code
6. ❌ ECS task needs to read confirmed values

**Next Action**: Deploy the Lambda functions, then integrate into App.tsx

---

**Status**: Component deployed but not integrated
**Blocker**: Backend Lambda functions not deployed
**Priority**: High (fixes critical measure alignment issue)
