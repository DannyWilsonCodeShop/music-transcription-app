# Add AWS Credentials to GitHub Secrets

## Step-by-Step Instructions

### 1. Go to Your Repository Settings

1. Open https://github.com/DannyWilsonCodeShop/music-transcription-app
2. Click the **Settings** tab (top right)
3. In the left sidebar, click **Secrets and variables** → **Actions**

### 2. Add AWS Access Key ID

1. Click **New repository secret** (green button)
2. Fill in:
   - **Name:** `AWS_ACCESS_KEY_ID`
   - **Secret:** (Get from `~/.aws/credentials` file, production profile, the value after `aws_access_key_id =`)
3. Click **Add secret**

### 3. Add AWS Secret Access Key

1. Click **New repository secret** again
2. Fill in:
   - **Name:** `AWS_SECRET_ACCESS_KEY`
   - **Secret:** (Get from `~/.aws/credentials` file, production profile, the value after `aws_secret_access_key =`)
3. Click **Add secret**

### 4. Verify Secrets Are Added

You should see two secrets listed:
- ✅ AWS_ACCESS_KEY_ID
- ✅ AWS_SECRET_ACCESS_KEY

### 5. Trigger the GitHub Action

Option A - Automatic (Recommended):
```bash
# Make a small change to trigger the workflow
cd simple-pipeline/ecs-youtube-downloader
echo "# ECS YouTube Downloader" >> README.md
git add README.md
git commit -m "Trigger ECS image build"
git push origin dev
```

Option B - Manual:
1. Go to https://github.com/DannyWilsonCodeShop/music-transcription-app/actions
2. Click **Build and Push ECS YouTube Downloader** (left sidebar)
3. Click **Run workflow** (right side)
4. Select branch: **dev**
5. Click **Run workflow** (green button)

### 6. Monitor the Build

1. Go to https://github.com/DannyWilsonCodeShop/music-transcription-app/actions
2. Click on the running workflow (yellow dot)
3. Click on the **build-and-push** job
4. Watch the logs in real-time
5. Should complete in 2-3 minutes

### 7. Verify Success

When complete, you should see:
- ✅ Green checkmark on the workflow
- ✅ "Image pushed" messages in the logs

Then verify in AWS:
```bash
export AWS_PROFILE=production
aws ecr describe-images \
  --repository-name music-transcription-youtube-downloader \
  --region us-east-1
```

You should see the Docker image!

## Next Steps

After the image is built:
1. Deploy ECS infrastructure: `cd simple-pipeline/ecs-youtube-downloader && ./deploy-ecs.sh`
2. Test the pipeline
3. Verify audio quality

## Troubleshooting

**"Secret scanning" error when adding secrets:**
- This is normal - GitHub is warning you about adding AWS credentials
- Click "Add secret anyway" or "I understand, add this secret"

**Workflow doesn't start:**
- Check that you pushed to the `dev` branch
- Check that changes were made to `simple-pipeline/ecs-youtube-downloader/` directory
- Try manual trigger (Option B above)

**Build fails:**
- Check the Actions logs for specific errors
- Verify AWS credentials are correct
- Ensure IAM user has ECR permissions
