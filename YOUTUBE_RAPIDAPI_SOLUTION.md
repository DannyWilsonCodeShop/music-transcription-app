# YouTube Download Solution: RapidAPI Integration

## Problem

YouTube's aggressive bot detection was blocking all download attempts from AWS Lambda, including:
- yt-dlp with cookies
- yt-dlp with bypass methods
- Multiple player client attempts
- Apify scraper (doesn't provide audio URLs)

## Solution

Integrated RapidAPI's YouTube MP3 downloader service as a reliable, paid solution.

## Implementation

### 1. New Lambda Function

Created `backend/functions-v2/youtube-downloader/index-rapidapi.py`:
- Uses RapidAPI's YouTube MP3 API
- Handles "processing" status with retry logic
- Downloads MP3 and uploads to S3
- Proper error handling and logging

### 2. Updated Infrastructure

Modified `backend/infrastructure-v2/cloudformation-ecs-architecture.yaml`:
- Added `RapidApiKey` parameter
- Passed API key to YouTube downloader Lambda as environment variable

### 3. Updated Deployment Script

Modified `deploy-backend.sh`:
- Validates `RAPIDAPI_KEY` is set in `.env`
- Passes RapidAPI key to CloudFormation stack

### 4. Environment Configuration

Updated `.env.example`:
- Added `RAPIDAPI_KEY` configuration
- Removed unused `APIFY_API_TOKEN`

## Files Changed

```
backend/functions-v2/youtube-downloader/
├── index.py (replaced with RapidAPI version)
├── index-rapidapi.py (new)
├── requirements.txt (updated to requests + boto3)
└── requirements-rapidapi.txt (new)

backend/infrastructure-v2/
└── cloudformation-ecs-architecture.yaml (added RapidApiKey parameter)

.env.example (added RAPIDAPI_KEY)
deploy-backend.sh (updated validation and parameters)
RAPIDAPI_SETUP.md (new setup guide)
```

## How It Works

1. **User submits YouTube URL** → Frontend sends to API Gateway
2. **Create Job Lambda** → Creates DynamoDB record, starts Step Functions
3. **YouTube Downloader Lambda** → 
   - Extracts video ID from URL
   - Calls RapidAPI with video ID
   - Waits for conversion (retries if "processing")
   - Downloads MP3 from returned URL
   - Uploads to S3
4. **Rest of pipeline** → Lyrics transcription, chord detection, PDF generation

## API Flow

```
Lambda → RapidAPI YouTube MP3 API
         ↓
         Response: { status: "processing" }
         ↓
         Wait 1 second, retry
         ↓
         Response: { status: "ok", link: "https://..." }
         ↓
         Download MP3 from link
         ↓
         Upload to S3
```

## Cost

RapidAPI YouTube MP3 pricing:
- **Free**: 50 requests/month (testing)
- **Pro**: $9.99/month for 1,000 requests
- **Ultra**: $29.99/month for 5,000 requests
- **Mega**: $99.99/month for 25,000 requests

Each transcription = 1 API request

## Setup Steps

1. **Get RapidAPI Key**:
   - Sign up at https://rapidapi.com/
   - Subscribe to https://rapidapi.com/ytjar/api/youtube-mp36
   - Copy your API key

2. **Configure Environment**:
   ```bash
   echo "RAPIDAPI_KEY=your-key-here" >> .env
   ```

3. **Deploy**:
   ```bash
   ./deploy-backend.sh
   ```

## Benefits

✅ **Reliable**: No bot detection issues
✅ **Fast**: Professional service with good performance
✅ **Simple**: Clean API, easy to integrate
✅ **Supported**: Active maintenance and support
✅ **Scalable**: Multiple pricing tiers

## Alternatives Considered

1. **yt-dlp with cookies** ❌ - Still blocked by bot detection
2. **Apify YouTube Scraper** ❌ - Doesn't provide audio download URLs
3. **File upload only** ❌ - User wanted YouTube as primary feature
4. **Self-hosted proxy** ❌ - Complex, expensive, maintenance burden
5. **RapidAPI** ✅ - Reliable, affordable, simple

## Testing

Test with Rick Astley:
```bash
curl -X POST https://ppq03hif98.execute-api.us-east-1.amazonaws.com/dev/jobs \
  -H "Content-Type: application/json" \
  -d '{"youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

## Next Steps

1. User needs to:
   - Sign up for RapidAPI
   - Subscribe to YouTube MP3 API
   - Add API key to `.env`
   - Run `./deploy-backend.sh`

2. Test the complete flow:
   - Submit YouTube URL
   - Verify download works
   - Check lyrics transcription
   - Verify chord detection
   - Download PDF

## Monitoring

Check Lambda logs:
```bash
aws logs tail /aws/lambda/chordscout-v2-youtube-downloader-dev --follow
```

Look for:
- "RapidAPI request attempt X/10"
- "RapidAPI response: {status: ok}"
- "Downloaded X bytes"
- "Upload complete"

## Rollback

If needed, revert to previous version:
```bash
cp backend/functions-v2/youtube-downloader/index-ytdlp-cookies.py \
   backend/functions-v2/youtube-downloader/index.py
./deploy-backend.sh
```

## Documentation

See `RAPIDAPI_SETUP.md` for detailed setup instructions.
