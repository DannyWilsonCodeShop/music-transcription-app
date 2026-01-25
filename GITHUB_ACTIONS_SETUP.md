# GitHub Actions Setup Guide

## What This Does

GitHub Actions will automatically build your Docker images in the cloud whenever you change the chord detector code. This means:

- ✅ **No more waiting locally** - Builds happen in GitHub's fast datacenter
- ✅ **10-15 minutes** instead of 2 hours
- ✅ **Automatic** - Just push code, GitHub does the rest
- ✅ **FREE** - Unlimited for public repositories
- ✅ **Professional** - Industry standard CI/CD

## Setup Instructions (5 Minutes)

### Step 1: Add AWS Credentials to GitHub

I've created a dedicated IAM user for GitHub Actions with minimal permissions (ECR only).

**Credentials Created:**
- **IAM User**: `github-actions-chordscout`
- **Permissions**: ECR PowerUser (can push/pull Docker images only)
- **Access Keys**: See `aws-credentials.txt` (not committed to git for security)

### Step 2: Add Secrets to GitHub Repository

1. **Go to your repository settings:**
   ```
   https://github.com/DannyWilsonCodeShop/music-transcription-app/settings/secrets/actions
   ```

2. **Click "New repository secret"**

3. **Add the first secret:**
   - Name: `AWS_ACCESS_KEY_ID`
   - Value: `[See aws-credentials.txt file]`
   - Click "Add secret"

4. **Add the second secret:**
   - Name: `AWS_SECRET_ACCESS_KEY`
   - Value: `[See aws-credentials.txt file]`
   - Click "Add secret"

### Step 3: Verify the Workflow File

The workflow file is already in your repository at:
```
.github/workflows/build-chord-detector.yml
```

It will automatically:
- ✅ Trigger when you change files in `backend/functions/chord-detector-ml/`
- ✅ Build the Docker image
- ✅ Push to your ECR repository
- ✅ Use caching to speed up builds

### Step 4: Test It!

Make a small change to test the workflow:

```bash
# Make a small change to the chord detector
echo "# Updated $(date)" >> backend/functions/chord-detector-ml/README.md

# Commit and push
git add backend/functions/chord-detector-ml/README.md
git commit -m "Test GitHub Actions workflow"
git push origin main
```

Then watch it build:
1. Go to: https://github.com/DannyWilsonCodeShop/music-transcription-app/actions
2. Click on the running workflow
3. Watch the build progress in real-time

## How It Works

### Automatic Triggers

The workflow runs automatically when:
- ✅ You push changes to `backend/functions/chord-detector-ml/**`
- ✅ You manually trigger it from the Actions tab

### Build Process

```
1. GitHub detects changes
   ↓
2. Spins up Ubuntu VM in GitHub's datacenter
   ↓
3. Checks out your code
   ↓
4. Logs into AWS ECR
   ↓
5. Builds Docker image (with caching)
   ↓
6. Pushes to ECR
   ↓
7. Done! (10-15 minutes)
```

### Caching

GitHub Actions caches Docker layers between builds:
- **First build**: 10-15 minutes (downloads all packages)
- **Subsequent builds**: 2-5 minutes (uses cache)

## What You Get

### Speed Comparison

| Method | First Build | Code Changes | Dependency Changes |
|--------|-------------|--------------|-------------------|
| **Local** | 2 hours | 30 seconds | 2 hours |
| **GitHub Actions** | 10-15 min | 2-5 min | 10-15 min |

### Benefits

1. **Your Computer is Free**
   - No Docker running locally
   - No waiting for builds
   - Keep working on other things

2. **Faster Builds**
   - GitHub's datacenter has fast internet
   - Downloads packages at 10-50 MB/s (vs your 30-40 KB/s)
   - 10-20x faster than local builds

3. **Automatic**
   - Push code → Build happens automatically
   - No manual docker build/push commands
   - Professional CI/CD workflow

4. **Free**
   - Unlimited minutes for public repos
   - 2,000 minutes/month for private repos
   - More than enough for your needs

## Workflow File Explained

```yaml
name: Build Chord Detector Docker Image

# When to run
on:
  push:
    branches: [main]
    paths: ['backend/functions/chord-detector-ml/**']
  workflow_dispatch: # Manual trigger

# What to do
jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Configure AWS credentials (uses secrets)
      - Login to ECR
      - Build Docker image (with caching)
      - Push to ECR
```

## Manual Trigger

You can also trigger builds manually:

1. Go to: https://github.com/DannyWilsonCodeShop/music-transcription-app/actions
2. Click "Build Chord Detector Docker Image"
3. Click "Run workflow"
4. Select branch (main)
5. Click "Run workflow"

## Monitoring Builds

### View Build Logs

1. Go to Actions tab
2. Click on a workflow run
3. Click on "build-and-push" job
4. Expand steps to see detailed logs

### Build Status

- ✅ **Green checkmark**: Build succeeded
- ❌ **Red X**: Build failed (check logs)
- 🟡 **Yellow dot**: Build in progress

### Notifications

GitHub will:
- Show status on commits
- Email you if builds fail
- Update PR status checks

## Troubleshooting

### Build Fails with "Access Denied"

**Problem**: AWS credentials not set correctly

**Solution**:
1. Verify secrets are added to GitHub
2. Check secret names match exactly:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
3. No extra spaces in secret values

### Build Fails with "Repository Not Found"

**Problem**: ECR repository doesn't exist

**Solution**:
```bash
aws ecr describe-repositories --repository-names chordscout-chord-detector --region us-east-1
# If not found, it was already created, so this shouldn't happen
```

### Build is Slow

**Problem**: Not using cache

**Solution**: Cache is automatic, but first build will always be slower

### Workflow Doesn't Trigger

**Problem**: Changes not in the right path

**Solution**: Workflow only triggers for changes in:
- `backend/functions/chord-detector-ml/**`

## Security Notes

### IAM User Permissions

The `github-actions-chordscout` user has **minimal permissions**:
- ✅ Can push/pull Docker images to ECR
- ❌ Cannot access S3, DynamoDB, Lambda, etc.
- ❌ Cannot create/delete AWS resources
- ❌ Cannot access secrets or other sensitive data

This follows the **principle of least privilege**.

### Rotating Credentials

To rotate credentials (recommended every 90 days):

```bash
# Delete old key
aws iam delete-access-key \
  --user-name github-actions-chordscout \
  --access-key-id [OLD_ACCESS_KEY_ID]

# Create new key
aws iam create-access-key \
  --user-name github-actions-chordscout

# Update GitHub secrets with new values
```

## Cost Estimate

### GitHub Actions (Public Repo)
- **Cost**: $0 (unlimited minutes)

### GitHub Actions (Private Repo)
- **Free tier**: 2,000 minutes/month
- **Your usage**: ~30-60 minutes/month
- **Cost**: $0 (well within free tier)

### ECR Storage
- **Image size**: ~1.5 GB
- **Cost**: $0.10/GB/month = $0.15/month

### Total Monthly Cost
- **GitHub Actions**: $0
- **ECR Storage**: $0.15
- **Total**: **$0.15/month**

## Next Steps

1. ✅ **Add secrets to GitHub** (5 minutes)
2. ✅ **Test the workflow** (push a small change)
3. ✅ **Watch it build** (10-15 minutes first time)
4. ✅ **Enjoy automatic builds** forever!

## Support

If you have issues:
1. Check the workflow logs in GitHub Actions
2. Verify AWS credentials are correct
3. Check ECR repository exists
4. Review this guide

## Summary

You now have:
- ✅ Professional CI/CD pipeline
- ✅ Automatic Docker builds in the cloud
- ✅ 10-20x faster than local builds
- ✅ Free for your public repository
- ✅ Industry-standard workflow

**No more 2-hour waits!** 🎉

---

**Created**: January 25, 2026  
**IAM User**: github-actions-chordscout  
**Permissions**: ECR PowerUser only  
**Status**: Ready to use
