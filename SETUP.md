# Setup Instructions

Quick start guide for setting up the Music Transcription App.

## Prerequisites

1. **Node.js 18+** - [Download](https://nodejs.org/)
2. **AWS Account** - [Sign up](https://aws.amazon.com/)
3. **Git** - [Download](https://git-scm.com/)
4. **OpenAI API Key** - [Get key](https://platform.openai.com/api-keys)
5. **YouTube Data API Key** - [Get key](https://console.cloud.google.com/apis/credentials)

## Step 1: Install AWS CLI

```bash
# macOS
brew install awscli

# Verify installation
aws --version
```

## Step 2: Configure AWS CLI

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

## Step 3: Install Amplify CLI

```bash
npm install -g @aws-amplify/cli

# Configure Amplify
amplify configure
```

## Step 4: Clone and Initialize

```bash
# Clone repository
git clone <your-repo-url>
cd music-transcription-app

# Initialize Amplify
amplify init
# Follow prompts:
# - Project name: musictranscription
# - Environment: dev
# - Default editor: Visual Studio Code (or your choice)
# - App type: javascript
# - Framework: react
# - Source directory: frontend/src
# - Distribution directory: frontend/build
# - Build command: npm run build
# - Start command: npm start
```

## Step 5: Add Backend Resources

```bash
# Add S3 storage
amplify add storage
# Choose: Content (Images, audio, video, etc.)
# Friendly name: audioStorage
# Bucket name: (accept default)
# Access: Auth and guest users

# Add DynamoDB
amplify add storage
# Choose: NoSQL Database
# Table name: TranscriptionJobs
# Partition key: id (String)
# Sort key: createdAt (Number)
# Add GSI: Yes
# - GSI name: userIdIndex
# - Partition key: userId
# - Sort key: createdAt

# Add API
amplify add api
# Choose: REST
# Friendly name: transcriptionAPI
# Path: /transcribe
# Lambda source: Create new Lambda
# Function name: transcribeAPI
# Runtime: NodeJS
# Template: Hello World

# Add worker function
amplify add function
# Name: transcribeWorker
# Runtime: NodeJS
# Template: Hello World

# Push to AWS
amplify push
```

## Step 6: Store API Keys

```bash
# Store OpenAI API key
aws secretsmanager create-secret \
  --name music-transcription/openai-key \
  --secret-string '{"OPENAI_API_KEY":"your-openai-key-here"}' \
  --region us-east-1

# Store YouTube API key
aws secretsmanager create-secret \
  --name music-transcription/youtube-key \
  --secret-string '{"YOUTUBE_API_KEY":"your-youtube-key-here"}' \
  --region us-east-1
```

## Step 7: Install Frontend Dependencies

```bash
cd frontend
npm install
```

## Step 8: Run Locally

```bash
# From frontend directory
npm start
```

Your app should open at http://localhost:3000

## Step 9: Deploy to Production

```bash
# Connect to GitHub
git remote add origin <your-github-repo-url>
git add .
git commit -m "Initial commit"
git push -u origin main

# Add hosting
amplify add hosting
# Choose: Amplify Console
# Type: Continuous deployment

amplify publish
```

## Troubleshooting

### Amplify CLI not found
```bash
npm install -g @aws-amplify/cli
```

### AWS credentials error
```bash
aws configure
# Re-enter your credentials
```

### Build errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Lambda timeout
Increase timeout in Amplify Console:
1. Go to Backend environments
2. Select your function
3. Increase timeout to 900 seconds

## Next Steps

1. Review [PRODUCTION_DEPLOYMENT_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md)
2. Set up monitoring in CloudWatch
3. Configure custom domain
4. Add user authentication with Cognito
5. Implement rate limiting

## Support

- AWS Amplify Docs: https://docs.amplify.aws/
- GitHub Issues: <your-repo-url>/issues
