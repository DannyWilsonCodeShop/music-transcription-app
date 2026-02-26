# GitHub Actions Setup for ECS Image Build

## Overview

We're using GitHub Actions to build and push the Docker image to ECR automatically. This avoids needing Docker Desktop on your local machine.

## Setup Steps

### 1. Add AWS Credentials to GitHub Secrets

Go to your GitHub repository:
1. Click **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add these two secrets:

**Secret 1:**
- Name: `AWS_ACCESS_KEY_ID`
- Value: Your AWS Access Key ID (from `~/.aws/credentials` production profile)

**Secret 2:**
- Name: `AWS_SECRET_ACCESS_KEY`
- Value: Your AWS Secret Access Key (from `~/.aws/credentials` production profile)

### 2. Push Code to GitHub

```bash
cd /Users/dannywilson/DevOps/ChordScout
git add .
git commit -m "Add ECS YouTube downloader with GitHub Actions"
git push origin dev
```

### 3. Trigger the Build

The workflow will automatically run when you push changes to the `simple-pipeline/ecs-youtube-downloader/` directory.

Or you can manually trigger it:
1. Go to **Actions** tab in GitHub
2. Click **Build and Push ECS YouTube Downloader**
3. Click **Run workflow**
4. Select branch (dev or main)
5. Click **Run workflow**

### 4. Monitor the Build

1. Go to **Actions** tab
2. Click on the running workflow
3. Watch the build progress
4. Should complete in 2-3 minutes

### 5. Verify Image in ECR

After the build completes:

```bash
export AWS_PROFILE=production
aws ecr describe-images \
  --repository-name music-transcription-youtube-downloader \
  --region us-east-1
```

You should see the image with tags `latest` and the git commit SHA.

## What the Workflow Does

1. ✅ Checks out your code
2. ✅ Configures AWS credentials
3. ✅ Logs into Amazon ECR
4. ✅ Creates ECR repository if needed
5. ✅ Builds Docker image
6. ✅ Tags image with commit SHA and `latest`
7. ✅ Pushes both tags to ECR

## Workflow File Location

`.github/workflows/build-ecs-image.yml`

## Triggers

The workflow runs when:
- You push to `main` or `dev` branch
- Changes are made to `simple-pipeline/ecs-youtube-downloader/**`
- You manually trigger it from GitHub Actions UI

## Next Steps

After the image is built:
1. Deploy ECS infrastructure: `cd simple-pipeline/ecs-youtube-downloader && ./deploy-ecs.sh`
2. Update API Gateway to use the new ECS trigger Lambda
3. Test the pipeline

## Troubleshooting

**Build fails with "Access Denied":**
- Check that AWS credentials are correct in GitHub Secrets
- Verify the IAM user has ECR permissions

**Image not found in ECR:**
- Check the Actions tab for build errors
- Verify the workflow completed successfully

**Want to build locally instead:**
- Install Docker Desktop
- Run `./build-and-push.sh` from the `ecs-youtube-downloader` directory
