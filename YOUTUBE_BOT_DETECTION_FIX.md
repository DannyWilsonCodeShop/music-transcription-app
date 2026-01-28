# YouTube Bot Detection Fix

## Problem
YouTube is now requiring authentication to prevent bot detection:
```
ERROR: [youtube] Sign in to confirm you're not a bot
```

## Solution
Added cookie-based authentication to the yt-dlp downloader Lambda function.

## Changes Made

### 1. Updated Lambda Function
**File**: `backend/functions-v2/youtube-downloader/index.py`

Added cookie support:
- Downloads cookies from S3 before running yt-dlp
- Falls back to no cookies if not available (will fail for bot-protected videos)
- Uses cookies for authentication with YouTube

### 2. Environment Variables (Optional)
- `COOKIES_BUCKET` - S3 bucket containing cookies (default: same as audio bucket)
- `COOKIES_KEY` - S3 key for cookies file (default: `cookies/youtube-cookies.txt`)

## Setup Instructions

### Step 1: Export YouTube Cookies

See `EXPORT_YOUTUBE_COOKIES.md` for detailed instructions.

**Quick method**:
1. Install browser extension "Get cookies.txt LOCALLY"
2. Go to YouTube (logged in)
3. Export cookies
4. Save as `youtube-cookies.txt`

### Step 2: Upload to S3

```bash
aws s3 cp youtube-cookies.txt s3://chordscout-audio-temp-dev-090130568474/cookies/youtube-cookies.txt --profile chordscout
```

### Step 3: Test

```bash
curl -X POST https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev/jobs \
  -H "Content-Type: application/json" \
  -d '{"youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

## Security Considerations

1. **Cookies contain authentication tokens** - Keep them secure
2. **S3 bucket permissions** - Ensure only Lambda can read the cookies
3. **Cookie expiration** - Re-export cookies every few months
4. **Don't commit cookies** - Already in .gitignore

## Troubleshooting

### Still getting bot detection?
1. Make sure you're logged into YouTube when exporting cookies
2. Try watching a video first, then export
3. Verify cookies uploaded correctly to S3
4. Check Lambda has S3 read permissions

### Cookies not working?
1. Check cookies.txt format (must be Netscape format)
2. Verify file path in S3: `cookies/youtube-cookies.txt`
3. Check Lambda logs for cookie download errors

### Lambda can't read cookies?
1. Verify IAM role has S3 GetObject permission
2. Check bucket name and key are correct
3. Look for errors in CloudWatch logs

## Alternative Solutions (Not Implemented)

1. **Use YouTube Data API** - Requires API key, has quotas
2. **Use --cookies-from-browser** - Complex in Lambda, requires browser binaries
3. **Use third-party services** - Costs money, less reliable
4. **Rotate IP addresses** - Doesn't solve authentication requirement

## Maintenance

- **Re-export cookies**: Every 2-3 months or when they expire
- **Monitor failures**: Watch for bot detection errors in logs
- **Update yt-dlp**: Keep library updated for latest YouTube changes

## Deployment Status

✅ Lambda function updated with cookie support
✅ Documentation created
⏳ Waiting for cookies to be uploaded to S3

## Next Steps

1. Export YouTube cookies from your browser
2. Upload to S3 at `s3://chordscout-audio-temp-dev-090130568474/cookies/youtube-cookies.txt`
3. Test with a YouTube URL
4. Monitor for any issues
