# Production Deployment Guide
## Music Transcription App (Lyrics & Chords)
### AWS Amplify + GitHub Deployment

This guide covers deploying a production-ready application that transcribes lyrics and chord progressions from audio files or YouTube links using AWS services and AWS Amplify.

---

## Architecture Overview

### AWS Services Stack
- **AWS Amplify**: Frontend hosting, CI/CD, backend deployment
- **Amazon API Gateway**: RESTful API endpoints
- **AWS Lambda**: Serverless backend functions
- **Amazon S3**: Audio file storage
- **Amazon DynamoDB**: NoSQL database for jobs and user data
- **Amazon SQS**: Job queue for async processing
- **AWS Step Functions**: Orchestrate transcription workflows
- **Amazon EventBridge**: Event-driven architecture
- **Amazon CloudFront**: CDN (integrated with Amplify)
- **AWS Secrets Manager**: API keys and credentials
- **Amazon CloudWatch**: Logging and monitoring
- **Amazon Cognito**: User authentication (optional)
- **Amazon SES**: Email notifications

### Application Flow
```
User → Amplify Frontend → API Gateway → Lambda Functions
                                          ↓
                                    SQS Queue → Lambda Workers
                                          ↓
                                    OpenAI Whisper API
                                          ↓
                                    Results → DynamoDB
                                          ↓
                                    S3 Storage
```

---

## Prerequisites

### Required Accounts & API Keys
- [ ] AWS Account with billing enabled
- [ ] GitHub account with repository access
- [ ] OpenAI API key (for Whisper API)
- [ ] YouTube Data API key (for metadata)
- [ ] Domain name (optional, Amplify provides subdomain)
- [ ] AWS CLI installed and configured locally

### Development Tools
- AWS CLI v2
- AWS Amplify CLI
- Node.js 18+ and npm/yarn
- Git
- Code editor (VS Code recommended)

---

## Step 1: GitHub Repository Setup

### Repository Structure
```
music-transcription-app/
├── amplify/
│   ├── backend/
│   │   ├── api/
│   │   ├── function/
│   │   └── storage/
│   └── team-provider-info.json
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.js
│   ├── package.json
│   └── amplify.yml
├── backend/
│   ├── functions/
│   │   ├── api/
│   │   ├── transcribe-worker/
│   │   └── chord-detector/
│   └── layers/
├── .gitignore
└── README.md
```

### Create GitHub Repository
```bash
# Initialize repository
git init
git add .
git commit -m "Initial commit"

# Create GitHub repo and push
gh repo create music-transcription-app --public --source=. --remote=origin
git push -u origin main
```

---

## Step 2: AWS Account Setup

### Install and Configure AWS CLI
```bash
# Install AWS CLI (macOS)
brew install awscli

# Configure AWS credentials
aws configure
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### Install Amplify CLI
```bash
# Install Amplify CLI globally
npm install -g @aws-amplify/cli

# Configure Amplify
amplify configure

# This will:
# 1. Open AWS Console to create IAM user
# 2. Create user with AdministratorAccess-Amplify policy
# 3. Save credentials locally
```

---

## Step 3: Initialize Amplify Project

### Initialize Amplify in Your Project
```bash
cd music-transcription-app

# Initialize Amplify
amplify init

# Configuration prompts:
# ? Enter a name for the project: musictranscription
# ? Initialize the project with the above configuration? Yes
# ? Select the authentication method: AWS profile
# ? Please choose the profile you want to use: default
```

### Amplify Configuration File
Create `amplify.yml` in the root directory:
```yaml
version: 1
backend:
  phases:
    build:
      commands:
        - '# Execute Amplify CLI with the helper script'
        - amplifyPush --simple
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: frontend/build
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
```

---

## Step 4: Configure AWS Backend Services

### Add S3 Storage for Audio Files
```bash
amplify add storage

# Configuration:
# ? Select from one of the below mentioned services: Content
# ? Provide a friendly name for your resource: audioStorage
# ? Provide bucket name: musictranscription-audio-{env}
# ? Who should have access: Auth and guest users
# ? What kind of access do you want for Authenticated users? create, read, delete
# ? What kind of access do you want for Guest users? read
```

### Add DynamoDB Tables
```bash
amplify add storage

# Configuration:
# ? Select from one of the below mentioned services: NoSQL Database
# ? Provide a friendly name: transcriptionJobs
# ? Provide table name: TranscriptionJobs

# Add GSI for querying by user and status
```

Create `amplify/backend/storage/transcriptionJobs/parameters.json`:
```json
{
  "tableName": "TranscriptionJobs",
  "partitionKeyName": "id",
  "partitionKeyType": "S",
  "sortKeyName": "createdAt",
  "sortKeyType": "N",
  "gsi": [
    {
      "name": "userIdIndex",
      "partitionKeyName": "userId",
      "partitionKeyType": "S",
      "sortKeyName": "createdAt",
      "sortKeyType": "N"
    },
    {
      "name": "statusIndex",
      "partitionKeyName": "status",
      "partitionKeyType": "S",
      "sortKeyName": "createdAt",
      "sortKeyType": "N"
    }
  ]
}
```

### Add API Gateway
```bash
amplify add api

# Configuration:
# ? Select from one of the below mentioned services: REST
# ? Provide a friendly name for your resource: transcriptionAPI
# ? Provide a path: /transcribe
# ? Choose a Lambda source: Create a new Lambda function
# ? Provide an AWS Lambda function name: transcribeHandler
# ? Choose the runtime: NodeJS
# ? Choose the function template: Serverless ExpressJS function
# ? Do you want to configure advanced settings? No
# ? Do you want to edit the local lambda function now? No
# ? Restrict API access? Yes
# ? Who should have access? Authenticated and Guest users
```

### Add Lambda Functions
```bash
# Main API handler
amplify add function
# Name: transcribeAPI
# Runtime: Node.js 18.x
# Template: Hello World

# Worker function for processing
amplify add function
# Name: transcribeWorker
# Runtime: Node.js 18.x
# Template: Hello World
# Add environment variables for OpenAI API key

# Chord detection function
amplify add function
# Name: chordDetector
# Runtime: Python 3.11
# Template: Hello World
```

### Configure Lambda Function - API Handler
Create `amplify/backend/function/transcribeAPI/src/index.js`:
```javascript
const AWS = require('aws-sdk');
const { v4: uuidv4 } = require('uuid');

const dynamodb = new AWS.DynamoDB.DocumentClient();
const sqs = new AWS.SQS();
const s3 = new AWS.S3();

const TABLE_NAME = process.env.DYNAMODB_TABLE;
const QUEUE_URL = process.env.SQS_QUEUE_URL;
const BUCKET_NAME = process.env.S3_BUCKET;

exports.handler = async (event) => {
  const { httpMethod, path, body } = event;
  
  try {
    switch (httpMethod) {
      case 'POST':
        if (path === '/transcribe/upload') {
          return await handleFileUpload(JSON.parse(body));
        } else if (path === '/transcribe/youtube') {
          return await handleYouTubeLink(JSON.parse(body));
        }
        break;
        
      case 'GET':
        if (path.startsWith('/transcribe/job/')) {
          const jobId = path.split('/').pop();
          return await getJobStatus(jobId);
        } else if (path === '/transcribe/jobs') {
          return await listJobs(event.queryStringParameters);
        }
        break;
        
      default:
        return response(405, { error: 'Method not allowed' });
    }
  } catch (error) {
    console.error('Error:', error);
    return response(500, { error: error.message });
  }
};

async function handleFileUpload(data) {
  const { fileName, fileType, userId } = data;
  const jobId = uuidv4();
  const s3Key = `uploads/${userId}/${jobId}/${fileName}`;
  
  // Generate presigned URL for upload
  const uploadUrl = s3.getSignedUrl('putObject', {
    Bucket: BUCKET_NAME,
    Key: s3Key,
    ContentType: fileType,
    Expires: 300 // 5 minutes
  });
  
  // Create job record
  const job = {
    id: jobId,
    userId,
    sourceType: 'file',
    fileName,
    s3Key,
    status: 'pending',
    createdAt: Date.now()
  };
  
  await dynamodb.put({
    TableName: TABLE_NAME,
    Item: job
  }).promise();
  
  // Queue processing job
  await sqs.sendMessage({
    QueueUrl: QUEUE_URL,
    MessageBody: JSON.stringify({ jobId, type: 'file' })
  }).promise();
  
  return response(200, { jobId, uploadUrl });
}

async function handleYouTubeLink(data) {
  const { youtubeUrl, userId } = data;
  const jobId = uuidv4();
  
  // Create job record
  const job = {
    id: jobId,
    userId,
    sourceType: 'youtube',
    youtubeUrl,
    status: 'pending',
    createdAt: Date.now()
  };
  
  await dynamodb.put({
    TableName: TABLE_NAME,
    Item: job
  }).promise();
  
  // Queue processing job
  await sqs.sendMessage({
    QueueUrl: QUEUE_URL,
    MessageBody: JSON.stringify({ jobId, type: 'youtube', youtubeUrl })
  }).promise();
  
  return response(200, { jobId });
}

async function getJobStatus(jobId) {
  const result = await dynamodb.get({
    TableName: TABLE_NAME,
    Key: { id: jobId }
  }).promise();
  
  if (!result.Item) {
    return response(404, { error: 'Job not found' });
  }
  
  return response(200, result.Item);
}

async function listJobs(params) {
  const { userId, limit = 20 } = params || {};
  
  const queryParams = {
    TableName: TABLE_NAME,
    IndexName: 'userIdIndex',
    KeyConditionExpression: 'userId = :userId',
    ExpressionAttributeValues: {
      ':userId': userId
    },
    Limit: parseInt(limit),
    ScanIndexForward: false // Most recent first
  };
  
  const result = await dynamodb.query(queryParams).promise();
  
  return response(200, {
    jobs: result.Items,
    lastKey: result.LastEvaluatedKey
  });
}

function response(statusCode, body) {
  return {
    statusCode,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': '*',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  };
}
```

### Configure Lambda Function - Worker
Create `amplify/backend/function/transcribeWorker/src/index.js`:
```javascript
const AWS = require('aws-sdk');
const axios = require('axios');
const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs').promises;
const path = require('path');

const execAsync = promisify(exec);
const dynamodb = new AWS.DynamoDB.DocumentClient();
const s3 = new AWS.S3();
const secretsManager = new AWS.SecretsManager();

const TABLE_NAME = process.env.DYNAMODB_TABLE;
const BUCKET_NAME = process.env.S3_BUCKET;

let openaiApiKey;

exports.handler = async (event) => {
  // Get OpenAI API key from Secrets Manager
  if (!openaiApiKey) {
    const secret = await secretsManager.getSecretValue({
      SecretId: process.env.OPENAI_SECRET_ARN
    }).promise();
    openaiApiKey = JSON.parse(secret.SecretString).OPENAI_API_KEY;
  }
  
  for (const record of event.Records) {
    const message = JSON.parse(record.body);
    const { jobId, type, youtubeUrl } = message;
    
    try {
      await updateJobStatus(jobId, 'processing');
      
      let audioFilePath;
      
      if (type === 'youtube') {
        // Download from YouTube
        audioFilePath = await downloadYouTubeAudio(youtubeUrl, jobId);
      } else {
        // Download from S3
        audioFilePath = await downloadFromS3(jobId);
      }
      
      // Transcribe lyrics
      const lyrics = await transcribeLyrics(audioFilePath);
      
      // Detect chords (invoke chord detector Lambda)
      const chords = await detectChords(audioFilePath);
      
      // Save results
      await saveResults(jobId, lyrics, chords);
      
      // Cleanup
      await fs.unlink(audioFilePath);
      
      await updateJobStatus(jobId, 'completed', { lyrics, chords });
      
    } catch (error) {
      console.error(`Error processing job ${jobId}:`, error);
      await updateJobStatus(jobId, 'failed', { error: error.message });
    }
  }
};

async function downloadYouTubeAudio(url, jobId) {
  const outputPath = `/tmp/${jobId}.mp3`;
  
  // Using yt-dlp (needs to be in Lambda layer)
  await execAsync(
    `yt-dlp -x --audio-format mp3 -o "${outputPath}" "${url}"`
  );
  
  return outputPath;
}

async function downloadFromS3(jobId) {
  const job = await dynamodb.get({
    TableName: TABLE_NAME,
    Key: { id: jobId }
  }).promise();
  
  const s3Key = job.Item.s3Key;
  const outputPath = `/tmp/${jobId}${path.extname(s3Key)}`;
  
  const s3Object = await s3.getObject({
    Bucket: BUCKET_NAME,
    Key: s3Key
  }).promise();
  
  await fs.writeFile(outputPath, s3Object.Body);
  
  return outputPath;
}

async function transcribeLyrics(audioFilePath) {
  const audioBuffer = await fs.readFile(audioFilePath);
  
  const formData = new FormData();
  formData.append('file', new Blob([audioBuffer]), 'audio.mp3');
  formData.append('model', 'whisper-1');
  formData.append('response_format', 'verbose_json');
  formData.append('timestamp_granularities', 'word');
  
  const response = await axios.post(
    'https://api.openai.com/v1/audio/transcriptions',
    formData,
    {
      headers: {
        'Authorization': `Bearer ${openaiApiKey}`,
        'Content-Type': 'multipart/form-data'
      }
    }
  );
  
  return response.data;
}

async function detectChords(audioFilePath) {
  // Invoke chord detector Lambda
  const lambda = new AWS.Lambda();
  
  const response = await lambda.invoke({
    FunctionName: process.env.CHORD_DETECTOR_FUNCTION,
    Payload: JSON.stringify({ audioFilePath })
  }).promise();
  
  return JSON.parse(response.Payload);
}

async function saveResults(jobId, lyrics, chords) {
  const resultsKey = `results/${jobId}.json`;
  
  await s3.putObject({
    Bucket: BUCKET_NAME,
    Key: resultsKey,
    Body: JSON.stringify({ lyrics, chords }),
    ContentType: 'application/json'
  }).promise();
  
  return resultsKey;
}

async function updateJobStatus(jobId, status, data = {}) {
  const updateParams = {
    TableName: TABLE_NAME,
    Key: { id: jobId },
    UpdateExpression: 'SET #status = :status, updatedAt = :updatedAt',
    ExpressionAttributeNames: {
      '#status': 'status'
    },
    ExpressionAttributeValues: {
      ':status': status,
      ':updatedAt': Date.now()
    }
  };
  
  if (status === 'completed') {
    updateParams.UpdateExpression += ', lyrics = :lyrics, chords = :chords, completedAt = :completedAt';
    updateParams.ExpressionAttributeValues[':lyrics'] = data.lyrics;
    updateParams.ExpressionAttributeValues[':chords'] = data.chords;
    updateParams.ExpressionAttributeValues[':completedAt'] = Date.now();
  } else if (status === 'failed') {
    updateParams.UpdateExpression += ', errorMessage = :error';
    updateParams.ExpressionAttributeValues[':error'] = data.error;
  }
  
  await dynamodb.update(updateParams).promise();
}
```

### Add SQS Queue
Create `amplify/backend/function/transcribeWorker/transcribeWorker-cloudformation-template.json` and add SQS queue:
```json
{
  "AWSTemplateFormatVersion": "2010-09-09",
  "Resources": {
    "TranscriptionQueue": {
      "Type": "AWS::SQS::Queue",
      "Properties": {
        "QueueName": "transcription-queue",
        "VisibilityTimeout": 900,
        "MessageRetentionPeriod": 1209600,
        "ReceiveMessageWaitTimeSeconds": 20
      }
    },
    "TranscriptionQueuePolicy": {
      "Type": "AWS::SQS::QueuePolicy",
      "Properties": {
        "Queues": [{"Ref": "TranscriptionQueue"}],
        "PolicyDocument": {
          "Statement": [{
            "Effect": "Allow",
            "Principal": "*",
            "Action": "SQS:SendMessage",
            "Resource": {"Fn::GetAtt": ["TranscriptionQueue", "Arn"]}
          }]
        }
      }
    }
  },
  "Outputs": {
    "QueueUrl": {
      "Value": {"Ref": "TranscriptionQueue"}
    },
    "QueueArn": {
      "Value": {"Fn::GetAtt": ["TranscriptionQueue", "Arn"]}
    }
  }
}
```

### Configure Lambda Event Source Mapping
Add SQS trigger to worker Lambda in `amplify/backend/function/transcribeWorker/function-parameters.json`:
```json
{
  "eventSourceMappings": [
    {
      "eventSourceArn": "${TranscriptionQueue.Arn}",
      "batchSize": 1,
      "enabled": true
    }
  ]
}

### Store Secrets in AWS Secrets Manager
```bash
# Store OpenAI API key
aws secretsmanager create-secret \
  --name music-transcription/openai-key \
  --secret-string '{"OPENAI_API_KEY":"sk-your-key-here"}' \
  --region us-east-1

# Store YouTube API key
aws secretsmanager create-secret \
  --name music-transcription/youtube-key \
  --secret-string '{"YOUTUBE_API_KEY":"your-key-here"}' \
  --region us-east-1
```

---

## Step 5: Deploy Backend with Amplify

### Push Backend to AWS
```bash
# Deploy all backend resources
amplify push

# This will create:
# - DynamoDB tables
# - S3 buckets
# - Lambda functions
# - API Gateway endpoints
# - SQS queues
# - IAM roles and policies
```

### Configure Lambda Layers (for dependencies)
Create a Lambda layer for yt-dlp and ffmpeg:
```bash
# Create layer directory
mkdir -p layers/media-tools/bin

# Download yt-dlp
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o layers/media-tools/bin/yt-dlp
chmod +x layers/media-tools/bin/yt-dlp

# Download ffmpeg static build
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xf ffmpeg-release-amd64-static.tar.xz
cp ffmpeg-*-amd64-static/ffmpeg layers/media-tools/bin/
chmod +x layers/media-tools/bin/ffmpeg

# Create layer
cd layers/media-tools
zip -r ../media-tools-layer.zip .
cd ../..

# Publish layer
aws lambda publish-layer-version \
  --layer-name media-tools \
  --zip-file fileb://layers/media-tools-layer.zip \
  --compatible-runtimes nodejs18.x \
  --region us-east-1
```

### Update Lambda Function to Use Layer
Edit `amplify/backend/function/transcribeWorker/transcribeWorker-cloudformation-template.json`:
```json
{
  "LambdaFunction": {
    "Type": "AWS::Lambda::Function",
    "Properties": {
      "Layers": [
        "arn:aws:lambda:us-east-1:YOUR_ACCOUNT:layer:media-tools:1"
      ],
      "Environment": {
        "Variables": {
          "PATH": "/opt/bin:/usr/local/bin:/usr/bin:/bin"
        }
      }
    }
  }
}
```

---

## Step 6: Frontend Setup

### Create React Frontend
```bash
cd frontend

# Initialize React app
npx create-react-app .

# Install Amplify libraries
npm install aws-amplify @aws-amplify/ui-react axios

# Install additional dependencies
npm install react-dropzone react-query
```

### Configure Amplify in Frontend
Create `frontend/src/aws-exports.js` (auto-generated by Amplify):
```javascript
const awsmobile = {
  "aws_project_region": "us-east-1",
  "aws_cloud_logic_custom": [
    {
      "name": "transcriptionAPI",
      "endpoint": "https://your-api-id.execute-api.us-east-1.amazonaws.com/prod",
      "region": "us-east-1"
    }
  ],
  "aws_user_files_s3_bucket": "musictranscription-audio-prod",
  "aws_user_files_s3_bucket_region": "us-east-1"
};

export default awsmobile;
```

### Main App Component
Create `frontend/src/App.js`:
```javascript
import React, { useState } from 'react';
import { Amplify, API, Storage } from 'aws-amplify';
import awsconfig from './aws-exports';
import FileUpload from './components/FileUpload';
import YouTubeInput from './components/YouTubeInput';
import JobStatus from './components/JobStatus';
import './App.css';

Amplify.configure(awsconfig);

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [currentJobId, setCurrentJobId] = useState(null);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Music Transcription</h1>
        <p>Extract lyrics and chords from any song</p>
      </header>

      <div className="tabs">
        <button 
          className={activeTab === 'upload' ? 'active' : ''}
          onClick={() => setActiveTab('upload')}
        >
          Upload File
        </button>
        <button 
          className={activeTab === 'youtube' ? 'active' : ''}
          onClick={() => setActiveTab('youtube')}
        >
          YouTube Link
        </button>
      </div>

      <div className="content">
        {activeTab === 'upload' && (
          <FileUpload onJobCreated={setCurrentJobId} />
        )}
        {activeTab === 'youtube' && (
          <YouTubeInput onJobCreated={setCurrentJobId} />
        )}
        
        {currentJobId && (
          <JobStatus jobId={currentJobId} />
        )}
      </div>
    </div>
  );
}

export default App;
```

### File Upload Component
Create `frontend/src/components/FileUpload.js`:
```javascript
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { API, Storage } from 'aws-amplify';
import axios from 'axios';

function FileUpload({ onJobCreated }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setProgress(0);

    try {
      // Request upload URL from API
      const response = await API.post('transcriptionAPI', '/transcribe/upload', {
        body: {
          fileName: file.name,
          fileType: file.type,
          userId: 'guest' // Replace with actual user ID from Cognito
        }
      });

      const { jobId, uploadUrl } = response;

      // Upload file to S3 using presigned URL
      await axios.put(uploadUrl, file, {
        headers: {
          'Content-Type': file.type
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        }
      });

      onJobCreated(jobId);
      setUploading(false);
      
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed: ' + error.message);
      setUploading(false);
    }
  }, [onJobCreated]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: false
  });

  return (
    <div className="file-upload">
      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
        <input {...getInputProps()} />
        {uploading ? (
          <div className="upload-progress">
            <p>Uploading... {progress}%</p>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          </div>
        ) : (
          <div>
            <p>Drag & drop an audio file here, or click to select</p>
            <p className="file-types">Supported: MP3, WAV, M4A, FLAC, OGG (max 50MB)</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default FileUpload;
```

### YouTube Input Component
Create `frontend/src/components/YouTubeInput.js`:
```javascript
import React, { useState } from 'react';
import { API } from 'aws-amplify';

function YouTubeInput({ onJobCreated }) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!url) return;

    setLoading(true);

    try {
      const response = await API.post('transcriptionAPI', '/transcribe/youtube', {
        body: {
          youtubeUrl: url,
          userId: 'guest' // Replace with actual user ID from Cognito
        }
      });

      onJobCreated(response.jobId);
      setUrl('');
      
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to process YouTube link: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="youtube-input">
      <form onSubmit={handleSubmit}>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.youtube.com/watch?v=..."
          required
          disabled={loading}
        />
        <button type="submit" disabled={loading || !url}>
          {loading ? 'Processing...' : 'Transcribe'}
        </button>
      </form>
      <p className="hint">Paste a YouTube music video URL</p>
    </div>
  );
}

export default YouTubeInput;
```

### Job Status Component
Create `frontend/src/components/JobStatus.js`:
```javascript
import React, { useEffect, useState } from 'react';
import { API } from 'aws-amplify';

function JobStatus({ jobId }) {
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let interval;

    const fetchJobStatus = async () => {
      try {
        const response = await API.get('transcriptionAPI', `/transcribe/job/${jobId}`);
        setJob(response);
        setLoading(false);

        // Stop polling if job is completed or failed
        if (response.status === 'completed' || response.status === 'failed') {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Error fetching job status:', error);
        setLoading(false);
      }
    };

    fetchJobStatus();
    interval = setInterval(fetchJobStatus, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
  }, [jobId]);

  if (loading) {
    return <div className="job-status loading">Loading...</div>;
  }

  if (!job) {
    return <div className="job-status error">Job not found</div>;
  }

  return (
    <div className="job-status">
      <h2>Transcription Status</h2>
      
      <div className={`status-badge ${job.status}`}>
        {job.status.toUpperCase()}
      </div>

      {job.status === 'processing' && (
        <div className="processing">
          <div className="spinner"></div>
          <p>Processing your audio... This may take a few minutes.</p>
        </div>
      )}

      {job.status === 'completed' && (
        <div className="results">
          <div className="lyrics-section">
            <h3>Lyrics</h3>
            <div className="lyrics-content">
              {job.lyrics?.text || 'No lyrics detected'}
            </div>
          </div>

          <div className="chords-section">
            <h3>Chord Progression</h3>
            <div className="chords-content">
              {job.chords?.map((chord, idx) => (
                <div key={idx} className="chord-item">
                  <span className="chord-name">{chord.name}</span>
                  <span className="chord-time">{chord.timestamp}s</span>
                </div>
              )) || 'No chords detected'}
            </div>
          </div>

          <button className="download-btn">Download Results</button>
        </div>
      )}

      {job.status === 'failed' && (
        <div className="error">
          <p>Transcription failed: {job.errorMessage}</p>
          <button onClick={() => window.location.reload()}>Try Again</button>
        </div>
      )}
    </div>
  );
}

export default JobStatus;
```

---

## Step 7: Connect GitHub Repository to Amplify

### Connect Repository via AWS Console
```bash
# Option 1: Using AWS Console
1. Go to AWS Amplify Console
2. Click "New app" → "Host web app"
3. Select "GitHub" as source
4. Authorize AWS Amplify to access your GitHub account
5. Select repository: music-transcription-app
6. Select branch: main
7. Amplify will auto-detect build settings from amplify.yml
8. Review and click "Save and deploy"

# Option 2: Using Amplify CLI
amplify add hosting

# Configuration:
# ? Select the plugin module to execute: Hosting with Amplify Console
# ? Choose a type: Continuous deployment (Git-based deployments)

amplify publish
```

### Configure Build Settings in Amplify Console
The `amplify.yml` file will be automatically detected. Verify it contains:
```yaml
version: 1
backend:
  phases:
    build:
      commands:
        - '# Execute Amplify CLI with the helper script'
        - amplifyPush --simple
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: frontend/build
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
```

### Set Environment Variables in Amplify Console
1. Go to Amplify Console → Your App → Environment variables
2. Add the following:
```
AMPLIFY_MONOREPO_APP_ROOT=frontend
NODE_ENV=production
REACT_APP_API_ENDPOINT=auto-generated
```

---

## Step 8: Configure Custom Domain (Optional)

### Add Custom Domain
```bash
# Via Amplify Console:
1. Go to App settings → Domain management
2. Click "Add domain"
3. Enter your domain (e.g., musictranscription.com)
4. Amplify will provide DNS records
5. Add CNAME records to your DNS provider
6. Wait for SSL certificate provisioning (automatic)

# Via CLI:
amplify add hosting
# Select: Amazon CloudFront and S3
```

---

## Step 9: Set Up Monitoring and Alerts

### CloudWatch Dashboards
Create a custom dashboard in CloudWatch:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name MusicTranscription \
  --dashboard-body file://dashboard.json
```

Create `dashboard.json`:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
          [".", "Errors", {"stat": "Sum"}],
          [".", "Duration", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Lambda Metrics"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/SQS", "NumberOfMessagesSent"],
          [".", "NumberOfMessagesReceived"],
          [".", "ApproximateNumberOfMessagesVisible"]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "SQS Queue Metrics"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/DynamoDB", "ConsumedReadCapacityUnits"],
          [".", "ConsumedWriteCapacityUnits"]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "DynamoDB Metrics"
      }
    }
  ]
}
```

### CloudWatch Alarms
```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name transcribe-worker-errors \
  --alarm-description "Alert when Lambda errors exceed threshold" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:alerts

# Queue backlog alarm
aws cloudwatch put-metric-alarm \
  --alarm-name transcription-queue-backlog \
  --alarm-description "Alert when queue has too many messages" \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --statistic Average \
  --period 300 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:alerts
```

### Set Up SNS for Alerts
```bash
# Create SNS topic
aws sns create-topic --name music-transcription-alerts

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:music-transcription-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

---

## Step 10: CI/CD with GitHub Integration

### Automatic Deployments
Amplify automatically deploys when you push to GitHub:
```bash
# Make changes to your code
git add .
git commit -m "Update feature"
git push origin main

# Amplify will automatically:
# 1. Detect the push
# 2. Run backend build (amplify push)
# 3. Run frontend build (npm run build)
# 4. Deploy to production
# 5. Invalidate CloudFront cache
```

### Branch-Based Deployments
```bash
# Create staging branch
git checkout -b staging
git push origin staging

# In Amplify Console:
1. Go to App settings → General
2. Click "Connect branch"
3. Select "staging" branch
4. Each branch gets its own URL:
   - main: https://main.d1234.amplifyapp.com
   - staging: https://staging.d1234.amplifyapp.com
```

### Preview Deployments for Pull Requests
Enable PR previews in Amplify Console:
```
1. Go to App settings → Previews
2. Enable "Pull request previews"
3. Select branches to enable previews for
4. Each PR will get a unique preview URL
```

---

## Step 11: Security Configuration

### API Security with API Gateway
Configure API Gateway settings:
```bash
# Add API key requirement
amplify update api

# Enable throttling
# In API Gateway console:
1. Select your API
2. Go to Stages → prod
3. Settings → Default Method Throttling
4. Rate: 1000 requests per second
5. Burst: 2000 requests
```

### CORS Configuration
Update Lambda function to include proper CORS headers:
```javascript
const corsHeaders = {
  'Access-Control-Allow-Origin': process.env.ALLOWED_ORIGINS || '*',
  'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
  'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
};
```

### S3 Bucket Security
```bash
# Enable encryption
aws s3api put-bucket-encryption \
  --bucket musictranscription-audio-prod \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket musictranscription-audio-prod \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket musictranscription-audio-prod \
  --versioning-configuration Status=Enabled

# Lifecycle policy to delete old files
aws s3api put-bucket-lifecycle-configuration \
  --bucket musictranscription-audio-prod \
  --lifecycle-configuration file://lifecycle.json
```

Create `lifecycle.json`:
```json
{
  "Rules": [
    {
      "Id": "DeleteOldUploads",
      "Status": "Enabled",
      "Prefix": "uploads/",
      "Expiration": {
        "Days": 30
      }
    },
    {
      "Id": "DeleteOldResults",
      "Status": "Enabled",
      "Prefix": "results/",
      "Expiration": {
        "Days": 90
      }
    }
  ]
}
```

---

## Docker Configuration (Optional - For Local Development)

If you want to test locally before deploying to AWS:

#### Backend Dockerfile
```dockerfile
FROM public.ecr.aws/lambda/nodejs:18

# Copy function code
COPY package*.json ./
RUN npm ci --production

COPY *.js ./

CMD [ "index.handler" ]
```

---

## Cost Optimization

### Estimated Monthly Costs (AWS)
```
Amplify Hosting:
- Build minutes: $0.01/minute × 100 builds = $1
- Hosting: $0.15/GB stored + $0.15/GB served = $5-20
- Total: ~$6-21/month

Lambda:
- API requests: 1M requests × $0.20/1M = $0.20
- Worker compute: 10,000 jobs × 2 min × $0.0000166667/GB-sec = $20
- Total: ~$20-50/month

DynamoDB:
- On-demand pricing: $1.25/million writes, $0.25/million reads
- 100K jobs/month: ~$5/month

S3:
- Storage: 100GB × $0.023/GB = $2.30
- Requests: $0.005/1000 PUT, $0.0004/1000 GET = $1
- Total: ~$3-5/month

SQS:
- First 1M requests free
- Additional: $0.40/million = ~$1/month

API Gateway:
- First 1M requests: $3.50
- Additional: $1.00/million = ~$4/month

Secrets Manager:
- $0.40/secret/month × 2 = $0.80/month

CloudWatch:
- Logs: 5GB × $0.50/GB = $2.50
- Metrics: $0.30/metric × 10 = $3
- Total: ~$5-6/month

Data Transfer:
- First 100GB free
- Additional: $0.09/GB = ~$5-20/month

OpenAI Whisper API:
- $0.006/minute of audio
- 10,000 songs × 4 min avg = $240/month

TOTAL ESTIMATED: $290-375/month
(Scales with usage)
```

---

## Environment Configuration

### Production Environment Variables (AWS Amplify)
Configure in Amplify Console → App Settings → Environment variables:
```bash
# Application
NODE_ENV=production
REACT_APP_API_NAME=transcriptionAPI

# AWS (auto-configured by Amplify)
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id

# External APIs (store in Secrets Manager, reference in Lambda)
OPENAI_API_KEY=stored-in-secrets-manager
YOUTUBE_API_KEY=stored-in-secrets-manager

# Limits
MAX_FILE_SIZE_MB=50
MAX_DURATION_MINUTES=15
RATE_LIMIT_PER_HOUR=100
```

---

## Monitoring & Observability

### Metrics to Track (CloudWatch)
```
Application Metrics:
- Lambda invocations (API and Worker)
- Lambda errors and throttles
- Lambda duration (p50, p95, p99)
- API Gateway request count
- API Gateway 4xx/5xx errors
- API Gateway latency
- SQS queue depth
- SQS message age
- DynamoDB read/write capacity
- DynamoDB throttled requests
- S3 storage size
- S3 request count

Business Metrics (Custom):
- Transcriptions per day
- Success/failure rate
- Average processing time
- File vs YouTube ratio
- User activity
```

### CloudWatch Logs Insights Queries
```sql
-- Find failed transcriptions
fields @timestamp, jobId, errorMessage
| filter status = "failed"
| sort @timestamp desc
| limit 100

-- Average processing time
fields @timestamp, duration
| filter status = "completed"
| stats avg(duration) as avg_duration by bin(5m)

-- Error rate by error type
fields @timestamp, errorMessage
| filter @message like /ERROR/
| stats count() by errorMessage
| sort count desc

-- Lambda cold starts
fields @timestamp, @duration, @initDuration
| filter @type = "REPORT"
| stats count(@initDuration > 0) as coldStarts, count() as totalInvocations
```

### CloudWatch Alarms
```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name transcribe-worker-errors \
  --alarm-description "Alert when Lambda errors exceed threshold" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:alerts

# Queue backlog alarm
aws cloudwatch put-metric-alarm \
  --alarm-name transcription-queue-backlog \
  --alarm-description "Alert when queue has too many messages" \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --statistic Average \
  --period 300 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:alerts

# Lambda duration alarm
aws cloudwatch put-metric-alarm \
  --alarm-name transcribe-worker-slow \
  --alarm-description "Alert when Lambda duration is high" \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 600000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:alerts
```

---

## Scaling Strategy

### AWS Serverless Auto-Scaling
```
Lambda:
- Concurrent executions: 1000 (default account limit)
- Can request increase to 10,000+
- Auto-scales based on incoming requests
- Reserved concurrency to control costs

DynamoDB:
- On-demand mode: Auto-scales to handle traffic
- No capacity planning needed
- Pay per request
- Or use provisioned mode with auto-scaling

S3:
- Unlimited storage
- Unlimited requests
- Auto-scales automatically

SQS:
- Unlimited throughput
- Auto-scales with Lambda polling
- Configure batch size and concurrency

API Gateway:
- 10,000 requests/second default
- Can request increase
- Throttling per API key/user
```

### Manual Scaling Adjustments
```bash
# Increase Lambda reserved concurrency
aws lambda put-function-concurrency \
  --function-name transcribeWorker \
  --reserved-concurrent-executions 100

# Request service quota increase
aws service-quotas request-service-quota-increase \
  --service-code lambda \
  --quota-code L-B99A9384 \
  --desired-value 5000

# Configure SQS Lambda trigger
aws lambda update-event-source-mapping \
  --uuid EVENT_SOURCE_UUID \
  --batch-size 10 \
  --maximum-batching-window-in-seconds 5
```

---

## Backup & Disaster Recovery

### DynamoDB Backup Strategy
```bash
# Enable point-in-time recovery
aws dynamodb update-continuous-backups \
  --table-name TranscriptionJobs \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# Create on-demand backup
aws dynamodb create-backup \
  --table-name TranscriptionJobs \
  --backup-name TranscriptionJobs-$(date +%Y%m%d)

# Restore from backup
aws dynamodb restore-table-from-backup \
  --target-table-name TranscriptionJobs-restored \
  --backup-arn arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/TranscriptionJobs/backup/BACKUP_NAME
```

### S3 Backup Strategy
```bash
# Enable versioning
aws s3api put-bucket-versioning \
  --bucket musictranscription-audio-prod \
  --versioning-configuration Status=Enabled

# Cross-region replication
aws s3api put-bucket-replication \
  --bucket musictranscription-audio-prod \
  --replication-configuration file://replication.json

# Lifecycle policy for old versions
aws s3api put-bucket-lifecycle-configuration \
  --bucket musictranscription-audio-prod \
  --lifecycle-configuration file://lifecycle-backup.json
```

### Disaster Recovery Plan
```
RTO (Recovery Time Objective): 2 hours
RPO (Recovery Point Objective): 5 minutes

Recovery Steps:
1. Identify failure scope (check CloudWatch, AWS Health Dashboard)
2. If Lambda failure: Redeploy from GitHub (amplify publish)
3. If DynamoDB failure: Restore from point-in-time backup
4. If S3 failure: Failover to replica bucket
5. If regional outage: Deploy to backup region using Amplify
6. Update DNS if needed (Route 53)
7. Verify all services operational
8. Monitor for 1 hour post-recovery

Testing Schedule:
- Monthly: Test backup restoration
- Quarterly: Full DR drill with region failover
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing locally
- [ ] Environment variables configured in Secrets Manager
- [ ] IAM roles and policies reviewed
- [ ] S3 bucket policies configured
- [ ] DynamoDB tables created with proper indexes
- [ ] Lambda functions tested locally
- [ ] API Gateway endpoints tested
- [ ] Frontend builds successfully
- [ ] GitHub repository connected to Amplify
- [ ] Custom domain configured (if applicable)
- [ ] Monitoring and alerts configured
- [ ] Backup strategy implemented

### Deployment Steps
1. Push code to GitHub main branch
```bash
git add .
git commit -m "Production deployment"
git push origin main
```

2. Monitor Amplify Console for build progress
3. Check CloudWatch Logs for any errors
4. Test API endpoints
5. Test frontend functionality
6. Verify file upload to S3
7. Verify YouTube link processing
8. Check DynamoDB for job records
9. Monitor SQS queue
10. Verify transcription results

### Post-Deployment
- [ ] All services healthy in AWS Console
- [ ] API responding correctly
- [ ] Frontend accessible
- [ ] File uploads working
- [ ] YouTube processing working
- [ ] Transcription jobs completing
- [ ] No errors in CloudWatch Logs
- [ ] Metrics showing in CloudWatch
- [ ] Alerts configured and working
- [ ] Cost tracking enabled
- [ ] Documentation updated

### Rollback Procedure
```bash
# Rollback frontend via Amplify Console
1. Go to Amplify Console → Your App
2. Click on the previous successful deployment
3. Click "Redeploy this version"

# Rollback backend
amplify env checkout prod
git revert HEAD
git push origin main

# Or restore from backup
aws dynamodb restore-table-from-backup \
  --target-table-name TranscriptionJobs \
  --backup-arn arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/TranscriptionJobs/backup/BACKUP_NAME
```

---

## Maintenance & Operations

### Regular Maintenance Tasks
```
Daily:
- Check CloudWatch dashboard
- Review error logs
- Monitor costs in AWS Cost Explorer
- Check SQS queue depth

Weekly:
- Review Lambda performance metrics
- Check DynamoDB capacity usage
- Review S3 storage growth
- Update dependencies (npm audit fix)
- Review and respond to CloudWatch alarms

Monthly:
- Review and optimize Lambda memory settings
- Analyze cost trends
- Update Lambda layers (yt-dlp, ffmpeg)
- Review IAM policies
- Test disaster recovery procedures
- Review and archive old logs

Quarterly:
- Major dependency updates
- Security audit
- Load testing
- Full DR drill
- Architecture review
```

### Troubleshooting Guide
```
Issue: Lambda timeout
- Increase timeout in function configuration
- Increase memory allocation (more CPU)
- Optimize code (parallel processing)
- Check external API response times

Issue: SQS queue backing up
- Increase Lambda concurrency
- Add more worker instances
- Check for failing jobs
- Verify OpenAI API availability

Issue: High costs
- Review CloudWatch Logs retention
- Check S3 storage usage (lifecycle policies)
- Review Lambda execution times
- Optimize DynamoDB capacity
- Check data transfer costs

Issue: Failed transcriptions
- Check CloudWatch Logs for errors
- Verify OpenAI API key in Secrets Manager
- Check Lambda layer (yt-dlp, ffmpeg)
- Verify S3 permissions
- Check audio file format compatibility
```

### Useful Commands
```bash
# View Amplify app status
amplify status

# View CloudWatch logs
aws logs tail /aws/lambda/transcribeWorker --follow

# Check SQS queue depth
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/transcription-queue \
  --attribute-names ApproximateNumberOfMessages

# List recent DynamoDB items
aws dynamodb scan \
  --table-name TranscriptionJobs \
  --limit 10

# Check S3 bucket size
aws s3 ls s3://musictranscription-audio-prod --recursive --summarize

# View Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=transcribeWorker \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

---

## Security Best Practices

### Checklist
- [ ] All API endpoints use HTTPS only
- [ ] API Gateway has throttling enabled
- [ ] Lambda functions use least-privilege IAM roles
- [ ] S3 buckets have encryption enabled
- [ ] S3 buckets block public access
- [ ] Secrets stored in AWS Secrets Manager
- [ ] CloudWatch Logs encrypted
- [ ] DynamoDB encryption at rest enabled
- [ ] AWS WAF configured for API Gateway (optional)
- [ ] VPC endpoints for private communication (optional)
- [ ] CloudTrail enabled for audit logging
- [ ] AWS Config for compliance monitoring
- [ ] Regular security audits scheduled

---

## Additional Resources

### AWS Documentation
- [AWS Amplify Documentation](https://docs.amplify.aws/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [S3 Security Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)

### External APIs
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)

### Support
- AWS Support: https://console.aws.amazon.com/support
- Amplify Discord: https://discord.gg/amplify
- GitHub Issues: Your repository issues page

---

**Document Version**: 2.0 (AWS Amplify + GitHub)  
**Last Updated**: January 2026  
**Platform**: AWS Amplify, Lambda, DynamoDB, S3, API Gateway  
**Deployment**: GitHub → AWS Amplify CI/CD
