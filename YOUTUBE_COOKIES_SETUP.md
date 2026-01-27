# YouTube Cookies Setup

YouTube has implemented bot detection that blocks yt-dlp from downloading videos. To fix this, we need to provide authentication cookies from a logged-in browser session.

## Why This Is Needed

YouTube's error: `Sign in to confirm you're not a bot`

This happens because YouTube detects automated downloads and requires authentication. By providing cookies from your browser, yt-dlp can authenticate as if it's your browser.

## Setup Methods

### Method 1: Browser Extension (Easiest)

1. **Install the extension:**
   - **Chrome/Edge**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - **Firefox**: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. **Export cookies:**
   - Go to [youtube.com](https://youtube.com) and make sure you're logged in
   - Click the extension icon
   - Click "Export" or "Download"
   - Save the file as `youtube-cookies.txt` in the ChordScout directory

3. **Upload to S3:**
   ```bash
   ./setup-youtube-cookies.sh
   ```

### Method 2: Using yt-dlp (If you have it installed locally)

```bash
# Chrome
yt-dlp --cookies-from-browser chrome --cookies youtube-cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Firefox
yt-dlp --cookies-from-browser firefox --cookies youtube-cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Safari
yt-dlp --cookies-from-browser safari --cookies youtube-cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Then upload
./setup-youtube-cookies.sh
```

## How It Works

1. The cookies are stored in S3 at: `s3://chordscout-audio-dev-090130568474/config/youtube-cookies.txt`
2. The Lambda function downloads them before running yt-dlp
3. yt-dlp uses the cookies to authenticate with YouTube
4. Downloads work without bot detection

## Security Considerations

⚠️ **Important:**
- These cookies give access to your YouTube account
- Only use this on your own AWS account
- Don't share the cookies file
- Cookies expire after some time (usually weeks/months)
- You'll need to refresh them when they expire

## Troubleshooting

### Still getting bot detection errors?

1. **Cookies expired**: Re-export fresh cookies from your browser
2. **Wrong format**: Make sure the file is in Netscape format (the extensions do this automatically)
3. **Not logged in**: Make sure you're logged into YouTube when exporting cookies

### Remove cookies from S3:

```bash
aws s3 rm s3://chordscout-audio-dev-090130568474/config/youtube-cookies.txt --region us-east-1 --profile chordscout
```

## Testing

After uploading cookies, try a YouTube transcription:

1. Go to your ChordScout app
2. Paste a YouTube URL
3. Click "Start Transcription"
4. Check the progress - it should now download successfully

## Alternative: Use File Upload Instead

If you don't want to deal with YouTube cookies, you can:
1. Download the YouTube video manually using a tool like [yt-dlp](https://github.com/yt-dlp/yt-dlp) or [youtube-dl](https://youtube-dl.org/)
2. Use the file upload feature in ChordScout to upload the audio file directly
