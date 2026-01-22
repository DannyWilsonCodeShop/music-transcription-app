# Project Structure

Complete directory structure for the Music Transcription App.

```
music-transcription-app/
│
├── 📄 README.md                          # Project overview and quick start
├── 📄 SETUP.md                           # Detailed setup instructions
├── 📄 PRODUCTION_DEPLOYMENT_GUIDE.md     # AWS deployment guide
├── 📄 CONTRIBUTING.md                    # Contribution guidelines
├── 📄 LICENSE                            # MIT License
├── 📄 package.json                       # Root package configuration
├── 📄 amplify.yml                        # Amplify build configuration
├── 📄 .gitignore                         # Git ignore rules
├── 📄 .env.example                       # Environment variables template
├── 🔧 quickstart.sh                      # Quick setup script
│
├── 📁 frontend/                          # React frontend application
│   ├── 📁 public/
│   │   └── index.html                    # HTML template
│   │
│   ├── 📁 src/
│   │   ├── 📁 components/
│   │   │   ├── FileUpload.js             # File upload component
│   │   │   ├── FileUpload.css            # File upload styles
│   │   │   ├── YouTubeInput.js           # YouTube link input
│   │   │   ├── YouTubeInput.css          # YouTube input styles
│   │   │   ├── JobStatus.js              # Job status display
│   │   │   └── JobStatus.css             # Job status styles
│   │   │
│   │   ├── App.js                        # Main app component
│   │   ├── App.css                       # App styles
│   │   ├── index.js                      # React entry point
│   │   └── index.css                     # Global styles
│   │
│   └── package.json                      # Frontend dependencies
│
├── 📁 backend/                           # Backend Lambda functions
│   └── 📁 functions/
│       │
│       ├── 📁 api/                       # API Gateway handler
│       │   ├── index.js                  # API routes and logic
│       │   └── package.json              # API dependencies
│       │
│       ├── 📁 transcribe-worker/         # Worker function
│       │   ├── index.js                  # Transcription processing
│       │   └── package.json              # Worker dependencies
│       │
│       └── 📁 chord-detector/            # Chord detection
│           ├── index.py                  # Python chord detection
│           └── requirements.txt          # Python dependencies
│
└── 📁 amplify/                           # Amplify backend (auto-generated)
    └── backend/
        ├── api/                          # API Gateway config
        ├── function/                     # Lambda functions config
        └── storage/                      # S3 and DynamoDB config
```

## Key Files Explained

### Root Level

- **README.md**: Project overview, features, quick start guide
- **SETUP.md**: Step-by-step setup instructions for development
- **PRODUCTION_DEPLOYMENT_GUIDE.md**: Complete AWS deployment guide
- **amplify.yml**: Amplify CI/CD build configuration
- **package.json**: Root package with scripts for the entire project
- **quickstart.sh**: Automated setup script

### Frontend (`/frontend`)

- **src/App.js**: Main React component with tab navigation
- **src/components/FileUpload.js**: Drag-and-drop file upload with progress
- **src/components/YouTubeInput.js**: YouTube URL input and submission
- **src/components/JobStatus.js**: Real-time job status polling and results display
- **package.json**: React, AWS Amplify, and UI dependencies

### Backend (`/backend/functions`)

#### API Handler (`/api`)
- **index.js**: 
  - POST /transcribe/upload - Generate S3 presigned URL
  - POST /transcribe/youtube - Submit YouTube link
  - GET /transcribe/job/:id - Get job status
  - GET /transcribe/jobs - List user jobs

#### Worker (`/transcribe-worker`)
- **index.js**:
  - Download audio from S3 or YouTube
  - Transcribe lyrics using OpenAI Whisper
  - Detect chords (placeholder)
  - Save results to S3 and DynamoDB

#### Chord Detector (`/chord-detector`)
- **index.py**: Python-based chord detection (placeholder for ML model)

## AWS Resources Created

When you run `amplify push`, these resources are created:

### Storage
- **S3 Bucket**: Audio file storage with lifecycle policies
- **DynamoDB Table**: TranscriptionJobs with GSI indexes

### Compute
- **Lambda Functions**: 
  - transcribeAPI (API handler)
  - transcribeWorker (Processing worker)
  - chordDetector (Chord detection)

### API & Queue
- **API Gateway**: REST API with CORS enabled
- **SQS Queue**: Job queue for async processing

### Security
- **IAM Roles**: Least-privilege roles for each Lambda
- **Secrets Manager**: Secure storage for API keys

### Hosting
- **Amplify Hosting**: Frontend hosting with CloudFront CDN
- **CI/CD**: Automatic deployments from GitHub

## Data Flow

1. **User uploads file** → Frontend
2. **Request presigned URL** → API Gateway → Lambda
3. **Upload to S3** → Direct from browser
4. **Job queued** → SQS
5. **Worker processes** → Lambda pulls from SQS
6. **Download audio** → From S3 or YouTube
7. **Transcribe** → OpenAI Whisper API
8. **Detect chords** → Chord detector Lambda
9. **Save results** → S3 + DynamoDB
10. **Frontend polls** → API Gateway → Lambda → DynamoDB
11. **Display results** → React components

## Environment Variables

### Frontend (Amplify Console)
- `NODE_ENV`: production
- `REACT_APP_API_NAME`: transcriptionAPI

### Backend (Lambda)
- `DYNAMODB_TABLE`: TranscriptionJobs table name
- `S3_BUCKET`: Audio storage bucket name
- `SQS_QUEUE_URL`: Job queue URL
- `OPENAI_SECRET_ARN`: Secrets Manager ARN
- `YOUTUBE_SECRET_ARN`: Secrets Manager ARN

## Development Workflow

1. **Local Development**:
   ```bash
   cd frontend
   npm start
   ```

2. **Test Backend Locally**:
   ```bash
   amplify mock api
   ```

3. **Deploy Backend**:
   ```bash
   amplify push
   ```

4. **Deploy Frontend**:
   ```bash
   git push origin main  # Auto-deploys via Amplify
   ```

## Monitoring

- **CloudWatch Logs**: `/aws/lambda/transcribeAPI`, `/aws/lambda/transcribeWorker`
- **CloudWatch Metrics**: Lambda invocations, errors, duration
- **X-Ray**: Distributed tracing (optional)
- **Amplify Console**: Build logs and deployment status

## Cost Breakdown

See PRODUCTION_DEPLOYMENT_GUIDE.md for detailed cost estimates.

**Estimated**: $290-375/month for moderate usage (10,000 transcriptions)

## Next Steps

1. ✅ Repository structure created
2. ⏭️ Run `./quickstart.sh` to install dependencies
3. ⏭️ Follow SETUP.md for AWS configuration
4. ⏭️ Deploy using PRODUCTION_DEPLOYMENT_GUIDE.md
5. ⏭️ Add authentication (Cognito)
6. ⏭️ Implement rate limiting
7. ⏭️ Improve chord detection accuracy

## Support

- 📖 Documentation: See README.md and SETUP.md
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
- 📧 Email: your-email@example.com
