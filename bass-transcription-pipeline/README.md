# Bass Transcription Pipeline

Dedicated pipeline for bass note transcription with Nashville Number System (NNS) output.

## Overview

This is a **separate, independent pipeline** from the chord detection system. It's specifically designed for:

- Monophonic bass line transcription
- Nashville Number System (NNS) conversion
- Measure-by-measure output
- Key detection with relative major support

## Why a Separate Pipeline?

1. **Clean separation of concerns** - Bass transcription is fundamentally different from chord detection
2. **Independent scaling** - Can scale bass transcription separately from chord detection
3. **Easier maintenance** - No risk of breaking existing chord detection
4. **Different output format** - Bass notes vs. chords require different data structures
5. **Reuses existing tools** - Leverages Demucs, downbeat detection, etc. from the main pipeline

## Architecture

```
User uploads file with analysisOptions: { musicPart: 'bass' }
         ↓
Upload Lambda (existing - modified to route to bass pipeline)
         ↓
S3 Upload Complete Event
         ↓
Bass Process Lambda (NEW)
         ↓
Bass Transcription ECS Task (NEW)
    - Extract bass stem (Demucs)
    - Detect tempo/beats (librosa)
    - Detect downbeat (reused from main pipeline)
    - Transcribe notes (Basic Pitch)
    - Detect key (note frequency analysis)
    - Convert to NNS
    - Group by measures
         ↓
Bass PDF Generator (NEW)
    - Generate NNS chart PDF
         ↓
Complete!
```

## Components

### 1. Bass Transcription ECS Task
**Directory**: `bass-transcription-ecs/`

**Files**:
- `app.py` - Main orchestration logic
- `bass_note_transcription.py` - Note transcription and NNS conversion
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies
- `build-and-push.sh` - Build and deploy script

**Key Features**:
- Uses Basic Pitch for accurate note transcription
- Monophonic filtering (bass should be one note at a time)
- 16th note quantization
- Key detection from note progression
- Relative major calculation for minor keys
- NNS conversion based on relative major

### 2. Bass Process Lambda (TODO)
**File**: `bass-process-lambda.py`

Triggers the bass transcription ECS task when a file is uploaded with `musicPart='bass'`.

### 3. Bass PDF Generator (TODO)
**Directory**: `bass-pdf-generator/`

Generates PDF with NNS notation instead of chord names.

## Data Format

### Bass Data Structure
```json
{
  "analysisType": "bass_notes",
  "notes": [
    {
      "pitch": 58,
      "note_name": "Bb2",
      "nns": "1",
      "start": 0.0,
      "end": 0.5,
      "measure": 1,
      "beat": 1,
      "subdivision": 1
    }
  ],
  "measures": [
    {
      "measure": 1,
      "start": 0.0,
      "end": 1.79,
      "nns": ["1", "1", "1", "1"],
      "noteNames": ["Bb", "Bb", "Bb", "Bb"],
      "pitches": [58, 58, 58, 58]
    }
  ],
  "key": "Bb",
  "mode": "minor",
  "relativeMajor": "Db",
  "confidence": 0.85,
  "tempo": 134.0,
  "timeSignature": "4/4",
  "totalNotes": 120,
  "totalMeasures": 30
}
```

## Example Output

**Song**: "That's What I Like" by Bruno Mars

```
Key: Bb minor (Db major)
Tempo: 134 BPM
Time Signature: 4/4

Measure 1:  1  1  1  1  |  (Bb Bb Bb Bb)
Measure 2:  4  4  4  4  |  (Eb Eb Eb Eb)
Measure 3:  6  6  6  6  |  (Gb Gb Gb Gb)
Measure 4:  5  5  5  5  |  (F F F F)
```

## Deployment

### 1. Build and Push ECS Image

```bash
cd bass-transcription-ecs
./build-and-push.sh
```

This will:
- Create ECR repository if needed
- Build Docker image for linux/amd64
- Push to ECR

### 2. Create ECS Task Definition (TODO)

```bash
# Create task definition
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json \
  --region us-east-1
```

### 3. Deploy Process Lambda (TODO)

```bash
# Package and deploy
zip bass-process-lambda.zip bass-process-lambda.py
aws lambda update-function-code \
  --function-name bass-process-lambda-dev \
  --zip-file fileb://bass-process-lambda.zip \
  --region us-east-1
```

### 4. Deploy PDF Generator (TODO)

```bash
cd bass-pdf-generator
npm install
zip -r function.zip .
aws lambda update-function-code \
  --function-name bass-nns-pdf-generator-dev \
  --zip-file fileb://function.zip \
  --region us-east-1
```

## Testing

### Local Testing

```bash
# Test bass transcription module
cd bass-transcription-ecs
python -c "
from bass_note_transcription import detect_bass_notes
import librosa

# Load test audio
audio, sr = librosa.load('../../public/04 That_s What I Like.m4a', sr=22050)

# Transcribe
result = detect_bass_notes(audio, sr, 134.0, '4/4', 0.0)

print(f'Key: {result[\"key\"]} {result[\"mode\"]}')
print(f'Relative major: {result[\"relativeMajor\"]}')
print(f'Total notes: {result[\"totalNotes\"]}')
print(f'Total measures: {result[\"totalMeasures\"]}')
"
```

### End-to-End Testing

```bash
# Upload file with bass analysis option
./test-bass-transcription.sh "public/04 That_s What I Like.m4a"
```

## Reused Components

This pipeline reuses these components from the main system:

1. **Demucs** - Stem separation (bass extraction)
2. **Downbeat Detection** - From `simple-pipeline/chord-detection/downbeat_detection.py`
3. **Upload Lambda** - Modified to route to bass pipeline
4. **DynamoDB Table** - Same jobs table, different data structure
5. **S3 Bucket** - Same audio storage

## Key Differences from Chord Pipeline

| Feature | Chord Pipeline | Bass Pipeline |
|---------|---------------|---------------|
| Input | Full mix or stems | Bass stem only |
| Analysis | Chromagram → Chords | Pitch detection → Notes |
| Output | Chord names (Cmaj7, Dm) | NNS numbers (1, 4, 5) |
| Temporal Resolution | Beat-level | 16th note level |
| Key Detection | Chord progression | Note frequency |
| Use Case | Full arrangements | Bass line study |

## Future Enhancements

1. **Piano/Guitar Pipelines** - Similar dedicated pipelines for other instruments
2. **Multi-stem Comparison** - Compare bass vs. piano progressions
3. **Modulation Detection** - Detect key changes within song
4. **Rhythm Notation** - Add rhythm symbols (quarter, eighth, etc.)
5. **MIDI Export** - Export bass line as MIDI file

## Troubleshooting

### ECS Task Fails

Check logs:
```bash
aws logs tail /ecs/bass-transcription-dev --follow --region us-east-1
```

### No Notes Detected

- Check if bass stem extraction worked
- Verify audio file is not corrupted
- Try adjusting Basic Pitch sensitivity

### Wrong Key Detected

- Key detection uses note frequency analysis
- For "That's What I Like", should detect Bb minor (Db major)
- If wrong, may need to adjust key detection algorithm

## Documentation

- Implementation: `BASS_NOTE_TRANSCRIPTION_IMPLEMENTATION.md`
- Deployment: `DEPLOYMENT_BASS_PIPELINE_2026-02-28.md`
- Testing: `BASS_PIPELINE_TESTING_GUIDE.md`

## Status

- ✅ Bass transcription module created
- ✅ ECS task created
- ✅ Dockerfile created
- ✅ Build script created
- ⏳ Process Lambda (TODO)
- ⏳ PDF Generator (TODO)
- ⏳ ECS task definition (TODO)
- ⏳ CloudFormation template (TODO)
- ⏳ End-to-end testing (TODO)
