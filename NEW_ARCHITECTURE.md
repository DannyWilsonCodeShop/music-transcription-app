# ChordScout New Architecture - High Accuracy Flow

## Overview
Complete redesign focusing on maximum accuracy for YouTube → Chord/Lyrics PDF conversion.

## Technology Stack

### 1. Audio Extraction
- **Service**: Apify YouTube Transcript API (agentx~youtube-transcript)
- **Why**: Reliable, no extra API keys needed, works with just Apify token
- **Output**: YouTube transcript + metadata

### 2. Audio Download
- **Service**: YouTube audio download (separate step)
- **Storage**: S3 bucket for temporary audio files
- **Format**: MP3/WAV for processing

### 3. Lyrics Transcription
- **Service**: Deepgram Nova-3 API
- **Accuracy**: Highest WER in 2026 benchmarks
- **Output**: Timestamped lyrics with high accuracy
- **Cost**: ~$0.0043/minute of audio

### 4. Chord Detection
- **Service**: Madmom CNN+CRF (self-hosted Lambda)
- **Accuracy**: 89.6% on benchmark datasets
- **Deployment**: Docker container on Lambda
- **Output**: Timestamped chord progressions

### 5. PDF Generation
- **Service**: jsPDF (Lambda function)
- **Output**: Formatted PDF with chords above lyrics
- **Storage**: S3 for final PDFs

### 6. Database
- **Service**: DynamoDB
- **Tables**: 
  - Jobs (tracking status)
  - Transcriptions (final results)
  - Users (if auth needed)

## Architecture Flow

```
User Input (YouTube URL)
    ↓
[Lambda 1: Job Creator]
    ↓
DynamoDB (Create Job Record)
    ↓
[Step Functions Workflow]
    ↓
┌─────────────────────────────────────┐
│ Step 1: YouTube Audio Download      │
│ - Download audio from YouTube       │
│ - Store in S3 (temp bucket)         │
│ - Update job status                 │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Step 2: Lyrics Transcription        │
│ - Send audio to Deepgram Nova-3     │
│ - Get timestamped lyrics            │
│ - Store in DynamoDB                 │
│ - Update job status                 │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Step 3: Chord Detection             │
│ - Process audio with Madmom         │
│ - Get timestamped chords            │
│ - Store in DynamoDB                 │
│ - Update job status                 │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Step 4: PDF Generation              │
│ - Combine lyrics + chords           │
│ - Generate formatted PDF            │
│ - Store in S3 (final bucket)        │
│ - Update job status: COMPLETE       │
└─────────────────────────────────────┘
    ↓
User receives PDF download link
```

## Lambda Functions Required

### 1. `create-job` (Node.js)
- Input: YouTube URL
- Creates DynamoDB job record
- Triggers Step Functions workflow
- Returns job ID to frontend

### 2. `youtube-downloader` (Python)
- Downloads audio from YouTube using yt-dlp
- Uploads to S3 temp bucket
- Returns S3 key

### 3. `lyrics-transcriber` (Node.js)
- Fetches audio from S3
- Sends to Deepgram Nova-3 API
- Stores timestamped lyrics in DynamoDB
- Returns lyrics data

### 4. `chord-detector` (Python + Docker)
- Fetches audio from S3
- Runs Madmom CNN+CRF model
- Stores timestamped chords in DynamoDB
- Returns chord data

### 5. `pdf-generator` (Node.js)
- Fetches lyrics and chords from DynamoDB
- Uses jsPDF to create formatted PDF
- Uploads to S3 final bucket
- Returns PDF URL

### 6. `update-job-status` (Node.js)
- Updates DynamoDB job status
- Handles errors and retries
- Sends notifications if needed

### 7. `get-job-status` (Node.js)
- API endpoint for frontend polling
- Returns current job status and progress
- Returns PDF URL when complete

## DynamoDB Schema

### Jobs Table
```
{
  jobId: string (PK),
  userId: string (optional),
  youtubeUrl: string,
  videoTitle: string,
  status: string, // PENDING, DOWNLOADING, TRANSCRIBING, DETECTING_CHORDS, GENERATING_PDF, COMPLETE, FAILED
  progress: number, // 0-100
  audioS3Key: string,
  pdfS3Key: string,
  lyricsData: object,
  chordsData: object,
  error: string,
  createdAt: timestamp,
  updatedAt: timestamp,
  completedAt: timestamp
}
```

### Transcriptions Table (for history)
```
{
  transcriptionId: string (PK),
  userId: string (GSI),
  jobId: string,
  youtubeUrl: string,
  videoTitle: string,
  pdfUrl: string,
  duration: number,
  createdAt: timestamp
}
```

## S3 Buckets

### 1. `chordscout-audio-temp`
- Temporary audio files
- Lifecycle: Delete after 1 day
- Access: Private (Lambda only)

### 2. `chordscout-pdfs`
- Final PDF files
- Lifecycle: Keep indefinitely (or 30 days)
- Access: Public read with signed URLs

## Environment Variables Needed

```env
# Apify
APIFY_API_TOKEN=your_token

# Deepgram
DEEPGRAM_API_KEY=your_key

# AWS
AWS_REGION=us-east-1
S3_AUDIO_BUCKET=chordscout-audio-temp
S3_PDF_BUCKET=chordscout-pdfs
DYNAMODB_JOBS_TABLE=chordscout-jobs
DYNAMODB_TRANSCRIPTIONS_TABLE=chordscout-transcriptions

# Step Functions
STEP_FUNCTION_ARN=arn:aws:states:...
```

## Cost Estimates (per transcription)

- YouTube download: Free (yt-dlp)
- Deepgram Nova-3: ~$0.0043/min × 4 min song = $0.017
- Lambda compute: ~$0.001
- S3 storage: ~$0.0001
- DynamoDB: ~$0.0001
- **Total per song: ~$0.02**

## Implementation Steps

1. ✅ Set up environment variables
2. Create DynamoDB tables
3. Create S3 buckets with proper policies
4. Build Lambda functions:
   - create-job
   - youtube-downloader
   - lyrics-transcriber (Deepgram)
   - chord-detector (Madmom Docker)
   - pdf-generator
   - update-job-status
   - get-job-status
5. Create Step Functions workflow
6. Update frontend to use new API
7. Test end-to-end flow
8. Deploy to production

## Next Steps
1. Get Deepgram API key
2. Build Madmom Docker container
3. Create Lambda functions
4. Set up infrastructure
