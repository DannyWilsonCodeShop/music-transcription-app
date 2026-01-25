# ChordScout - Immediate Action Plan

## Goal: Get First Transcription Working Today

---

## Step 1: Deploy Full Backend (After Docker Build) ⏳

**Wait for**: GitHub Actions to finish (~10 min)

**Then run**:
```bash
export AWS_PROFILE=chordscout

aws cloudformation deploy \
  --template-file backend/infrastructure/cloudformation-template.yaml \
  --stack-name ChordScout-Pipeline-dev \
  --parameter-overrides \
    Environment=dev \
    OpenAISecretArn=arn:aws:secretsmanager:us-east-1:090130568474:secret:ChordScout-OpenAI-dev-lH3RGP \
    ChordDetectorImageUri=090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

**Time**: 5-10 minutes

---

## Step 2: Wire Up Frontend to Backend 🔌

### A. Add AWS SDK to Frontend

```bash
npm install @aws-sdk/client-sfn @aws-sdk/client-dynamodb
```

### B. Create API Service

Create `src/services/transcriptionService.ts`:

```typescript
import { SFNClient, StartExecutionCommand } from '@aws-sdk/client-sfn';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand } from '@aws-sdk/lib-dynamodb';

const sfnClient = new SFNClient({ region: 'us-east-1' });
const dynamoClient = DynamoDBDocumentClient.from(new DynamoDBClient({ region: 'us-east-1' }));

export async function startTranscription(youtubeUrl: string, title: string) {
  const jobId = `job-${Date.now()}`;
  
  const command = new StartExecutionCommand({
    stateMachineArn: 'arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-Transcription-dev',
    name: jobId,
    input: JSON.stringify({
      jobId,
      youtubeUrl,
      title
    })
  });
  
  await sfnClient.send(command);
  return jobId;
}

export async function getJobStatus(jobId: string) {
  const command = new GetCommand({
    TableName: 'ChordScout-TranscriptionJobs-dev',
    Key: { id: jobId }
  });
  
  const response = await dynamoClient.send(command);
  return response.Item;
}
```

### C. Update UploadInterface Component

Add the API calls to trigger transcription.

**Time**: 30-45 minutes

---

## Step 3: Test First Transcription 🧪

1. Run frontend locally: `npm run dev`
2. Enter YouTube URL: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
3. Click "Transcribe"
4. Watch CloudWatch logs
5. Verify results appear

**Time**: 15-30 minutes

---

## Step 4: Deploy Frontend 🚀

```bash
git add .
git commit -m "Connect frontend to backend API"
git push origin main
```

Amplify will auto-deploy in ~6 minutes.

**Time**: 10 minutes

---

## Total Time: 2-3 hours

---

## What You'll Have

After completing these steps:
- ✅ Full backend pipeline deployed
- ✅ Frontend connected to backend
- ✅ Working transcription feature
- ✅ Live app on Amplify

---

## Troubleshooting

### If Step Functions fails:
- Check CloudWatch logs
- Verify IAM permissions
- Check input format

### If Frontend can't connect:
- Verify AWS credentials configured
- Check CORS settings
- Verify API endpoints

### If Transcription hangs:
- Check Lambda timeouts
- Verify OpenAI API key
- Check S3 permissions

---

## After This Works

Then you can add:
- Better UI/UX
- Error handling
- Progress indicators
- Download features
- User accounts
- Saved transcriptions

---

## Ready?

Let me know when GitHub Actions finishes, and I'll help you deploy the full stack! 🚀
