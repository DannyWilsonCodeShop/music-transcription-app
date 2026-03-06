# Genius API Setup Guide

## Overview

This guide walks you through setting up the Genius API token for ChordScout v3.0's lyrics feature.

## Test Results

The test script `test-genius-simple.sh` has confirmed:
- ✗ GENIUS_ACCESS_TOKEN not found in environment
- ✗ Secret 'chordscout/genius-api-token' does not exist in AWS Secrets Manager
- ✗ API connection cannot be tested without token

## Step 1: Get a Genius API Token

1. Go to https://genius.com/api-clients
2. Sign in or create a free account
3. Click "New API Client"
4. Fill in the form:
   - **App Name**: ChordScout
   - **App Website URL**: https://main.dqg97bbmmprz.amplifyapp.com (or your domain)
   - **Redirect URI**: http://localhost (not used for our use case)
5. Click "Save"
6. After saving, you'll see three values:
   - **Client ID** - NOT what we need
   - **Client Secret** - NOT what we need
   - **Client Access Token** - THIS IS WHAT YOU NEED!
7. Look for "Generate Access Token" button or scroll down to find the **Client Access Token**
8. Copy the "Client Access Token" (this is your GENIUS_ACCESS_TOKEN)

**IMPORTANT**: You need the **Client Access Token**, NOT the Client ID or Client Secret. The access token is typically a longer string that starts with random characters.

### Where to Find the Client Access Token

After creating your API client, scroll down on the API client page. You should see:

```
Client ID: [some-id]
Client Secret: [some-secret]

Generate Access Token
[Button or link to generate]

OR

Client Access Token: [long-string-of-characters]
```

If you don't see a "Client Access Token" yet, you may need to:
- Click "Generate Access Token" button
- Or look for a section that says "Access Token" or "Bearer Token"

The token you need is usually 40-64 characters long and looks something like:
`xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Still can't find it?** Try this alternative method:
1. Go to https://genius.com/api-clients
2. Click on your API client name
3. Look for "Generate Access Token" section
4. Click the button to generate a token
5. Copy the generated token

## Step 2: Create AWS Secret

Once you have your token, create the secret in AWS Secrets Manager:

```bash
# Replace YOUR_TOKEN_HERE with your actual Genius API token
aws secretsmanager create-secret \
  --name chordscout/genius-api-token \
  --description "Genius API token for ChordScout lyrics feature" \
  --secret-string '{"GENIUS_ACCESS_TOKEN":"YOUR_TOKEN_HERE"}' \
  --region us-east-1
```

Expected output:
```json
{
    "ARN": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:chordscout/genius-api-token-XXXXX",
    "Name": "chordscout/genius-api-token",
    "VersionId": "..."
}
```

## Step 3: Grant ECS Task Role Access

The ECS task needs permission to read this secret. Update the task role policy:

```bash
# Get the current task role name
TASK_ROLE=$(aws ecs describe-task-definition \
  --task-definition bass-transcription-ecs-dev \
  --query 'taskDefinition.taskRoleArn' \
  --output text | cut -d'/' -f2)

echo "Task Role: $TASK_ROLE"

# Create policy document
cat > /tmp/secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:chordscout/genius-api-token-*"
    }
  ]
}
EOF

# Attach inline policy to the role
aws iam put-role-policy \
  --role-name "$TASK_ROLE" \
  --policy-name GeniusAPISecretAccess \
  --policy-document file:///tmp/secrets-policy.json

echo "✓ Policy attached to role: $TASK_ROLE"
```

## Step 4: Update ECS Task Definition

The task definition needs to reference the secret as an environment variable:

```bash
# Get current task definition
aws ecs describe-task-definition \
  --task-definition bass-transcription-ecs-dev \
  --query 'taskDefinition' > /tmp/task-def.json

# Edit the task definition to add the secret
# Add this to the containerDefinitions[0].secrets array:
```

```json
{
  "name": "GENIUS_ACCESS_TOKEN",
  "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:chordscout/genius-api-token-XXXXX:GENIUS_ACCESS_TOKEN::"
}
```

Or use this script to update it automatically:

```bash
# Get the secret ARN
SECRET_ARN=$(aws secretsmanager describe-secret \
  --secret-id chordscout/genius-api-token \
  --query 'ARN' \
  --output text)

echo "Secret ARN: $SECRET_ARN"

# Note: You'll need to manually edit the task definition JSON
# or use a script to inject the secret reference
echo "Add this to your task definition's secrets array:"
echo "{\"name\": \"GENIUS_ACCESS_TOKEN\", \"valueFrom\": \"${SECRET_ARN}:GENIUS_ACCESS_TOKEN::\"}"
```

## Step 5: Test the Secret Retrieval

After setting up the secret and updating the task definition, test it:

```bash
# Test locally (if you have AWS credentials configured)
./test-genius-simple.sh
```

Expected output:
```
✓ Secrets Manager:       ✓ PASS
✓ API Connection:        ✓ PASS
✓ ALL TESTS PASSED - Genius API is properly configured
```

## Step 6: Test in ECS Task

To test the secret retrieval in an actual ECS task:

1. Deploy the updated task definition
2. Run a test job
3. Check CloudWatch logs for:
   ```
   ENABLE_LYRICS: True
   GENIUS_ACCESS_TOKEN: [masked value]
   ```

## Alternative: Local Development

For local development, you can set the environment variable directly:

```bash
# Add to .env file
echo 'GENIUS_ACCESS_TOKEN=your_token_here' >> ../../.env

# Or export directly
export GENIUS_ACCESS_TOKEN='your_token_here'

# Test
./test-genius-simple.sh
```

## Troubleshooting

### Secret Not Found
```
✗ Secret 'chordscout/genius-api-token' does not exist
```
**Solution**: Create the secret using Step 2 above

### Access Denied
```
✗ Access denied - check IAM permissions
```
**Solution**: Grant the ECS task role access using Step 3 above

### API Request Failed (401)
```
✗ API request failed (status: 401)
```
**Solution**: Your token is invalid or expired. Get a new token from Genius

### API Request Failed (429)
```
✗ API request failed (status: 429)
```
**Solution**: Rate limit exceeded. Wait a few minutes and try again

## Security Best Practices

1. **Never commit tokens to git** - Always use Secrets Manager or environment variables
2. **Rotate tokens periodically** - Update the secret in Secrets Manager
3. **Use least privilege** - Only grant secret access to roles that need it
4. **Monitor usage** - Check CloudWatch logs for API errors

## Cost Considerations

- **Genius API**: Free tier includes 1000 requests/day (sufficient for most use cases)
- **AWS Secrets Manager**: $0.40/month per secret + $0.05 per 10,000 API calls
- **Estimated monthly cost**: ~$0.50 for typical usage

## Next Steps

After completing this setup:
1. ✓ Test the secret retrieval
2. Update environment variables (Task 16.2)
3. Deploy updated ECS task (Task 16.3)
4. Validate Phase 3 deployment (Task 16.4)

## References

- Genius API Documentation: https://docs.genius.com/
- AWS Secrets Manager: https://docs.aws.amazon.com/secretsmanager/
- ECS Task Definition Secrets: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/specifying-sensitive-data-secrets.html
