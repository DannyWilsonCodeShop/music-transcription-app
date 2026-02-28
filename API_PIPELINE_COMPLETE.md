# Complete API Pipeline Documentation

## API Gateway Configuration

### Primary API Gateway
- **Name**: `music-transcription-api-test`
- **ID**: `hfv1glzbxi`
- **Base URL**: `https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com`

### API Endpoints

#### 1. POST /upload
**Purpose**: Create presigned S3 URL for file upload and initialize job

**Lambda**: `music-transcription-upload-test`
- **Handler**: `upload-lambda.lambda_handler`
- **Runtime**: Python 3.9
- **Environment**:
  - `JOBS_TABLE`: ChordScout-Jobs-V2-dev ✅
  - `AUDIO_BUCKET`: music-transcription-audio-test-090130568474 ✅

**Request Body**:
```json
{
  "filename": "song.m4a",
  "contentType": "audio/x-m4a",
  "userId": "guest"
}
```

**Response**:
```json
{
  "jobId": "uuid",
  "uploadUrl": "https://s3-presigned-url",
  "s3Key": "uploads/{jobId}/{filename}"
}
```

**What it does**:
1. Generates unique jobId
2. Creates presigned S3 URL for upload
3. Creates job record in DynamoDB with status "UPLOADING"
4. Returns upload URL to frontend

---

#### 2. GET /jobs/{jobId}
**Purpose**: Get current status of a transcription job

**Lambda**: `music-transcription-get-job-status-test`
- **Handler**: `get-job-status.lambda_handler`
- **Runtime**: Python 3.9
- **Environment**:
  - `JOBS_TABLE`: ChordScout-Jobs-V2-dev ✅

**Response**:
```json
{
  "jobId": "uuid",
  "status": "PROCESSING|COMPLETED|FAILED",
  "progress": 75,
  "chordsData": {
    "key": "C Major",
    "tempo": 120,
    "chords": [...],
    "leadSheet": {
      "metadata": {...},
      "sections": [...]
    }
  },
  "pdfUrl": "https://s3-pdf-url",
  "errorMessage": "error if failed"
}
```

**Status Values**:
- `UPLOADING` (0%) - File being uploaded
- `PROCESSING` (5-10%) - ECS task starting
- `DETECTING_CHORDS` (70%) - Chord detection in progress
- `CHORDS_DETECTED` (80%) - Chords detected, lyrics extraction starting
- `COMPLETED` (100%) - All processing complete
- `FAILED` - Error occurred

---

## Backend Processing Flow

### 3. S3 Event Trigger
**Trigger**: S3 ObjectCreated event on `music-transcription-audio-test-090130568474`
**Filter**: Prefix = `uploads/`

**Lambda**: `music-transcription-process-audio-test`
- **Handler**: `process-audio.lambda_handler`
- **Runtime**: Python 3.9
- **Environment**:
  - `ECS_CLUSTER`: ChordScout-dev ✅
  - `JOBS_TABLE`: ChordScout-Jobs-V2-dev ✅
  - `ECS_TASK_DEFINITION`: chordscout-chord-detector-dev ✅
  - `ECS_SUBNETS`: subnet-025cbdacce40039e8,... ✅
  - `ECS_SECURITY_GROUPS`: sg-0d36529326aacd89d ✅

**What it does**:
1. Triggered when file uploaded to S3
2. Extracts jobId from S3 key
3. Updates job status to "PROCESSING"
4. Launches ECS Fargate task with environment:
   - `JOB_ID`: jobId
   - `AUDIO_BUCKET`: bucket name
   - `AUDIO_KEY`: S3 key
5. Updates job with ECS task ARN

**Container Override**:
- Container name: `chord-detector` ✅ (FIXED)
- Image: `090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest`

---

### 4. ECS Task Processing
**Cluster**: `ChordScout-dev`
**Task Definition**: `chordscout-chord-detector-dev:13`
**Container**: `chord-detector`

**Processing Steps**:
1. Download audio from S3
2. Detect tempo and beats (librosa)
3. Detect chords with enhanced templates (84 chord types)
4. **Extract lyrics with Whisper** (NEW - base model)
5. **Align lyrics with chords** (NEW)
   - Section detection (Verse, Chorus, Bridge)
   - Phrase grouping (2-4 measures per line)
   - Chord-to-word alignment
   - Lead sheet structure generation
6. Update job with chord data + lead sheet
7. Trigger PDF generation Lambda

**Environment Variables**:
- `DYNAMODB_JOBS_TABLE`: ChordScout-Jobs-V2-dev ✅
- `PDF_GENERATOR_FUNCTION`: chordscout-v2-pdf-generator-dev ✅
- `S3_AUDIO_BUCKET`: chordscout-audio-temp-dev-090130568474 ✅
- `ENABLE_STEM_SEPARATION`: false ✅
- `CHUNK_DURATION`: 30 ✅

---

### 5. PDF Generation
**Lambda**: `chordscout-v2-pdf-generator-dev`
- **Handler**: `index.handler`
- **Runtime**: Node.js 18.x
- **Environment**:
  - `DYNAMODB_JOBS_TABLE`: ChordScout-Jobs-V2-dev ✅
  - `S3_PDF_BUCKET`: chordscout-pdfs-dev-090130568474 ✅

**What it does**:
1. Triggered by ECS task after chord detection
2. Retrieves job data from DynamoDB
3. Generates PDF with aligned lead sheet
4. Uploads PDF to S3
5. Updates job status to "COMPLETED" with PDF URL

---

## Frontend Integration

### App.tsx API Calls

**1. Upload Flow**:
```typescript
// Request upload URL
POST https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/upload
Body: { filename, contentType, userId }

// Upload file to S3
PUT {presignedUrl}
Body: file binary

// Poll for status
GET https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/jobs/{jobId}
Interval: 2 seconds
```

**2. Status Polling**:
- Starts immediately after upload
- Polls every 2 seconds
- Stops when status is "COMPLETED" or "FAILED"
- Updates progress bar based on `progress` field

**3. Result Display**:
- If `leadSheet` exists: Display LeadSheetDisplay component
- Otherwise: Display separate lyrics and chord sections

---

## IAM Permissions

### Lambda Role: `MusicTranscription-Lambda-test`

**DynamoDB Access**:
```json
{
  "Action": [
    "dynamodb:PutItem",
    "dynamodb:GetItem",
    "dynamodb:UpdateItem",
    "dynamodb:Query",
    "dynamodb:Scan"
  ],
  "Resource": [
    "arn:aws:dynamodb:us-east-1:090130568474:table/MusicTranscription-Jobs-test",
    "arn:aws:dynamodb:us-east-1:090130568474:table/ChordScout-Jobs-V2-dev"
  ]
}
```

**ECS Access**:
```json
{
  "Action": ["ecs:RunTask"],
  "Resource": "*"
}
```

**S3 Access**:
```json
{
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Resource": "arn:aws:s3:::music-transcription-audio-test-090130568474/*"
}
```

---

## Complete Request Flow

```
1. User uploads file
   ↓
2. Frontend → POST /upload
   ← Returns: jobId, uploadUrl
   ↓
3. Frontend → PUT S3 presigned URL
   ← File uploaded
   ↓
4. S3 Event → Process Lambda
   ↓
5. Process Lambda → Launch ECS Task
   ↓
6. ECS Task:
   - Download audio
   - Detect chords (30-60s)
   - Extract lyrics with Whisper (60-120s) ← NEW
   - Align lyrics with chords (<5s) ← NEW
   - Update DynamoDB
   - Trigger PDF Lambda
   ↓
7. PDF Lambda:
   - Generate PDF with lead sheet
   - Upload to S3
   - Update job status to COMPLETED
   ↓
8. Frontend polls GET /jobs/{jobId}
   ← Returns: status, progress, chordsData, leadSheet, pdfUrl
   ↓
9. Frontend displays LeadSheetDisplay component
```

---

## Timing Estimates

- **Upload**: < 5 seconds
- **ECS Task Startup**: 30-60 seconds
- **Chord Detection**: 30-60 seconds (depends on song length)
- **Lyrics Extraction**: 60-120 seconds (Whisper processing)
- **Alignment**: < 5 seconds
- **PDF Generation**: 5-10 seconds
- **Total**: 2-4 minutes for typical 3-minute song

---

## Error Handling

### Common Errors:

1. **404 on /jobs/{jobId}**
   - Cause: Job not found in DynamoDB
   - Fix: Verify upload Lambda is using correct table

2. **ECS Task Failed to Start**
   - Cause: Invalid container name in override
   - Fix: Use `chord-detector` not `chord-detection`

3. **Access Denied on DynamoDB**
   - Cause: Lambda role missing permissions
   - Fix: Add table ARN to IAM policy

4. **Timeout on Lyrics Extraction**
   - Cause: Whisper processing taking too long
   - Solution: Consider using smaller model (tiny) or skip for long songs

---

## Monitoring

### CloudWatch Log Groups:
- `/aws/lambda/music-transcription-upload-test`
- `/aws/lambda/music-transcription-get-job-status-test`
- `/aws/lambda/music-transcription-process-audio-test`
- `/ecs/chordscout-chord-detector-dev`
- `/aws/lambda/chordscout-v2-pdf-generator-dev`

### Key Metrics to Monitor:
- Lambda invocation count
- Lambda error rate
- ECS task success rate
- Average processing time
- DynamoDB read/write capacity

---

## Testing

### Test Upload:
```bash
curl -X POST https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/upload \
  -H "Content-Type: application/json" \
  -d '{"filename":"test.m4a","contentType":"audio/x-m4a","userId":"test"}'
```

### Test Job Status:
```bash
curl https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/jobs/{jobId}
```

### Verify DynamoDB:
```bash
aws dynamodb get-item \
  --table-name ChordScout-Jobs-V2-dev \
  --key '{"jobId": {"S": "your-job-id"}}' \
  --profile chordscout
```

---

## All Systems Configured ✅

- ✅ Upload Lambda → ChordScout-Jobs-V2-dev
- ✅ Get Job Status Lambda → ChordScout-Jobs-V2-dev
- ✅ Process Lambda → ChordScout-dev cluster
- ✅ Process Lambda → chord-detector container name
- ✅ ECS Task → Latest Docker image with Whisper
- ✅ IAM Permissions → Access to new table
- ✅ S3 Event Trigger → Configured
- ✅ API Gateway → All routes working

**Pipeline is ready for testing!**
