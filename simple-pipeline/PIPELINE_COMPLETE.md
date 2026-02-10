# Music Transcription Pipeline - Complete

## Overview

Simple, reliable file upload pipeline for music transcription in AWS account 090130568474.

## Architecture

```
User Upload → API Gateway → Lambda (presigned URL) → S3 Upload
                                                        ↓
                                                   S3 Trigger
                                                        ↓
                                              Lambda (process)
                                                        ↓
                                                   DynamoDB
                                                        ↑
User Status Check ← API Gateway ← Lambda (get status) ←
```

## Deployed Components

### 1. Upload Endpoint
- **Endpoint**: `POST https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/upload`
- **Lambda**: `music-transcription-upload-test`
- **Function**: Generates presigned S3 URL, creates job record

### 2. Processing Pipeline
- **Lambda**: `music-transcription-process-audio-test`
- **Trigger**: S3 ObjectCreated events on `uploads/` prefix
- **Function**: Updates job status, processes audio (currently simulated)

### 3. Status Endpoint
- **Endpoint**: `GET https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/jobs/{jobId}`
- **Lambda**: `music-transcription-get-job-status-test`
- **Function**: Returns job status and results

### 4. Storage
- **S3 Bucket**: `music-transcription-audio-test-090130568474`
- **DynamoDB Table**: `MusicTranscription-Jobs-test`

## Usage

### Upload a File

```bash
./test-upload.sh path/to/audio.mp3
```

### Check Job Status

```bash
curl https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/jobs/{jobId} | python3 -m json.tool
```

### Manual API Calls

**Request Upload URL:**
```bash
curl -X POST https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/upload \
  -H "Content-Type: application/json" \
  -d '{"filename": "song.mp3", "contentType": "audio/mpeg", "userId": "user123"}'
```

**Upload File:**
```bash
curl -X PUT "{uploadUrl}" \
  -H "Content-Type: audio/mpeg" \
  --data-binary "@song.mp3"
```

**Check Status:**
```bash
curl https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/jobs/{jobId}
```

## Job Status Flow

1. **UPLOADING** - Job created, waiting for file upload
2. **PROCESSING** - File uploaded, processing started
3. **COMPLETED** - Processing finished successfully
4. **FAILED** - Processing encountered an error

## Test Results

✅ **Test 1**: 6.2 MB MP3 file
- Job ID: `ec7e42b9-d8be-4986-bf50-eb4da9049362`
- Status: Upload successful, file in S3

✅ **Test 2**: 121 KB MP3 file (Piano - C1 min.mp3)
- Job ID: `b65c31ef-407a-45c3-bfc3-0d09b44c5354`
- Status: Complete pipeline working
- Processing time: ~3 seconds
- S3 trigger: Working correctly
- Status endpoint: Returning correct data

## Next Steps

### Immediate
- [ ] Replace simulated processing with actual chord detection
- [ ] Add error handling and retry logic
- [ ] Add file validation (format, size limits)

### Future Enhancements
- [ ] Integrate ECS-based chord detection (from previous work)
- [ ] Add lyrics extraction
- [ ] Add PDF generation
- [ ] Add progress updates during processing
- [ ] Add webhook notifications
- [ ] Add file cleanup after processing

## Deployment Scripts

- `deploy-upload-simple.sh` - Deploy upload endpoint
- `deploy-processing.sh` - Deploy processing pipeline
- `test-upload.sh` - Test complete pipeline

## Configuration

All configuration stored in `config-upload.json`:
```json
{
  "apiEndpoint": "https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com",
  "audioBucket": "music-transcription-audio-test-090130568474",
  "jobsTable": "MusicTranscription-Jobs-test",
  "region": "us-east-1"
}
```

## Why File Upload?

Switched from YouTube download approach because:
- ✅ 100% reliable (no bot detection, no API failures)
- ✅ Legal and compliant (no ToS violations)
- ✅ Predictable performance
- ✅ User controls audio quality
- ✅ Supports any audio source (not just YouTube)

## AWS Account

**Account ID**: 090130568474  
**Profile**: `production` or `chordscout`  
**Region**: us-east-1
