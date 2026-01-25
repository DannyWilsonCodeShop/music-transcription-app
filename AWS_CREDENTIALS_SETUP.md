# AWS Credentials Setup for ChordScout Frontend

## Configuration Complete

### Cognito Identity Pool
- **Identity Pool ID**: `us-east-1:781b986b-cc62-418d-8b14-70292d1f773e`
- **Name**: ChordScout-Frontend-dev
- **Unauthenticated Access**: Enabled
- **Account**: 090130568474

### IAM Role
- **Role Name**: ChordScout-Cognito-Unauth-dev
- **Role ARN**: `arn:aws:iam::090130568474:role/ChordScout-Cognito-Unauth-dev`
- **Purpose**: Allows unauthenticated users to access Step Functions and DynamoDB

### Permissions Granted
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution",
        "states:DescribeExecution",
        "states:ListExecutions"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": "*"
    }
  ]
}
```

**Note**: Using wildcard (*) for resources temporarily for testing. Should be restricted to specific resources in production.

## How It Works

1. **Frontend loads** → Cognito Identity Pool provides temporary AWS credentials
2. **User submits YouTube URL** → Frontend uses credentials to call Step Functions
3. **Step Functions starts** → Backend processes the transcription
4. **Frontend polls DynamoDB** → Gets job status updates every 5 seconds
5. **Job completes** → Frontend displays results

## Troubleshooting

### If you get "AccessDeniedException"
- Wait 1-2 minutes for IAM policy changes to propagate
- Check browser console for detailed error logs
- Verify the Identity Pool ID in `src/services/transcriptionService.ts` matches: `us-east-1:781b986b-cc62-418d-8b14-70292d1f773e`

### If credentials don't work
- Clear browser cache and reload
- Check that the Cognito Identity Pool role is attached:
  ```bash
  aws cognito-identity get-identity-pool-roles \
    --identity-pool-id us-east-1:781b986b-cc62-418d-8b14-70292d1f773e \
    --profile chordscout
  ```

### Verify permissions
```bash
aws iam get-role-policy \
  --role-name ChordScout-Cognito-Unauth-dev \
  --policy-name ChordScout-Frontend-Permissions \
  --profile chordscout
```

## Security Considerations

### Current Setup (Development)
- ✅ No IAM credentials exposed in frontend code
- ✅ Temporary credentials generated per session
- ⚠️ Wildcard permissions (should be restricted)
- ⚠️ No user authentication (anyone can use the app)

### Production Recommendations
1. **Restrict Resource ARNs** - Replace `*` with specific ARNs
2. **Add Rate Limiting** - Prevent abuse of the API
3. **Add User Authentication** - Use Cognito User Pools
4. **Add Cost Monitoring** - Set up billing alerts
5. **Add Request Validation** - Validate YouTube URLs server-side
6. **Add CORS Configuration** - Restrict to your domain only

## Testing

After deployment completes, test the transcription feature:
1. Go to https://main.dqg97bbmmprz.amplifyapp.com
2. Enter a YouTube URL (e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ)
3. Click "Start Transcription"
4. Watch the progress indicator
5. Check browser console for detailed logs

## Files Modified
- `src/services/transcriptionService.ts` - Added Cognito credentials
- `cognito-permissions-policy.json` - IAM policy document
- `trust-policy.json` - Cognito trust relationship

## AWS Resources Created
- Cognito Identity Pool: `us-east-1:781b986b-cc62-418d-8b14-70292d1f773e`
- IAM Role: `ChordScout-Cognito-Unauth-dev`
- IAM Policy: `ChordScout-Frontend-Permissions` (inline)

## Next Steps
1. Wait for Amplify deployment to complete
2. Test transcription feature
3. If it works, restrict IAM permissions to specific resources
4. Add user authentication with Cognito User Pools
5. Add error handling and retry logic
6. Add cost monitoring and alerts
