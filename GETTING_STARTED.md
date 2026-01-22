# Getting Started - Quick Guide

Get your Music Transcription App up and running in minutes!

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites Check

Make sure you have:
- ✅ Node.js 18+ installed
- ✅ AWS Account created
- ✅ Git installed
- ✅ OpenAI API key ready
- ✅ YouTube Data API key ready

### 2. Run Quick Setup

```bash
# Make the script executable and run it
chmod +x quickstart.sh
./quickstart.sh
```

This will install all dependencies automatically.

### 3. Configure AWS

```bash
# Install AWS CLI (if not already installed)
brew install awscli

# Configure your credentials
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Region: us-east-1
# Output format: json
```

### 4. Initialize Amplify

```bash
# Install Amplify CLI globally
npm install -g @aws-amplify/cli

# Configure Amplify
amplify configure
# Follow the prompts to create an IAM user

# Initialize your project
amplify init
# Project name: musictranscription
# Environment: dev
# Default editor: (your choice)
# App type: javascript
# Framework: react
# Source directory: frontend/src
# Distribution directory: frontend/build
# Build command: npm run build
# Start command: npm start
```

### 5. Add Backend Resources

```bash
# Add S3 storage for audio files
amplify add storage
# Service: Content
# Friendly name: audioStorage
# Bucket name: (accept default)
# Access: Auth and guest users

# Add DynamoDB for job tracking
amplify add storage
# Service: NoSQL Database
# Table name: TranscriptionJobs
# Partition key: id (String)
# Sort key: createdAt (Number)
# Add GSI: Yes
  # GSI name: userIdIndex
  # Partition key: userId
  # Sort key: createdAt

# Add REST API
amplify add api
# Service: REST
# Friendly name: transcriptionAPI
# Path: /transcribe
# Lambda source: Create new
# Function name: transcribeAPI
# Runtime: NodeJS
# Template: Hello World

# Add worker function
amplify add function
# Name: transcribeWorker
# Runtime: NodeJS
# Template: Hello World
# Advanced settings: Yes
# - Access other resources: Yes
# - Select: storage (both S3 and DynamoDB)
# - Environment variables: Yes
#   - OPENAI_SECRET_ARN: (will add later)

# Deploy everything to AWS
amplify push
```

### 6. Store API Keys Securely

```bash
# Store OpenAI API key
aws secretsmanager create-secret \
  --name music-transcription/openai-key \
  --secret-string '{"OPENAI_API_KEY":"sk-your-actual-key-here"}' \
  --region us-east-1

# Store YouTube API key
aws secretsmanager create-secret \
  --name music-transcription/youtube-key \
  --secret-string '{"YOUTUBE_API_KEY":"your-youtube-key-here"}' \
  --region us-east-1

# Get the ARN of the OpenAI secret
aws secretsmanager describe-secret \
  --secret-id music-transcription/openai-key \
  --region us-east-1 \
  --query ARN \
  --output text

# Update Lambda environment variable with the ARN
# (Do this in AWS Console or update amplify/backend/function/transcribeWorker)
```

### 7. Run Locally

```bash
cd frontend
npm start
```

Your app will open at http://localhost:3000 🎉

## 📦 What Was Created?

After running these steps, you'll have:

### AWS Resources
- ✅ S3 bucket for audio storage
- ✅ DynamoDB table for job tracking
- ✅ Lambda functions (API + Worker)
- ✅ API Gateway REST API
- ✅ SQS queue for job processing
- ✅ IAM roles with proper permissions
- ✅ Secrets Manager for API keys

### Local Files
- ✅ React frontend application
- ✅ Lambda function code
- ✅ Amplify configuration
- ✅ All dependencies installed

## 🧪 Test It Out

1. **Upload a file**: Drag and drop an MP3 file
2. **Or paste a YouTube link**: Try a music video URL
3. **Watch the status**: See real-time processing updates
4. **View results**: Lyrics and chords appear when complete

## 🚀 Deploy to Production

### Option 1: GitHub + Amplify (Recommended)

```bash
# Create GitHub repository
gh repo create music-transcription-app --public --source=. --remote=origin

# Push code
git add .
git commit -m "Initial commit"
git push -u origin main

# Connect to Amplify Console
amplify add hosting
# Choose: Amplify Console
# Type: Continuous deployment

amplify publish
```

### Option 2: Manual Deploy

```bash
# Build frontend
cd frontend
npm run build

# Deploy
amplify publish
```

## 📊 Monitor Your App

### CloudWatch Logs
```bash
# View API logs
aws logs tail /aws/lambda/transcribeAPI --follow

# View worker logs
aws logs tail /aws/lambda/transcribeWorker --follow
```

### Amplify Console
1. Go to AWS Amplify Console
2. Select your app
3. View deployments, logs, and metrics

## 💰 Cost Estimate

For development/testing (low usage):
- AWS Services: ~$5-10/month
- OpenAI API: Pay per use ($0.006/minute)

For production (10,000 transcriptions/month):
- AWS Services: ~$50-85/month
- OpenAI API: ~$240/month
- **Total**: ~$290-325/month

## 🆘 Troubleshooting

### "Amplify command not found"
```bash
npm install -g @aws-amplify/cli
```

### "AWS credentials not configured"
```bash
aws configure
```

### "Module not found" errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Lambda timeout errors
Increase timeout in Amplify Console:
1. Backend environments → Functions
2. Select function → Edit
3. Timeout: 900 seconds
4. Memory: 3008 MB (for worker)

### OpenAI API errors
- Check your API key in Secrets Manager
- Verify you have credits in your OpenAI account
- Check CloudWatch logs for detailed error messages

## 📚 Next Steps

1. ✅ App is running locally
2. ⏭️ Review [PRODUCTION_DEPLOYMENT_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md)
3. ⏭️ Add user authentication (Cognito)
4. ⏭️ Implement rate limiting
5. ⏭️ Set up monitoring alerts
6. ⏭️ Configure custom domain
7. ⏭️ Improve chord detection

## 🎯 Key Features to Implement

- [ ] User authentication (AWS Cognito)
- [ ] Rate limiting per user
- [ ] Batch processing
- [ ] Export results (PDF, JSON)
- [ ] Song library/history
- [ ] Better chord detection (ML model)
- [ ] Real-time progress updates (WebSocket)
- [ ] Mobile app version

## 📖 Documentation

- **README.md**: Project overview
- **SETUP.md**: Detailed setup guide
- **PRODUCTION_DEPLOYMENT_GUIDE.md**: AWS deployment
- **PROJECT_STRUCTURE.md**: Code organization
- **CONTRIBUTING.md**: How to contribute

## 🤝 Get Help

- 📖 Check documentation files
- 🐛 Open an issue on GitHub
- 💬 Join discussions
- 📧 Contact maintainers

## 🎉 You're Ready!

Your Music Transcription App is now set up and ready to use. Start transcribing! 🎵

---

**Pro Tip**: Bookmark this guide and the PRODUCTION_DEPLOYMENT_GUIDE.md for reference.
