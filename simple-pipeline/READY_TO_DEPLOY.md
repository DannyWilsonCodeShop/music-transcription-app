# ✅ Ready to Deploy - Music Transcription App

## What We Fixed

### 1. AWS Account Configuration ✅
- **Problem:** Your AWS CLI was using the default profile (account 463470937777)
- **Solution:** Scripts now use `AWS_PROFILE=production` (account 090130568474)
- **Verified:** `aws sts get-caller-identity` shows correct account

### 2. Branding Cleanup ✅
- **Problem:** All resources had "ChordScout" in their names
- **Solution:** Renamed everything to "Music Transcription" or generic names

**Before → After:**
- `chordscout-simple-audio-*` → `music-transcription-audio-*`
- `ChordScout-Simple-Jobs-*` → `MusicTranscription-Jobs-*`
- `chordscout-simple-youtube-downloader-*` → `music-transcription-youtube-downloader-*`
- `chordscout-simple-api-*` → `music-transcription-api-*`
- `ChordScout-Simple-Lambda-*` → `MusicTranscription-Lambda-*`
- `chordscout-simple-pipeline` → `music-transcription-pipeline`

### 3. Directory Structure ✅
- Working directory: `/Users/dannywilson/DevOps/ChordScout/simple-pipeline`
- Scripts are executable
- All files ready to deploy

## Deploy Now

```bash
cd simple-pipeline
./deploy.sh
```

The deployment will:
1. Verify you're in account 090130568474 ✅
2. Create CloudFormation stack `music-transcription-pipeline`
3. Create S3 bucket for audio files
4. Create DynamoDB table for job tracking
5. Create Lambda function for YouTube downloads
6. Create API Gateway endpoint
7. Save configuration to `config.json`

## After Deployment

### Add RapidAPI Key

The deployment script will show you the exact command. It will look like:

```bash
aws lambda update-function-configuration \
  --function-name music-transcription-youtube-downloader-test \
  --environment Variables={AUDIO_BUCKET=music-transcription-audio-test-090130568474,JOBS_TABLE=MusicTranscription-Jobs-test,RAPIDAPI_KEY=YOUR_KEY} \
  --region us-east-1 \
  --profile production
```

### Test the Pipeline

```bash
./test.sh "https://www.youtube.com/watch?v=Q-RKhgsZu64"
```

This will:
- Download the YouTube video as MP3
- Store it in S3
- Download it locally to `downloaded-audio/`
- Show file size and quality metrics

### Verify Audio Quality

```bash
open downloaded-audio/YOUR_JOB_ID.mp3
```

Listen for:
- ✅ Clear audio (no distortion)
- ✅ Good bitrate (not overly compressed)
- ✅ All instruments audible
- ✅ No artifacts or glitches

## What This Pipeline Does

**Single Purpose:** YouTube URL → MP3 file in S3

That's it. No complexity. No chord detection. No lyrics. Just audio extraction.

Once we verify the audio quality is perfect, we'll add the next component.

## Your AWS Credentials

You have these profiles configured:
- `default` → Account 463470937777 (don't use)
- `DWilson19` → Account 463470937777 (don't use)
- `chordscout` → Account 090130568474 ✅
- `production` → Account 090130568474 ✅

The scripts use `production` profile automatically.

## Ready?

Run this command to deploy:

```bash
cd /Users/dannywilson/DevOps/ChordScout/simple-pipeline && ./deploy.sh
```

Then follow the instructions to add your RapidAPI key and test!
