# Downbeat Confirmation - Quick Reference

## Overview

User confirms the detected downbeat before chord detection to ensure accurate measure alignment.

## Workflow

```
Upload → Detect Downbeat → User Confirms → Chord Detection → Results
```

## API Endpoints

### 1. Detect Downbeat

```http
POST /api/detect-downbeat
Content-Type: application/json

{
  "jobId": "job-123",
  "bucket": "audio-bucket",
  "key": "uploads/audio.m4a"
}
```

**Response**:
```json
{
  "tempo": 136.0,
  "timeSignature": "4/4",
  "detectedDownbeat": 1.625,
  "confidence": 0.362,
  "beatTimes": [0.720, 1.184, 1.625, ...],
  "downbeats": [1.625, 3.413, 5.201, ...]
}
```

### 2. Confirm Downbeat

```http
POST /api/confirm-downbeat
Content-Type: application/json

{
  "jobId": "job-123",
  "downbeat": 1.625,
  "timeSignature": "4/4"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Downbeat confirmed, chord detection started"
}
```

## React Component

```tsx
import { DownbeatConfirmation } from './components/DownbeatConfirmation';

<DownbeatConfirmation
  audioUrl="https://..."
  detectedDownbeat={1.625}
  detectedTempo={136.0}
  detectedTimeSignature="4/4"
  beatTimes={[0.720, 1.184, 1.625, ...]}
  onConfirm={(downbeat, timeSignature) => {
    // Save and continue
  }}
  onCancel={() => {
    // Cancel workflow
  }}
/>
```

## Python Function

```python
from chord_detection_v2 import detect_chords_complete

results = detect_chords_complete(
    audio_path="audio.m4a",
    confirmed_downbeat=1.625,
    confirmed_time_signature="4/4"
)
```

## Environment Variables

### Lambda: downbeat-detector
- `JOBS_TABLE` - DynamoDB table name

### Lambda: confirm-downbeat
- `JOBS_TABLE` - DynamoDB table name
- `ECS_CLUSTER` - ECS cluster name
- `ECS_TASK_DEFINITION` - Task definition name
- `ECS_SUBNETS` - Comma-separated subnet IDs
- `ECS_SECURITY_GROUPS` - Comma-separated security group IDs

### ECS: chord-detector
- `JOB_ID` - Job identifier
- `AUDIO_BUCKET` - S3 bucket
- `AUDIO_KEY` - S3 key
- `CONFIRMED_DOWNBEAT` - Confirmed downbeat (seconds)
- `CONFIRMED_TIME_SIGNATURE` - Confirmed time signature
- `JOBS_TABLE` - DynamoDB table name

## Files

### Created
- `backend/functions-v2/downbeat-detector/` - Lambda function
- `backend/functions-v2/confirm-downbeat/` - Lambda function
- `src/components/DownbeatConfirmation.tsx` - React component

### Modified
- `simple-pipeline/chord-detection/chord_detection_v2.py` - Added parameters
- `package.json` - Added lucide-react

## Deployment Commands

```bash
# Install frontend dependencies
npm install lucide-react

# Deploy downbeat detector
cd backend/functions-v2/downbeat-detector
npm install
zip -r downbeat-detector.zip .
aws lambda create-function --function-name chordscout-downbeat-detector-dev ...

# Deploy confirm downbeat
cd backend/functions-v2/confirm-downbeat
npm install
zip -r confirm-downbeat.zip .
aws lambda create-function --function-name chordscout-confirm-downbeat-dev ...

# Build frontend
npm run build
```

## Testing

```bash
# Test downbeat detection
curl -X POST https://api.../api/detect-downbeat \
  -H "Content-Type: application/json" \
  -d '{"jobId":"test-123","bucket":"bucket","key":"audio.m4a"}'

# Test confirmation
curl -X POST https://api.../api/confirm-downbeat \
  -H "Content-Type: application/json" \
  -d '{"jobId":"test-123","downbeat":1.625,"timeSignature":"4/4"}'
```

## Key Benefits

1. **Accurate Measures** - First beat ≠ first downbeat (often off by 2-3 beats)
2. **User Control** - Listen and adjust if needed
3. **Visual Feedback** - Waveform with beat markers
4. **Audio Feedback** - Click track for verification
5. **Confidence Score** - Know when to adjust

## Common Issues

### Click track not playing
- Check browser audio permissions
- Try different browser

### Waveform not showing
- Verify beatTimes array is populated
- Check canvas rendering

### Chord detection not using confirmed values
- Check ECS environment variables
- Verify Lambda passes values correctly

## Documentation

- `DOWNBEAT_UI_INTEGRATION_GUIDE.md` - Detailed integration guide
- `DOWNBEAT_CONFIRMATION_DEPLOYMENT_GUIDE.md` - Deployment instructions
- `DOWNBEAT_INTEGRATION_EXAMPLE.tsx` - Code examples
- `DOWNBEAT_CONFIRMATION_IMPLEMENTATION_COMPLETE.md` - Implementation summary

## Status

✅ Implementation Complete
⏳ Ready for Deployment

## Next Steps

1. Deploy Lambda functions to AWS
2. Add API Gateway routes
3. Update ECS task definition
4. Integrate React component into upload workflow
5. Test end-to-end
6. Deploy to production

---

**Last Updated**: February 18, 2026
