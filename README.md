# Music Transcription App

AI-powered application that transcribes lyrics and chord progressions from audio files or YouTube links.

## Features

- 🎵 Upload audio files (MP3, WAV, M4A, FLAC, OGG)
- 🎬 Process YouTube music videos
- 📝 AI-powered lyrics transcription using OpenAI Whisper
- 🎸 Chord progression detection
- ⚡ Serverless architecture with AWS
- 🚀 Automatic deployment via AWS Amplify

## Architecture

- **Frontend**: React app hosted on AWS Amplify
- **Backend**: AWS Lambda functions
- **Database**: Amazon DynamoDB
- **Storage**: Amazon S3
- **Queue**: Amazon SQS
- **API**: Amazon API Gateway

## Prerequisites

- Node.js 18+
- AWS Account
- AWS CLI configured
- Amplify CLI installed
- OpenAI API key
- YouTube Data API key

## Quick Start

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd music-transcription-app
```

### 2. Install Amplify CLI

```bash
npm install -g @aws-amplify/cli
amplify configure
```

### 3. Initialize Amplify

```bash
amplify init
amplify push
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 5. Configure Secrets

```bash
# Store OpenAI API key
aws secretsmanager create-secret \
  --name music-transcription/openai-key \
  --secret-string '{"OPENAI_API_KEY":"your-key"}' \
  --region us-east-1

# Store YouTube API key
aws secretsmanager create-secret \
  --name music-transcription/youtube-key \
  --secret-string '{"YOUTUBE_API_KEY":"your-key"}' \
  --region us-east-1
```

### 6. Run Locally

```bash
cd frontend
npm start
```

## Deployment

Push to GitHub main branch to trigger automatic deployment:

```bash
git add .
git commit -m "Deploy to production"
git push origin main
```

Amplify will automatically build and deploy your application.

## Project Structure

```
music-transcription-app/
├── amplify/                 # Amplify backend configuration
│   └── backend/
│       ├── api/            # API Gateway configuration
│       ├── function/       # Lambda functions
│       └── storage/        # S3 and DynamoDB configuration
├── frontend/               # React frontend application
│   ├── public/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   └── App.js         # Main app component
│   └── package.json
├── backend/                # Backend function code
│   ├── functions/
│   │   ├── api/           # API handler functions
│   │   ├── transcribe-worker/  # Worker functions
│   │   └── chord-detector/     # Chord detection
│   └── layers/            # Lambda layers
├── amplify.yml            # Amplify build configuration
├── .gitignore
└── README.md
```

## Documentation

See [PRODUCTION_DEPLOYMENT_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## Cost Estimate

Estimated monthly cost for moderate usage (~10,000 transcriptions):
- AWS Services: $50-85/month
- OpenAI Whisper API: $240/month
- **Total**: ~$290-325/month

## Support

For issues and questions:
- Check the [deployment guide](./PRODUCTION_DEPLOYMENT_GUIDE.md)
- Review CloudWatch logs
- Open an issue on GitHub

## License

MIT
