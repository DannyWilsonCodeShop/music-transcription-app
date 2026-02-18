# Downbeat Confirmation Feature - Deployment Guide

## Overview

This guide covers the deployment of the downbeat confirmation feature, which allows users to verify and adjust the detected downbeat before chord detection runs.

## What Was Created

### Frontend Components

1. **React Component**: `src/components/DownbeatConfirmation.tsx`
   - Visual waveform with beat markers
   - Audio playback with click track
   - Interactive downbeat adjustment
   - Time signature selection
   - User confirmation workflow

### Backend Lambda Functions

2. **Downbeat Detector**: `backend/functions-v2/downbeat-detector/`
   - Detects tempo, beats, and downbeat from audio
   - Returns data for user confirmation UI
   - Uses 3 complementary detection methods

3. **Confirm Downbeat**: `backend/functions-v2/confirm-downbeat/`
   - Saves user-confirmed downbeat and time signature
   - Triggers ECS chord detection task with confirmed values

### Updated Files

4. **Chord Detection Pipeline**: `simple-pipeline/chord-detection/chord_detection_v2.py`
   - Added `confirmed_downbeat` parameter to `detect_chords_complete()`
   - Added `confirmed_time_signature` parameter
   - Adjusts beat grid to align with confirmed downbeat

5. **Dependencies**: `package.json`
   - Added `lucide-react` for UI icons

## Architecture Flow

```
1. User uploads audio
   ↓
2. File upload handler saves to S3
   ↓
3. POST /api/detect-downbeat
   ├─ Downloads audio from S3
   ├─ Runs Python downbeat detection
   ├─ Returns: tempo, beats, downbeat, confidence
   └─ Saves to DynamoDB
   ↓
4. Frontend shows DownbeatConfirmation modal
   ├─ Displays waveform with beat markers
   ├─ Plays audio with click track
   ├─ User adjusts if needed
   └─ User confirms or cancels
   ↓
5. POST /api/confirm-downbeat
   ├─ Saves confirmed values to DynamoDB
   └─ Triggers ECS chord detection task
   ↓
6. ECS task runs chord detection
   ├─ Reads confirmed downbeat from environment
   ├─ Aligns beat grid to confirmed downbeat
   └─ Detects chords with correct measure alignment
   ↓
7. Results displayed with accurate measure numbers
```

## Deployment Steps

### Step 1: Install Frontend Dependencies

```bash
npm install lucide-react
```

### Step 2: Deploy Lambda Functions

#### Downbeat Detector Lambda

```bash
cd backend/functions-v2/downbeat-detector
npm install
zip -r downbeat-detector.zip .

# Upload to Lambda
aws lambda create-function \
  --function-name chordscout-downbeat-detector-dev \
  --runtime nodejs18.x \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
  --handler index.handler \
  --zip-file fileb://downbeat-detector.zip \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables="{JOBS_TABLE=ChordScout-Jobs-V2-dev}"

# Or update existing function
aws lambda update-function-code \
  --function-name chordscout-downbeat-detector-dev \
  --zip-file fileb://downbeat-detector.zip
```

#### Confirm Downbeat Lambda

```bash
cd backend/functions-v2/confirm-downbeat
npm install
zip -r confirm-downbeat.zip .

# Upload to Lambda
aws lambda create-function \
  --function-name chordscout-confirm-downbeat-dev \
  --runtime nodejs18.x \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
  --handler index.handler \
  --zip-file fileb://confirm-downbeat.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables="{JOBS_TABLE=ChordScout-Jobs-V2-dev,ECS_CLUSTER=chord-detection-cluster,ECS_TASK_DEFINITION=chord-detector,ECS_SUBNETS=subnet-xxx,ECS_SECURITY_GROUPS=sg-xxx}"

# Or update existing function
aws lambda update-function-code \
  --function-name chordscout-confirm-downbeat-dev \
  --zip-file fileb://confirm-downbeat.zip
```

### Step 3: Add API Gateway Routes

Add these routes to your API Gateway:

```yaml
# POST /api/detect-downbeat
/api/detect-downbeat:
  post:
    x-amazon-apigateway-integration:
      uri: arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:ACCOUNT_ID:function:chordscout-downbeat-detector-dev/invocations
      httpMethod: POST
      type: aws_proxy

# POST /api/confirm-downbeat
/api/confirm-downbeat:
  post:
    x-amazon-apigateway-integration:
      uri: arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:ACCOUNT_ID:function:chordscout-confirm-downbeat-dev/invocations
      httpMethod: POST
      type: aws_proxy
```

### Step 4: Update ECS Task Definition

Update the chord detector ECS task to accept confirmed downbeat:

```json
{
  "containerDefinitions": [
    {
      "name": "chord-detector",
      "environment": [
        {"name": "JOB_ID", "value": ""},
        {"name": "AUDIO_BUCKET", "value": ""},
        {"name": "AUDIO_KEY", "value": ""},
        {"name": "CONFIRMED_DOWNBEAT", "value": ""},
        {"name": "CONFIRMED_TIME_SIGNATURE", "value": ""},
        {"name": "JOBS_TABLE", "value": "ChordScout-Jobs-V2-dev"}
      ]
    }
  ]
}
```

### Step 5: Update ECS App to Use Confirmed Values

Update `simple-pipeline/chord-detection/app.py` or `backend/functions-v2/chord-detector-ecs/app.py`:

```python
# Get confirmed values from environment
confirmed_downbeat = os.environ.get('CONFIRMED_DOWNBEAT')
confirmed_time_signature = os.environ.get('CONFIRMED_TIME_SIGNATURE')

# Convert to proper types
if confirmed_downbeat:
    confirmed_downbeat = float(confirmed_downbeat)
if not confirmed_time_signature:
    confirmed_time_signature = None

# Run chord detection with confirmed values
chords_data = detect_chords_complete(
    audio_path,
    confirmed_downbeat=confirmed_downbeat,
    confirmed_time_signature=confirmed_time_signature
)
```

### Step 6: Integrate React Component

Update your upload workflow component (e.g., `src/pages/Upload.tsx` or similar):

```typescript
import { DownbeatConfirmation } from '../components/DownbeatConfirmation';

function UploadPage() {
  const [showDownbeatConfirmation, setShowDownbeatConfirmation] = useState(false);
  const [downbeatData, setDownbeatData] = useState(null);
  const [currentJobId, setCurrentJobId] = useState(null);

  const handleFileUpload = async (file: File) => {
    // 1. Upload file
    const { jobId, uploadUrl } = await requestUploadUrl(file.name, file.type);
    await uploadToS3(uploadUrl, file);
    
    setCurrentJobId(jobId);
    
    // 2. Detect downbeat
    const response = await fetch(`${API_BASE_URL}/api/detect-downbeat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jobId,
        bucket: 'your-bucket',
        key: `uploads/${jobId}/${file.name}`
      })
    });
    
    const data = await response.json();
    
    // 3. Show confirmation modal
    setDownbeatData({
      audioUrl: uploadUrl, // Or generate a presigned URL
      downbeat: data.detectedDownbeat,
      tempo: data.tempo,
      timeSignature: data.timeSignature,
      beatTimes: data.beatTimes
    });
    setShowDownbeatConfirmation(true);
  };

  const handleDownbeatConfirm = async (downbeat: number, timeSignature: string) => {
    // Save confirmed values and trigger chord detection
    await fetch(`${API_BASE_URL}/api/confirm-downbeat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jobId: currentJobId,
        downbeat,
        timeSignature
      })
    });
    
    setShowDownbeatConfirmation(false);
    
    // Start polling for job status
    pollJobStatus(currentJobId);
  };

  return (
    <>
      {/* Your upload UI */}
      
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
    </>
  );
}
```

### Step 7: Deploy Frontend

```bash
npm run build
# Deploy to your hosting service (Amplify, S3+CloudFront, etc.)
```

## Testing Checklist

### Backend Testing

- [ ] Test downbeat detector Lambda with sample audio
- [ ] Verify JSON output format is correct
- [ ] Test confirm downbeat Lambda
- [ ] Verify DynamoDB updates correctly
- [ ] Verify ECS task is triggered with correct environment variables
- [ ] Test chord detection with confirmed downbeat

### Frontend Testing

- [ ] Component renders correctly
- [ ] Audio plays when clicking play button
- [ ] Click track generates and plays
- [ ] Waveform shows beat markers (red for downbeats, blue for beats)
- [ ] Previous/next buttons adjust downbeat correctly
- [ ] Time signature selector works
- [ ] Confirm button calls API with correct values
- [ ] Cancel button closes modal
- [ ] Workflow continues after confirmation

### Integration Testing

- [ ] Upload audio file
- [ ] Downbeat detection runs automatically
- [ ] Confirmation modal appears
- [ ] User can listen and adjust
- [ ] Chord detection uses confirmed values
- [ ] Measure numbers are accurate in output
- [ ] Can go back and re-confirm if needed

## Environment Variables

### Lambda Functions

**downbeat-detector**:
- `JOBS_TABLE`: DynamoDB table name (e.g., `ChordScout-Jobs-V2-dev`)

**confirm-downbeat**:
- `JOBS_TABLE`: DynamoDB table name
- `ECS_CLUSTER`: ECS cluster name
- `ECS_TASK_DEFINITION`: ECS task definition name
- `ECS_SUBNETS`: Comma-separated subnet IDs
- `ECS_SECURITY_GROUPS`: Comma-separated security group IDs

### ECS Task

**chord-detector**:
- `JOB_ID`: Job identifier
- `AUDIO_BUCKET`: S3 bucket with audio file
- `AUDIO_KEY`: S3 key for audio file
- `CONFIRMED_DOWNBEAT`: User-confirmed downbeat time (seconds)
- `CONFIRMED_TIME_SIGNATURE`: User-confirmed time signature (e.g., "4/4")
- `JOBS_TABLE`: DynamoDB table name

## Troubleshooting

### Click track not playing
- Check browser audio permissions
- Verify Web Audio API is supported
- Check console for errors
- Try different browser

### Waveform not showing beats
- Verify `beatTimes` array is populated
- Check canvas rendering in browser dev tools
- Ensure downbeat is within audio duration

### Audio not loading
- Check `audioUrl` is accessible
- Verify CORS headers on S3 bucket
- Check network tab for 404/403 errors
- Generate presigned URL if needed

### Downbeat adjustment not working
- Verify `beatTimes` array is sorted
- Check `currentDownbeat` is in `beatTimes`
- Ensure React state updates correctly

### Chord detection not using confirmed downbeat
- Check ECS task environment variables
- Verify `CONFIRMED_DOWNBEAT` is passed correctly
- Check ECS task logs for confirmation
- Verify `detect_chords_complete()` receives parameter

## Rollback Plan

If issues occur:

1. **Frontend**: Remove downbeat confirmation modal, skip directly to chord detection
2. **Backend**: Update confirm-downbeat Lambda to skip ECS trigger, use old workflow
3. **ECS**: Remove confirmed downbeat parameters, use auto-detected values

## Next Steps

After successful deployment:

1. Monitor user feedback on downbeat accuracy
2. Collect metrics on how often users adjust the downbeat
3. Improve auto-detection algorithms based on adjustment patterns
4. Add advanced features:
   - Waveform from actual audio (not placeholder)
   - Visual feedback during playback
   - Fine-tune with slider
   - Save/load presets

## Files Modified/Created

### Created
- `src/components/DownbeatConfirmation.tsx`
- `backend/functions-v2/downbeat-detector/index.js`
- `backend/functions-v2/downbeat-detector/detect_downbeat.py`
- `backend/functions-v2/downbeat-detector/package.json`
- `backend/functions-v2/confirm-downbeat/index.js`
- `backend/functions-v2/confirm-downbeat/package.json`
- `DOWNBEAT_CONFIRMATION_DEPLOYMENT_GUIDE.md`

### Modified
- `simple-pipeline/chord-detection/chord_detection_v2.py`
- `package.json` (added lucide-react)

## Support

For issues or questions:
1. Check CloudWatch logs for Lambda functions
2. Check ECS task logs
3. Check browser console for frontend errors
4. Review this deployment guide
5. Refer to `DOWNBEAT_UI_INTEGRATION_GUIDE.md` for detailed integration instructions

---

**Status**: Ready for deployment to dev branch
**Last Updated**: February 18, 2026
