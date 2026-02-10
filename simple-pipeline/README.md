# Simple Pipeline - YouTube to MP3

**Purpose:** Clean, simple pipeline to test YouTube audio download quality

**Account:** 090130568474 (8474)

## Architecture

```
YouTube URL
  ↓
API Gateway (POST /download)
  ↓
Lambda Function
  ├─ Download via RapidAPI
  ├─ Upload to S3
  └─ Save metadata to DynamoDB
  ↓
MP3 file in S3
```

**That's it!** No Step Functions, no ECS, no complexity.

## Components

### S3 Bucket
- Name: `chordscout-simple-audio-test-{account-id}`
- Purpose: Store MP3 files
- Lifecycle: Delete after 7 days

### DynamoDB Table
- Name: `ChordScout-Simple-Jobs-test`
- Key: `jobId` (String)
- Stores: status, progress, s3Key, fileSize, error

### Lambda Function
- Name: `chordscout-simple-youtube-downloader-test`
- Runtime: Python 3.9
- Timeout: 300 seconds (5 minutes)
- Memory: 512 MB

### API Gateway
- Type: HTTP API
- Endpoint: POST /download
- CORS: Enabled

## Deployment

### Prerequisites

1. **AWS CLI configured for account 8474:**
   ```bash
   aws sts get-caller-identity
   # Should show Account: 090130568474
   ```

2. **RapidAPI Key:**
   - Get from: https://rapidapi.com/
   - Subscribe to: "YouTube MP3 Audio Video Downloader"

### Deploy

```bash
cd simple-pipeline
./deploy.sh
```

This will:
1. Create S3 bucket
2. Create DynamoDB table
3. Create Lambda function
4. Create API Gateway
5. Save configuration to `config.json`

### Add RapidAPI Key

After deployment, add your API key:

```bash
aws lambda update-function-configuration \
  --function-name chordscout-simple-youtube-downloader-test \
  --environment Variables={AUDIO_BUCKET=chordscout-simple-audio-test-090130568474,JOBS_TABLE=ChordScout-Simple-Jobs-test,RAPIDAPI_KEY=YOUR_KEY_HERE} \
  --region us-east-1
```

## Testing

### Run Test

```bash
./test.sh "https://www.youtube.com/watch?v=Q-RKhgsZu64"
```

This will:
1. Submit job to API
2. Wait for completion
3. Download MP3 file
4. Save to `downloaded-audio/`

### Manual Test

```bash
# Submit job
curl -X POST "https://YOUR_API_ENDPOINT/download" \
  -H "Content-Type: application/json" \
  -d '{"youtubeUrl": "https://www.youtube.com/watch?v=Q-RKhgsZu64", "jobId": "test-123"}'

# Check status
aws dynamodb get-item \
  --table-name ChordScout-Simple-Jobs-test \
  --key '{"jobId": {"S": "test-123"}}' \
  --region us-east-1

# Download file
aws s3 cp s3://chordscout-simple-audio-test-090130568474/audio/test-123.mp3 ./test.mp3
```

## Verify Audio Quality

After downloading, check:

1. **File size:**
   - Expected: ~1-2 MB per minute
   - 192 kbps MP3: ~1.4 MB/min
   - 128 kbps MP3: ~0.9 MB/min

2. **Listen to the file:**
   ```bash
   open downloaded-audio/YOUR_JOB_ID.mp3
   ```

3. **Check for:**
   - ✅ Clear audio (no distortion)
   - ✅ All instruments audible
   - ✅ Good bitrate
   - ✅ No compression artifacts

4. **Use ffprobe (if installed):**
   ```bash
   ffprobe downloaded-audio/YOUR_JOB_ID.mp3 2>&1 | grep Audio
   ```

## Troubleshooting

### Job fails immediately

**Check Lambda logs:**
```bash
aws logs tail /aws/lambda/chordscout-simple-youtube-downloader-test \
  --follow \
  --region us-east-1
```

**Common issues:**
- RapidAPI key not set
- RapidAPI quota exceeded
- Invalid YouTube URL

### Job times out

**Increase Lambda timeout:**
```bash
aws lambda update-function-configuration \
  --function-name chordscout-simple-youtube-downloader-test \
  --timeout 600 \
  --region us-east-1
```

### Audio quality is poor

**Possible causes:**
1. YouTube source is low quality
2. RapidAPI service compresses audio
3. Need to try different RapidAPI service

**Solutions:**
- Test with different YouTube videos
- Try different RapidAPI endpoints
- Consider using yt-dlp instead

## Next Steps

Once this works and audio quality is verified:

1. ✅ **Verify MP3 quality** - Listen to downloaded files
2. ⏳ **Add chord detection** - New Lambda function
3. ⏳ **Add lyrics transcription** - Another Lambda function
4. ⏳ **Add PDF generation** - Final Lambda function
5. ⏳ **Connect to frontend** - Update API endpoint

**One component at a time!**

## Clean Up

To delete everything:

```bash
aws cloudformation delete-stack \
  --stack-name chordscout-simple-pipeline \
  --region us-east-1

# Wait for deletion
aws cloudformation wait stack-delete-complete \
  --stack-name chordscout-simple-pipeline \
  --region us-east-1
```

## Cost

**Estimated cost per job:**
- Lambda: $0.0001 (5 seconds @ 512 MB)
- S3: $0.0001 (storage + transfer)
- DynamoDB: $0.0001 (1 write)
- RapidAPI: $0.00 (free tier) or $0.01 (paid)

**Total: ~$0.01 per job**

Much cheaper than ECS!

## Summary

**What this does:**
- ✅ Downloads YouTube audio via RapidAPI
- ✅ Saves MP3 to S3
- ✅ Records metadata in DynamoDB
- ✅ Simple, testable, debuggable

**What this doesn't do:**
- ❌ Chord detection (add later)
- ❌ Lyrics transcription (add later)
- ❌ PDF generation (add later)
- ❌ Complex workflows (keep it simple!)

**The goal:**
Verify audio quality FIRST, then add features one at a time.
