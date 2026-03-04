# Bass Transcription Pipeline Deployed - 2026-02-28

## Summary

Successfully deployed the bass transcription pipeline with Nashville Number System (NNS) support. This is a completely separate pipeline from chord detection, designed specifically for monophonic bass line analysis.

## What Was Deployed

### 1. Bass Transcription ECS Task ✅
- **Image**: `090130568474.dkr.ecr.us-east-1.amazonaws.com/bass-transcription:latest`
- **Task Definition**: `bass-transcription-dev:1`
- **Container**: `bass-transcription`
- **Resources**: 1024 CPU, 4096 MB memory
- **Features**:
  - Bass stem extraction (Demucs)
  - Note transcription (Basic Pitch)
  - 16th note attack detection
  - Key detection from note progression
  - Nashville Number System conversion
  - Beat-level placeholder formatting (`| 1 - - - |`)

### 2. Process Lambda Updated ✅
- **Function**: `music-transcription-process-audio-test`
- **Changes**:
  - Added routing logic based on `musicPart` parameter
  - Routes `bass` requests to `bass-transcription-dev` task
  - Routes other requests to `chordscout-chord-detector-dev` task
  - Added `BASS_TASK_DEFINITION` environment variable

### 3. Frontend Updated ✅
- **Modal**: `src/components/AnalysisOptionsModal.tsx`
- **Changes**:
  - Shows only bass option (piano/guitar removed)
  - Fixed to `musicPart: 'bass'`
  - Displays "Bass Line (Nashville Numbers)" label
- **Deployment**: Pushed to git, Amplify will auto-deploy

## Pipeline Flow

```
User uploads file → Modal shows "Bass Line" option → Upload Lambda
    ↓
S3 Upload Complete Event
    ↓
Process Lambda (checks musicPart='bass')
    ↓
Bass Transcription ECS Task
    - Download audio
    - Extract bass stem (Demucs)
    - Detect tempo/beats (librosa)
    - Detect downbeat
    - Transcribe notes (Basic Pitch)
    - Filter to monophonic
    - Quantize to 16th note grid
    - Detect note attacks (pitch change, gap, volume)
    - Detect key from note progression
    - Convert to NNS (relative major)
    - Group by measures with beat placeholders
    ↓
Update DynamoDB with bassData
    ↓
Trigger PDF Generator (TODO)
    ↓
Complete!
```

## Key Features

### Note Attack Detection
Only shows newly played notes (attacks), not sustained notes:
- **Pitch change**: Different note than previous
- **Gap in time**: Silence >50ms before note
- **Volume increase**: Re-attack of same note (>30% velocity increase)

### Beat Placeholders
Makes output more readable:
- `| 1 - - - |` = whole note on beat 1
- `| 1 - 5 - |` = half notes on beats 1 and 3
- `| 1 4 5 1 |` = quarter notes on each beat

### Key Detection
- Analyzes note frequency distribution
- Uses Krumhansl-Schmuckler key profiles
- Detects minor keys with relative major
- Example: "That's What I Like" → Bb minor (Db major)

## Data Structure

```json
{
  "bassData": {
    "key": "Bb",
    "mode": "minor",
    "relativeMajor": "Db",
    "confidence": 0.85,
    "tempo": 134.0,
    "timeSignature": "4/4",
    "totalNotes": 120,
    "totalMeasures": 30,
    "measures": [
      {
        "measure": 1,
        "start": 0.0,
        "end": 1.79,
        "nns_display": "1 - - -",
        "notes_display": "Bb - - -",
        "beat_grid": [
          {"beat": 1, "nns": "1", "note_name": "Bb", "has_note": true},
          {"beat": 2, "nns": "-", "note_name": "", "has_note": false},
          {"beat": 3, "nns": "-", "note_name": "", "has_note": false},
          {"beat": 4, "nns": "-", "note_name": "", "has_note": false}
        ]
      }
    ]
  }
}
```

## Testing

### Test with "That's What I Like"

```bash
# Upload the test file
curl -X POST https://your-api.com/upload \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "04 That_s What I Like.m4a",
    "contentType": "audio/m4a",
    "analysisOptions": {
      "musicPart": "bass",
      "includeKey": true,
      "includeTempo": true,
      "includeTimeSignature": true
    }
  }'

# Expected output:
# Key: Bb minor (Db major)
# Tempo: ~134 BPM
# Measures with NNS: 1, 4, 6, 5 pattern
```

### Check ECS Logs

```bash
aws logs tail /ecs/bass-transcription-dev --follow --profile production --region us-east-1
```

### Check Lambda Logs

```bash
aws logs tail /aws/lambda/music-transcription-process-audio-test --follow --profile production --region us-east-1
```

## What's Still TODO

### 1. Bass PDF Generator
- Create Lambda function: `bass-nns-pdf-generator-dev`
- Generate PDF with NNS chart instead of chord names
- Format: Measure-by-measure with beat placeholders
- Include key, tempo, time signature

### 2. Frontend Display
- Create component to display bass transcription results
- Show NNS chart with measures
- Display key information (minor + relative major)
- Show tempo and time signature

### 3. End-to-End Testing
- Test full pipeline with multiple songs
- Verify key detection accuracy
- Verify note attack detection
- Verify beat placeholder formatting

## Files Changed

### New Files
- `bass-transcription-pipeline/bass-transcription-ecs/app.py`
- `bass-transcription-pipeline/bass-transcription-ecs/bass_note_transcription.py`
- `bass-transcription-pipeline/bass-transcription-ecs/Dockerfile`
- `bass-transcription-pipeline/bass-transcription-ecs/requirements.txt`
- `bass-transcription-pipeline/bass-transcription-ecs/build-and-push.sh`
- `bass-transcription-pipeline/bass-transcription-ecs/task-definition.json`
- `bass-transcription-pipeline/README.md`
- `bass-transcription-pipeline/NOTE_ATTACK_DETECTION.md`
- `src/components/AnalysisOptionsModal.tsx`

### Modified Files
- `simple-pipeline/process-audio-lambda.py` (added bass routing)

## AWS Resources

### ECR Repository
- **Name**: `bass-transcription`
- **URI**: `090130568474.dkr.ecr.us-east-1.amazonaws.com/bass-transcription`
- **Latest Image**: `sha256:5261d892a745e8f9ce8fae67dc5382c08c89a48485605204ec4083ad6871d70c`

### ECS Task Definition
- **Family**: `bass-transcription-dev`
- **Revision**: 1
- **ARN**: `arn:aws:ecs:us-east-1:090130568474:task-definition/bass-transcription-dev:1`

### Lambda Function
- **Name**: `music-transcription-process-audio-test`
- **Runtime**: Python 3.9
- **Environment Variables**:
  - `JOBS_TABLE`: ChordScout-Jobs-V2-dev
  - `ECS_CLUSTER`: ChordScout-dev
  - `ECS_TASK_DEFINITION`: chordscout-chord-detector-dev
  - `BASS_TASK_DEFINITION`: bass-transcription-dev
  - `ECS_SUBNETS`: (6 subnets)
  - `ECS_SECURITY_GROUPS`: sg-0d36529326aacd89d

## Next Steps

1. **Create Bass PDF Generator**
   - Lambda function to generate NNS chart PDF
   - Format with measures and beat placeholders
   - Include key, tempo, time signature

2. **Update Frontend**
   - Display bass transcription results
   - Show NNS chart
   - Add download PDF button

3. **Test End-to-End**
   - Upload "That's What I Like"
   - Verify Bb minor/Db major detection
   - Verify NNS output: 1, 4, 6, 5 pattern
   - Check beat placeholders

4. **Add Piano/Guitar Pipelines** (Future)
   - Similar dedicated pipelines for other instruments
   - Reuse same architecture pattern

## Troubleshooting

### ECS Task Fails
```bash
# Check logs
aws logs tail /ecs/bass-transcription-dev --follow --profile production --region us-east-1

# Common issues:
# - Missing environment variables (JOB_ID, AUDIO_BUCKET, AUDIO_KEY)
# - S3 permissions
# - DynamoDB permissions
# - Basic Pitch not installed
```

### No Notes Detected
- Check if bass stem extraction worked
- Verify audio file is not corrupted
- Try adjusting Basic Pitch sensitivity in `bass_note_transcription.py`

### Wrong Key Detected
- Key detection uses note frequency analysis
- For "That's What I Like", should detect Bb minor (Db major)
- If wrong, may need to adjust key detection algorithm

## Documentation

- **Pipeline Overview**: `bass-transcription-pipeline/README.md`
- **Attack Detection**: `bass-transcription-pipeline/NOTE_ATTACK_DETECTION.md`
- **This Deployment**: `BASS_TRANSCRIPTION_DEPLOYED_2026-02-28.md`

## Status

✅ ECS image built and pushed
✅ ECS task definition registered
✅ Process Lambda updated with routing
✅ Frontend modal updated (bass only)
✅ Code pushed to git
⏳ Amplify deployment (in progress)
⏳ Bass PDF generator (TODO)
⏳ Frontend display component (TODO)
⏳ End-to-end testing (TODO)
