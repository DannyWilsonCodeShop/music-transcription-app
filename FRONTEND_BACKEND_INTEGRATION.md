# Frontend-Backend Integration Guide

This guide explains how the ChordScout dashboard connects to the backend transcription pipeline.

## Architecture Overview

```
User Upload → DynamoDB → DynamoDB Stream → Lambda Trigger → Step Functions → Processing
     ↓                                                              ↓
  Frontend ←─────────── Polling (every 5s) ←──────────────── DynamoDB Updates
```

## Components

### 1. Upload Interface (`src/components/UploadInterface.tsx`)
- Handles YouTube URL and audio file uploads
- Uploads files to S3 using Amplify Storage
- Creates job records in DynamoDB with status='pending'
- Returns jobId to parent component

### 2. Transcription Progress (`src/components/TranscriptionProgress.tsx`)
- Polls DynamoDB every 5 seconds for job status updates
- Displays progress bar and processing steps
- Notifies parent when job completes
- Shows error states if transcription fails

### 3. Main Dashboard (`src/App-test.tsx`)
- Manages active and completed jobs
- Displays upload interface
- Shows real-time progress for active jobs
- Lists completed transcriptions with sheet music viewer

### 4. Job Trigger Lambda (`amplify/functions/job-trigger/`)
- Watches DynamoDB Stream for new jobs
- Automatically starts Step Functions execution when job status='pending'
- Passes job details to transcription pipeline

## Data Flow

### Upload Flow (YouTube)
1. User enters YouTube URL in UploadInterface
2. Component creates DynamoDB record:
   ```json
   {
     "id": "job-1234567890-abc123",
     "status": "pending",
     "youtubeUrl": "https://youtube.com/watch?v=...",
     "title": "Song Title",
     "artist": "Artist Name",
     "createdAt": "2024-01-24T12:00:00Z"
   }
   ```
3. DynamoDB Stream triggers job-trigger Lambda
4. Lambda starts Step Functions execution
5. Frontend polls for status updates

### Upload Flow (Audio File)
1. User selects audio file in UploadInterface
2. Component uploads file to S3 using Amplify Storage
3. Component creates DynamoDB record with audioUrl
4. Same flow as YouTube from step 3 onwards

### Processing Flow
1. Step Functions downloads audio (from YouTube or S3)
2. Parallel processing:
   - Whisper API transcribes lyrics
   - Basic Pitch ML detects chords
3. Results combined and stored in DynamoDB
4. Job status updated to 'completed'
5. Frontend detects completion and displays results

## DynamoDB Schema

```typescript
TranscriptionJob {
  id: string              // Primary key: "job-{timestamp}-{random}"
  status: enum            // 'pending' | 'processing' | 'completed' | 'failed'
  audioUrl?: string       // S3 path for uploaded files
  youtubeUrl?: string     // YouTube URL if provided
  title: string           // Song title
  artist: string          // Artist name
  lyrics?: string         // Transcribed lyrics (populated on completion)
  chords?: json           // Chord data with timestamps (populated on completion)
  createdAt: datetime     // Job creation timestamp
  updatedAt: datetime     // Last update timestamp
  userId?: string         // User ID (for multi-user support)
}
```

## Chord Data Format

```typescript
{
  key: string,              // e.g., "C", "Am", "F#"
  mode: string,             // "major" or "minor"
  chords: [
    {
      name: string,         // e.g., "C", "Am7", "Gsus4"
      timestamp: number,    // Start time in seconds
      duration: number,     // Duration in seconds
      confidence: number    // 0.0 to 1.0
    }
  ],
  chordProgressionText: string  // Human-readable format
}
```

## Setup Instructions

### 1. Deploy Backend Infrastructure
```bash
# Deploy Step Functions and Lambda functions
./deploy-full-pipeline.sh

# Note the State Machine ARN from output
```

### 2. Configure Environment Variables
Add to `amplify/functions/job-trigger/resource.ts`:
```typescript
environment: {
  STATE_MACHINE_ARN: 'arn:aws:states:us-east-1:ACCOUNT:stateMachine:TranscriptionWorkflow'
}
```

### 3. Enable DynamoDB Streams
The Amplify backend automatically enables streams on the TranscriptionJob table and connects the job-trigger Lambda.

### 4. Deploy Amplify Backend
```bash
npx ampx sandbox
# or for production:
git push origin main  # Triggers Amplify deployment
```

### 5. Test the Integration
```bash
# Start frontend dev server
npm run dev

# Upload a test file or YouTube URL
# Monitor browser console for API calls
# Check DynamoDB for job records
# Verify Step Functions execution in AWS Console
```

## Monitoring & Debugging

### Frontend Debugging
```javascript
// In browser console:
// Check Amplify configuration
console.log(Amplify.getConfig());

// Monitor job polling
// Open Network tab and filter for GraphQL requests
```

### Backend Debugging
```bash
# Check DynamoDB for jobs
aws dynamodb scan --table-name TranscriptionJob-dev

# Check Step Functions executions
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:ACCOUNT:stateMachine:TranscriptionWorkflow

# View Lambda logs
aws logs tail /aws/lambda/job-trigger --follow
```

### Common Issues

**Issue: Jobs stuck in 'pending' status**
- Check if DynamoDB Streams are enabled
- Verify job-trigger Lambda has correct STATE_MACHINE_ARN
- Check Lambda logs for errors

**Issue: "Failed to fetch job status"**
- Verify Amplify is configured correctly
- Check browser console for CORS errors
- Ensure user has permissions to read from DynamoDB

**Issue: Upload fails**
- Check S3 bucket permissions
- Verify Amplify Storage is configured
- Check file size (max 50MB)

**Issue: YouTube downloads fail**
- Verify yt-dlp is installed in Lambda layer
- Check YouTube URL format
- Ensure Lambda has internet access (NAT Gateway if in VPC)

## Cost Optimization

### Polling Strategy
Current: Poll every 5 seconds
- Cost: ~$0.01 per 1000 jobs (DynamoDB reads)
- Latency: 0-5 seconds to detect completion

Alternative: WebSocket with AppSync
- Cost: ~$0.08 per 1000 jobs (AppSync subscriptions)
- Latency: Real-time updates
- Implementation: Requires AppSync setup

### Recommendation
Keep polling for MVP, switch to WebSocket for production with high traffic.

## Security Considerations

1. **Authentication**: Currently using Amplify guest access
   - Production: Require user authentication
   - Add user-based access controls

2. **File Upload Validation**
   - Frontend validates file type and size
   - Backend should re-validate
   - Scan for malware in production

3. **Rate Limiting**
   - Add per-user rate limits
   - Prevent abuse of YouTube downloads
   - Implement job queue limits

4. **API Keys**
   - Store in AWS Secrets Manager
   - Rotate regularly
   - Monitor usage

## Next Steps

1. **Add Real-time Updates**: Implement WebSocket subscriptions
2. **User Authentication**: Require login for uploads
3. **Job History**: Add pagination for completed jobs
4. **Error Handling**: Improve error messages and retry logic
5. **Analytics**: Track success rates and processing times
6. **Notifications**: Email/SMS when transcription completes
7. **Sharing**: Allow users to share transcriptions
8. **Export**: Add PDF export for sheet music

## Support

For issues or questions:
- Check CloudWatch logs for backend errors
- Review browser console for frontend errors
- Consult AWS documentation for service-specific issues
- See DEPLOYMENT_TROUBLESHOOTING.md for common problems
