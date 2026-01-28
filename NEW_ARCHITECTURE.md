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


---

## YouTube Download Strategy - Evolution & Solutions

### Current Challenge (January 2026)
YouTube has implemented aggressive bot detection that blocks yt-dlp downloads, even with cookies. The issue manifests as:
- "Sign in to confirm you're not a bot" errors
- HLS fragment download failures (empty files)
- Inconsistent success rates

### Solution Options Analysis

#### Option 1: Third-Party YouTube API (✅ RECOMMENDED - PHASE 1)
**Services:**
- **Apify YouTube Scraper** (Already have token in .env!)
  - Handles bot detection automatically
  - Returns direct download URLs
  - Cost: ~$0.001-0.01 per download

- **RapidAPI YouTube Services**
  - Multiple providers available
  - Reliable audio extraction
  - Cost: ~$0.001-0.01 per download

**Pros:**
- ✅ No bot detection issues
- ✅ No cookie management needed
- ✅ Reliable and fast
- ✅ Already have Apify token
- ✅ Quick implementation (1-2 hours)

**Cons:**
- ❌ Small cost per download (~$0.001-0.01)
- ❌ Dependency on third-party service
- ❌ Rate limits may apply

**Implementation:**
```python
# Replace yt-dlp with Apify in Lambda
import requests

def download_with_apify(youtube_url, job_id):
    response = requests.post(
        'https://api.apify.com/v2/acts/apify~youtube-scraper/runs',
        json={'startUrls': [{'url': youtube_url}]},
        params={'token': os.environ['APIFY_API_TOKEN']}
    )
    # Get audio URL and download
```

---

#### Option 2: Lambda + FFmpeg Layer
**Approach:** Add FFmpeg to Lambda via Lambda Layer to handle HLS streams properly

**Pros:**
- ✅ Handles all YouTube formats
- ✅ No third-party dependencies
- ✅ Better audio quality control
- ✅ One-time setup

**Cons:**
- ❌ Larger Lambda package (~50MB)
- ❌ Still needs cookie management
- ❌ More complex deployment
- ❌ Cookies expire frequently

**Implementation:**
```python
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'm4a',
    }],
    'ffmpeg_location': '/opt/bin/ffmpeg',  # Lambda layer path
}
```

---

#### Option 3: ECS Fargate for Downloads (✅ RECOMMENDED - PHASE 2)
**Approach:** Move YouTube downloading from Lambda to ECS Fargate (like chord detector)

**Why:**
- Full control over environment
- Can install FFmpeg easily
- Longer execution time (no 15min Lambda limit)
- Better for handling large files
- Consistent with existing chord detector architecture

**Pros:**
- ✅ Most reliable long-term solution
- ✅ No Lambda limitations
- ✅ Full FFmpeg support
- ✅ Consistent architecture
- ✅ Better error handling
- ✅ Can handle any video length

**Cons:**
- ❌ Slightly higher cost (~$0.04 per task)
- ❌ More infrastructure to manage
- ❌ Longer setup time (6 hours)

**Implementation:**
```dockerfile
FROM python:3.11
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install yt-dlp boto3
COPY download.py .
CMD ["python", "download.py"]
```

---

### 🏆 Recommended Implementation Path

#### **Phase 1: Quick Win with Apify (THIS WEEK)**
**Timeline:** 1-2 hours
**Cost:** ~$1-10 per 1000 videos
**Reliability:** ⭐⭐⭐⭐⭐

**Steps:**
1. Update Lambda to use Apify API
2. Remove yt-dlp dependency
3. Test with various videos
4. Deploy to production

**Benefits:**
- Works immediately
- No bot detection
- Minimal code changes
- Proven reliability

---

#### **Phase 2: ECS Migration (NEXT SPRINT)**
**Timeline:** 6 hours
**Cost:** ~$40 per 1000 videos
**Reliability:** ⭐⭐⭐⭐⭐

**Steps:**
1. Create ECS task definition for YouTube downloader
2. Build Docker image with FFmpeg + yt-dlp
3. Update Step Functions to trigger ECS task
4. Keep Apify as fallback
5. Implement cookie rotation system

**Benefits:**
- Full control and flexibility
- No third-party dependencies
- Consistent with chord detector
- Can handle edge cases

---

### Cost Comparison (per 1000 videos)

| Solution | Cost | Reliability | Setup Time | Maintenance |
|----------|------|-------------|------------|-------------|
| **Apify (Phase 1)** | $1-10 | ⭐⭐⭐⭐⭐ | 1 hour | Low |
| **Lambda + FFmpeg** | $0.50 | ⭐⭐⭐⭐ | 4 hours | Medium |
| **ECS (Phase 2)** | $40 | ⭐⭐⭐⭐⭐ | 6 hours | Low |
| **Current (yt-dlp only)** | $0.10 | ⭐⭐ | - | High |

---

### Updated Cost Estimates (with Apify)

**Phase 1 (Apify):**
- YouTube download (Apify): ~$0.005
- Deepgram Nova-3: ~$0.017
- Lambda compute: ~$0.001
- S3 storage: ~$0.0001
- DynamoDB: ~$0.0001
- **Total per song: ~$0.024**

**Phase 2 (ECS):**
- YouTube download (ECS): ~$0.04
- Deepgram Nova-3: ~$0.017
- Lambda compute: ~$0.001
- S3 storage: ~$0.0001
- DynamoDB: ~$0.0001
- **Total per song: ~$0.059**

---

### Action Plan

**Today (Phase 1):**
1. ✅ Update Lambda to use Apify API
2. ✅ Test with multiple YouTube videos
3. ✅ Deploy to production
4. ✅ Monitor reliability

**This Week:**
1. Monitor Apify usage and costs
2. Collect metrics on success rate
3. Plan ECS migration if needed

**Next Sprint (Phase 2):**
1. Create ECS task for YouTube downloads
2. Implement cookie rotation system
3. Keep Apify as backup/fallback
4. A/B test both approaches

---

### Cookie Management Notes

**Current Status:**
- ✅ Cookies uploaded to S3: `s3://chordscout-audio-temp-dev-090130568474/cookies/youtube-cookies.txt`
- ✅ Lambda configured to use cookies
- ✅ Cookies bypass bot detection
- ❌ HLS fragment downloads still fail

**For Phase 2 (ECS):**
- Implement automatic cookie refresh (weekly)
- Use browser automation to export fresh cookies
- Store multiple cookie sets for rotation
- Monitor cookie expiration

**Cookie Refresh Script:**
```bash
# Run weekly via cron or GitHub Actions
./export-youtube-cookies.sh
aws s3 cp cookies.txt s3://bucket/cookies/youtube-cookies.txt
```

---

### Testing Strategy

**Phase 1 Testing:**
- [ ] Test with popular music videos
- [ ] Test with age-restricted content
- [ ] Test with long videos (>10 min)
- [ ] Test with various audio qualities
- [ ] Monitor Apify rate limits

**Phase 2 Testing:**
- [ ] Compare ECS vs Apify reliability
- [ ] Measure cost differences
- [ ] Test cookie rotation
- [ ] Load testing (100+ concurrent downloads)

---

### Monitoring & Alerts

**Key Metrics:**
- Download success rate
- Average download time
- Cost per download
- Error types and frequency
- API rate limit hits

**Alerts:**
- Success rate drops below 95%
- Average cost exceeds $0.10 per song
- Apify rate limit warnings
- Cookie expiration (Phase 2)

---

## Updated Implementation Steps

1. ✅ Set up environment variables
2. ✅ Create DynamoDB tables
3. ✅ Create S3 buckets with proper policies
4. 🔄 Build Lambda functions:
   - ✅ create-job
   - 🔄 youtube-downloader (UPDATE TO APIFY)
   - ✅ lyrics-transcriber (Deepgram)
   - ✅ chord-detector (Madmom Docker on ECS)
   - ✅ pdf-generator
   - ✅ update-job-status
   - ✅ get-job-status
5. ✅ Create Step Functions workflow
6. ✅ Update frontend to use new API
7. 🔄 Test end-to-end flow
8. 🔄 Deploy to production

**Next Immediate Steps:**
1. 🎯 Implement Apify integration in youtube-downloader Lambda
2. 🎯 Test with multiple videos
3. 🎯 Deploy and monitor
