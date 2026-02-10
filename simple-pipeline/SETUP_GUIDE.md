# Music Transcription App - Simple Pipeline Setup

## What's Happening?

You have multiple AWS accounts configured in `~/.aws/credentials`:
- **Account 463470937777** (default profile) - OLD account, don't use
- **Account 090130568474** (production/chordscout profiles) - CORRECT account

The scripts now automatically use the `production` profile to ensure you're in the correct account (090130568474).

## Quick Start

### 1. Deploy the Pipeline

```bash
cd simple-pipeline
./deploy.sh
```

This will:
- Verify you're in account 090130568474
- Create S3 bucket: `music-transcription-audio-test-090130568474`
- Create DynamoDB table: `MusicTranscription-Jobs-test`
- Create Lambda function: `music-transcription-youtube-downloader-test`
- Create API Gateway endpoint

### 2. Add Your RapidAPI Key

After deployment completes, you'll see instructions to add your RapidAPI key:

```bash
aws lambda update-function-configuration \
  --function-name music-transcription-youtube-downloader-test \
  --environment Variables={AUDIO_BUCKET=music-transcription-audio-test-090130568474,JOBS_TABLE=MusicTranscription-Jobs-test,RAPIDAPI_KEY=YOUR_KEY} \
  --region us-east-1 \
  --profile production
```

Replace `YOUR_KEY` with your actual RapidAPI key.

### 3. Test the Pipeline

```bash
./test.sh "https://www.youtube.com/watch?v=Q-RKhgsZu64"
```

This will:
- Submit a job to download the YouTube video
- Wait for completion
- Download the MP3 file to `downloaded-audio/`
- Show file size and quality info

### 4. Verify Audio Quality

The test script will download the MP3 file. Listen to it:

```bash
open downloaded-audio/YOUR_JOB_ID.mp3
```

Check for:
- Audio clarity
- Bitrate quality
- All instruments audible
- No compression artifacts

## What Changed?

All "ChordScout" branding has been removed:
- ✅ S3 bucket: `music-transcription-audio-*`
- ✅ DynamoDB table: `MusicTranscription-Jobs-*`
- ✅ Lambda function: `music-transcription-youtube-downloader-*`
- ✅ API Gateway: `music-transcription-api-*`
- ✅ IAM role: `MusicTranscription-Lambda-*`
- ✅ Stack name: `music-transcription-pipeline`

## Troubleshooting

### Wrong AWS Account

If you see "WARNING: Not in account 8474!", the script will ask if you want to continue. This shouldn't happen anymore since we're using the `production` profile.

To manually verify your account:

```bash
export AWS_PROFILE=production
aws sts get-caller-identity
```

Should show: `"Account": "090130568474"`

### RapidAPI Key Not Set

If the Lambda fails with "RAPIDAPI_KEY not configured", you need to add your key (see step 2 above).

### Audio File Not Found

Audio files are automatically deleted after 7 days. If you're testing an old job, the file may have been deleted.

## Next Steps

Once you verify the MP3 audio quality is good:
1. Add chord detection (one component at a time)
2. Add lyrics transcription
3. Add PDF generation

But first, let's make sure the audio quality is perfect!
