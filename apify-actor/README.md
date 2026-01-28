# YouTube Audio Downloader Actor

This Apify actor downloads audio from YouTube videos and returns direct download links.

## Input

```json
{
  "youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

## Output

```json
{
  "videoId": "dQw4w9WgXcQ",
  "title": "Video Title",
  "duration": 213,
  "channel": "Channel Name",
  "audioUrl": "https://...",
  "format": "webm",
  "bitrate": 160,
  "quality": "AUDIO_QUALITY_MEDIUM"
}
```

## Deployment

1. Push this code to your GitHub repository: `https://github.com/DannyWilsonCodeShop/music-transcription-app`
2. In Apify Console, go to your actor settings
3. Set the source to GitHub
4. Set the repository to your GitHub repo
5. Set the build directory to `apify-actor`
6. Save and build

## Testing Locally

```bash
cd apify-actor
npm install
export APIFY_INPUT_KEY=INPUT
echo '{"youtubeUrl":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' > apify_storage/key_value_stores/default/INPUT.json
npm start
```
