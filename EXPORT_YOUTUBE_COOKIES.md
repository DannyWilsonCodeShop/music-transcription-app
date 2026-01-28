# Export YouTube Cookies Guide

YouTube now requires authentication to prevent bot detection. You need to export cookies from your browser where you're logged into YouTube.

## Method 1: Using Browser Extension (Recommended)

### Chrome/Edge:
1. Install "Get cookies.txt LOCALLY" extension: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
2. Go to https://www.youtube.com
3. Make sure you're logged in
4. Click the extension icon
5. Click "Export" to download cookies.txt
6. Save as `youtube-cookies.txt`

### Firefox:
1. Install "cookies.txt" extension: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/
2. Go to https://www.youtube.com
3. Make sure you're logged in
4. Click the extension icon
5. Click "Export" to download cookies.txt
6. Save as `youtube-cookies.txt`

## Method 2: Using yt-dlp Command (Alternative)

If you have yt-dlp installed locally:

```bash
# Export cookies from your browser
yt-dlp --cookies-from-browser chrome --cookies youtube-cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Replace `chrome` with your browser: `chrome`, `firefox`, `edge`, `safari`, `opera`, `brave`

## Upload Cookies to S3

Once you have the `youtube-cookies.txt` file:

```bash
# Upload to S3
aws s3 cp youtube-cookies.txt s3://chordscout-audio-temp-dev-090130568474/cookies/youtube-cookies.txt --profile chordscout
```

## Update Lambda Environment

The Lambda function will automatically use cookies from:
- Bucket: `chordscout-audio-temp-dev-090130568474`
- Key: `cookies/youtube-cookies.txt`

You can override these with environment variables:
- `COOKIES_BUCKET` - S3 bucket containing cookies
- `COOKIES_KEY` - S3 key for cookies file

## Important Notes

1. **Security**: Cookies contain your authentication tokens. Keep them secure!
2. **Expiration**: Cookies expire. You may need to re-export them periodically (usually every few months)
3. **Format**: The cookies.txt file must be in Netscape format (the extensions above handle this automatically)
4. **Testing**: After uploading, test with a YouTube URL to verify it works

## Troubleshooting

If you still get bot detection errors:
1. Make sure you're logged into YouTube in the browser you're exporting from
2. Try watching a video first, then export cookies
3. Make sure the cookies.txt file is in Netscape format
4. Check that the file was uploaded to S3 correctly
5. Verify Lambda has permission to read from the S3 bucket

## Alternative: Use --cookies-from-browser in Lambda

If you want yt-dlp to extract cookies directly from your browser on each run (not recommended for Lambda due to complexity), you would need to:
1. Package browser profile data
2. Install browser binaries in Lambda layer
3. Configure yt-dlp to use --cookies-from-browser

The cookies.txt approach is simpler and more reliable for Lambda.
