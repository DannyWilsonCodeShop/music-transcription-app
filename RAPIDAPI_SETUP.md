# RapidAPI Setup Guide

## Overview

ChordScout now uses RapidAPI's YouTube MP3 downloader service to reliably download audio from YouTube videos. This is a paid service that bypasses YouTube's bot detection.

## Why RapidAPI?

YouTube has aggressive bot detection that blocks most free download methods from AWS Lambda. Using a paid API service provides:

- ✅ Reliable downloads without bot detection
- ✅ High-quality MP3 audio extraction
- ✅ Fast processing times
- ✅ No need for cookies or complex bypass methods
- ✅ Professional service with support

## Setup Instructions

### Step 1: Create RapidAPI Account

1. Go to [RapidAPI](https://rapidapi.com/)
2. Click "Sign Up" and create a free account
3. Verify your email address

### Step 2: Subscribe to YouTube MP3 API

1. Visit the [YouTube MP3 API](https://rapidapi.com/ytjar/api/youtube-mp36)
2. Click "Subscribe to Test"
3. Choose a pricing plan:
   - **Basic (Free)**: 50 requests/month - Good for testing
   - **Pro ($9.99/month)**: 1,000 requests/month - Good for personal use
   - **Ultra ($29.99/month)**: 5,000 requests/month - Good for production
   - **Mega ($99.99/month)**: 25,000 requests/month - High volume

4. Complete the subscription

### Step 3: Get Your API Key

1. After subscribing, you'll see your API key in the "Code Snippets" section
2. Look for the header: `x-rapidapi-key: YOUR_KEY_HERE`
3. Copy your API key

### Step 4: Add API Key to Your Environment

1. Open your `.env` file in the project root
2. Add your RapidAPI key:

```bash
RAPIDAPI_KEY=your-rapidapi-key-here
```

3. Save the file

### Step 5: Deploy Backend

Run the deployment script to update your Lambda function with the new API key:

```bash
./deploy-backend.sh
```

The script will:
- Validate your RapidAPI key is set
- Update the CloudFormation stack with the new parameter
- Deploy the updated YouTube downloader Lambda function

## Testing

Test your setup with a YouTube URL:

```bash
curl -X POST https://YOUR_API_URL/jobs \
  -H "Content-Type: application/json" \
  -d '{"youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

## API Usage

The RapidAPI YouTube MP3 service:

1. Accepts a YouTube video ID
2. Converts the video to MP3 (128kbps)
3. Returns a download URL
4. The download URL is valid for a limited time

### Response Format

```json
{
  "status": "ok",
  "link": "https://download-url.com/audio.mp3",
  "title": "Video Title"
}
```

### Status Values

- `ok`: Conversion successful, download link ready
- `processing`: Video is being converted, retry after 1 second
- `fail`: Conversion failed, check error message

## Cost Estimation

Based on typical usage:

- **Testing/Development**: Free tier (50 requests/month) is sufficient
- **Personal Use**: Pro plan ($9.99/month) for ~30 songs/day
- **Production**: Ultra plan ($29.99/month) for ~150 songs/day

Each transcription job = 1 API request

## Troubleshooting

### Error: "RAPIDAPI_KEY environment variable not set"

Make sure you've added `RAPIDAPI_KEY` to your `.env` file and redeployed.

### Error: "You are not subscribed to this API"

1. Go to [RapidAPI Dashboard](https://rapidapi.com/developer/dashboard)
2. Check your active subscriptions
3. Make sure you're subscribed to "YouTube MP3" API

### Error: "Rate limit exceeded"

You've exceeded your plan's monthly quota. Either:
- Wait until next month
- Upgrade to a higher plan

### Error: "Video processing timeout"

The video may be too long or unavailable. Try:
- A shorter video
- A different video
- Check if the video is publicly accessible

## Alternative APIs

If you prefer a different service, you can modify `backend/functions-v2/youtube-downloader/index.py` to use:

- [YouTube Video & MP3 Downloader](https://rapidapi.com/easeapi-easeapi-default/api/youtube-video-mp3-downloader-api)
- [YouTube Downloader (FAST)](https://rapidapi.com/toumirttv/api/youtube-downloader-fast)
- [YT Video & Audio Downloader](https://rapidapi.com/KvnqPoza/api/yt-video-audio-downloader-api)

All follow similar patterns - just update the API endpoint and headers.

## Security Notes

- ✅ API keys are stored as CloudFormation parameters (encrypted)
- ✅ Never commit `.env` file to git
- ✅ Use AWS Secrets Manager for production deployments
- ✅ Rotate API keys periodically

## Support

- RapidAPI Support: https://rapidapi.com/support
- YouTube MP3 API: https://t.me/api_chat_support
- ChordScout Issues: Create an issue in the GitHub repository
