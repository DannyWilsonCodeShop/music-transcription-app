# Production Deployment Guide

## Option 1: AWS Amplify Console (Recommended)

1. **Push to GitHub/GitLab/Bitbucket:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Music Transcription App"
   git branch -M main
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Deploy via Amplify Console:**
   - Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
   - Click "New app" → "Host web app"
   - Connect your Git repository
   - Amplify will auto-detect the build settings
   - Deploy!

## Option 2: Manual Deployment

1. **Create Amplify App:**
   ```bash
   aws amplify create-app --name music-transcription-app --repository <your-repo-url>
   ```

2. **Create Branch:**
   ```bash
   aws amplify create-branch --app-id <app-id> --branch-name main
   ```

3. **Start Build:**
   ```bash
   aws amplify start-job --app-id <app-id> --branch-name main --job-type RELEASE
   ```

## Environment Variables Needed

Set these in the Amplify Console under "Environment variables":
- `OPENAI_API_KEY`: Your OpenAI API key
- `NODE_VERSION`: 18

## Build Settings (amplify.yml)

The build configuration will be auto-detected, but here's the manual version:

```yaml
version: 1
backend:
  phases:
    build:
      commands:
        - npm ci
        - npx ampx pipeline-deploy --branch $AWS_BRANCH --app-id $AWS_APP_ID
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: dist
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```