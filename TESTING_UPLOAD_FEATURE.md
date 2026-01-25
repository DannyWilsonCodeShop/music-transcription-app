# Testing the Upload & Progress Monitoring Feature

This guide helps you test the new upload interface and progress monitoring features.

## What's New

### 1. Upload Interface
- **YouTube Tab**: Paste YouTube URLs to transcribe music videos
- **Audio File Tab**: Upload MP3, WAV, M4A, FLAC, OGG, or AAC files
- **Metadata Fields**: Optional title and artist fields
- **Drag & Drop**: Drag audio files directly onto the upload area

### 2. Progress Monitoring
- **Real-time Status**: See job status (pending → processing → completed)
- **Progress Bar**: Visual indicator of transcription progress
- **Processing Steps**: Shows which steps are complete
- **Auto-refresh**: Polls every 5 seconds for updates

### 3. Transcription List
- **Completed Jobs**: View all finished transcriptions
- **Sheet Music**: Click any transcription to view sheet music
- **Job Details**: See creation date, time, and job ID

## Quick Test (Frontend Only)

### 1. Start Development Server
```bash
npm run dev
```

### 2. Open Browser
Navigate to `http://localhost:5173`

### 3. Test Upload Interface
- Click between "YouTube Link" and "Audio File" tabs
- Enter a YouTube URL (validation will show if invalid)
- Try dragging a file onto the upload area
- Fill in optional title/artist fields

### 4. View Demo Sheet Music
Click the "🎼 View Demo Sheet Music" button to see the sheet music viewer with sample chord data.

## Full Integration Test (With Backend)

### Prerequisites
1. AWS account configured
2. Amplify backend deployed
3. Step Functions state machine deployed
4. DynamoDB table created

### 1. Deploy Backend
```bash
# Deploy the full pipeline
./deploy-full-pipeline.sh

# Deploy Amplify backend
npx ampx sandbox
```

### 2. Configure Environment
Ensure `amplify_outputs.json` has correct values:
```json
{
  "storage": {
    "bucket_name": "your-actual-bucket-name"
  },
  "data": {
    "url": "your-actual-graphql-endpoint"
  }
}
```

### 3. Test YouTube Upload
1. Open the app in browser
2. Click "YouTube Link" tab
3. Enter a valid YouTube URL (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
4. Add title: "Test Song"
5. Add artist: "Test Artist"
6. Click "Start Transcription"
7. Watch the progress indicator appear
8. Wait 2-5 minutes for completion

### 4. Test File Upload
1. Click "Audio File" tab
2. Drag an MP3 file onto the upload area (or click to browse)
3. Verify file name and size appear
4. Click "Upload & Transcribe"
5. Watch upload progress
6. Monitor transcription progress

### 5. Verify in AWS Console

#### Check DynamoDB
```bash
aws dynamodb scan --table-name TranscriptionJob-dev
```

Expected output:
```json
{
  "Items": [
    {
      "id": { "S": "job-1234567890-abc123" },
      "status": { "S": "pending" },
      "title": { "S": "Test Song" },
      "youtubeUrl": { "S": "https://youtube.com/..." }
    }
  ]
}
```

#### Check Step Functions
```bash
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:REGION:ACCOUNT:stateMachine:TranscriptionWorkflow \
  --max-results 5
```

#### Check Lambda Logs
```bash
# Job trigger logs
aws logs tail /aws/lambda/job-trigger --follow

# Transcribe function logs
aws logs tail /aws/lambda/transcribe-audio --follow
```

## Testing Scenarios

### Scenario 1: Happy Path (YouTube)
1. Upload valid YouTube URL
2. Status changes: pending → processing → completed
3. Transcription appears in list
4. Click to view sheet music
5. Sheet music displays correctly

### Scenario 2: Happy Path (File)
1. Upload valid audio file
2. File uploads to S3
3. Status changes as expected
4. Results appear in list

### Scenario 3: Invalid YouTube URL
1. Enter invalid URL (e.g., "not-a-url")
2. Validation error appears
3. Submit button disabled
4. No job created

### Scenario 4: Large File
1. Try uploading file > 50MB
2. Error message appears
3. Upload prevented

### Scenario 5: Multiple Jobs
1. Upload 3 different songs
2. All appear in progress section
3. Each updates independently
4. Completed jobs move to transcription list

### Scenario 6: Failed Job
1. Upload invalid audio file
2. Job starts processing
3. Status changes to 'failed'
4. Error message displayed

## Expected Behavior

### Upload Interface
- ✅ Tabs switch smoothly
- ✅ Form validation works
- ✅ File drag & drop works
- ✅ Upload button disabled when invalid
- ✅ Loading spinner during upload
- ✅ Form resets after successful upload

### Progress Monitoring
- ✅ Job appears immediately after upload
- ✅ Status updates every 5 seconds
- ✅ Progress bar animates
- ✅ Processing steps show checkmarks
- ✅ Completed jobs move to list
- ✅ Failed jobs show error

### Transcription List
- ✅ Shows all completed jobs
- ✅ Newest jobs appear first
- ✅ Click to view sheet music
- ✅ Sheet music modal opens
- ✅ Can close modal

## Troubleshooting

### Upload Button Doesn't Work
- Check browser console for errors
- Verify Amplify is configured
- Check network tab for failed requests

### Progress Stuck at "Pending"
- Check DynamoDB Streams are enabled
- Verify job-trigger Lambda is deployed
- Check Lambda logs for errors

### No Jobs Appear
- Check DynamoDB table exists
- Verify GraphQL endpoint is correct
- Check browser console for API errors

### Sheet Music Doesn't Display
- Verify chord data format is correct
- Check abcjs library is loaded
- Look for JavaScript errors

## Performance Metrics

### Expected Timings
- File upload: 5-30 seconds (depends on file size)
- YouTube download: 10-60 seconds
- Lyrics transcription: 30-120 seconds
- Chord detection: 30-90 seconds
- Total: 2-5 minutes average

### Cost Per Transcription
- S3 storage: $0.001
- DynamoDB: $0.002
- Lambda execution: $0.01
- Whisper API: $0.006 per minute
- Step Functions: $0.025 per 1000 transitions
- **Total: ~$0.08-0.12 per song**

## Next Steps

After successful testing:
1. ✅ Upload interface works
2. ✅ Progress monitoring works
3. ✅ Jobs complete successfully
4. ✅ Sheet music displays

Ready for:
- User authentication
- Production deployment
- Additional features (sharing, export, etc.)

## Demo Mode

If backend isn't deployed yet, the app works in demo mode:
- Upload interface is visible
- Jobs are created in DynamoDB (if configured)
- Demo sheet music button shows functionality
- Real processing requires backend deployment

## Support

Issues? Check:
1. Browser console for frontend errors
2. CloudWatch logs for backend errors
3. DynamoDB for job records
4. Step Functions for execution status
5. FRONTEND_BACKEND_INTEGRATION.md for architecture details
