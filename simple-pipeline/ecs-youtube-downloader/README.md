# ECS YouTube Downloader

Reliable YouTube audio downloader using yt-dlp in ECS Fargate.

## Features

- ✅ Uses yt-dlp (most reliable YouTube downloader)
- ✅ Runs in ECS Fargate (no server management)
- ✅ Best audio quality (320kbps MP3)
- ✅ Automatic retry and error handling
- ✅ Direct upload to S3
- ✅ Job tracking in DynamoDB

## Architecture

1. API Gateway receives request
2. Lambda triggers ECS task
3. ECS task downloads audio with yt-dlp
4. Audio uploaded to S3
5. Job status updated in DynamoDB

## Cost

~$0.01 per download (ECS Fargate Spot pricing)

Much cheaper and more reliable than RapidAPI ($20/month).

## Deployment

See `GITHUB_ACTIONS_SETUP.md` for build instructions.
See `deploy-ecs.sh` for infrastructure deployment.
