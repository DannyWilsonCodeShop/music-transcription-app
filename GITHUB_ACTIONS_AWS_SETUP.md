# GitHub Actions AWS Credentials Setup

## Step 1: Create IAM User for GitHub Actions (if not exists)

1. Go to AWS Console: https://console.aws.amazon.com/iam/
2. Click "Users" in the left sidebar
3. Click "Create user"
4. User name: `github-actions-ecr`
5. Click "Next"
6. Select "Attach policies directly"
7. Search and select these policies:
   - `AmazonEC2ContainerRegistryPowerUser` (for ECR access)
   - Or create a custom policy with these permissions:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": [
             "ecr:GetAuthorizationToken",
             "ecr:BatchCheckLayerAvailability",
             "ecr:GetDownloadUrlForLayer",
             "ecr:BatchGetImage",
             "ecr:PutImage",
             "ecr:InitiateLayerUpload",
             "ecr:UploadLayerPart",
             "ecr:CompleteLayerUpload",
             "ecr:DescribeRepositories",
             "ecr:CreateRepository"
           ],
           "Resource": "*"
         }
       ]
     }
     ```
8. Click "Next" and "Create user"

## Step 2: Create Access Keys

1. Click on the newly created user `github-actions-ecr`
2. Go to "Security credentials" tab
3. Scroll down to "Access keys"
4. Click "Create access key"
5. Select "Third-party service"
6. Check the confirmation box
7. Click "Next"
8. Add description: "GitHub Actions for ECR"
9. Click "Create access key"
10. **IMPORTANT**: Copy both:
    - Access key ID (starts with `AKIA...`)
    - Secret access key (long random string)
    - Save these somewhere safe - you won't see the secret again!

## Step 3: Add Secrets to GitHub

1. Go to your GitHub repository: https://github.com/DannyWilsonCodeShop/music-transcription-app
2. Click "Settings" (top right)
3. In the left sidebar, click "Secrets and variables" → "Actions"
4. Click "New repository secret"

### Add AWS_ACCESS_KEY_ID:
- Name: `AWS_ACCESS_KEY_ID`
- Secret: Paste the Access key ID from Step 2
- Click "Add secret"

### Add AWS_SECRET_ACCESS_KEY:
- Click "New repository secret" again
- Name: `AWS_SECRET_ACCESS_KEY`
- Secret: Paste the Secret access key from Step 2
- Click "Add secret"

## Step 4: Verify Setup

1. Go to "Actions" tab in your GitHub repo
2. Find a failed workflow run
3. Click "Re-run all jobs"
4. The workflow should now succeed!

## Alternative: Use Existing AWS Credentials

If you already have AWS credentials configured locally (the ones you use with `AWS_PROFILE=production`), you can use those:

1. Find your credentials file:
   ```bash
   cat ~/.aws/credentials
   ```

2. Look for the `[production]` section:
   ```
   [production]
   aws_access_key_id = AKIA...
   aws_secret_access_key = ...
   ```

3. Copy those values to GitHub Secrets as described in Step 3 above

## Security Notes

- These credentials will only be used by GitHub Actions to push Docker images to ECR
- They are encrypted and only accessible to workflow runs
- Never commit credentials to your repository
- You can rotate these keys anytime in AWS IAM Console

## Troubleshooting

If workflows still fail after adding credentials:

1. Check the workflow logs in GitHub Actions tab
2. Verify the IAM user has ECR permissions
3. Ensure the ECR repositories exist in account 090130568474
4. Check that the AWS region is correct (us-east-1)
