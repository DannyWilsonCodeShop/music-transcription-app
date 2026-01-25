# ChordScout Deployment Guide

## Quick Answer: Deployment Times

### First Time Setup
- **Docker Image Build**: 30-40 minutes (ONE TIME ONLY)
- **Infrastructure Deploy**: 5-10 minutes
- **Total**: ~45 minutes

### Regular Deployments (After First Time)
- **Frontend Changes**: 5-7 minutes (Amplify auto-deploy)
- **Backend Changes**: 2-5 minutes (CloudFormation update)
- **No Docker rebuild needed**: Uses cached image from ECR
- **Total**: 5-7 minutes ⚡

## Deployment Types

### 1. Frontend-Only Deployment (Most Common)
**When**: You change React/TypeScript code

**Time**: 5-7 minutes

**Process**: Automatic via Amplify
```bash
git add .
git commit -m "Update frontend"
git push origin main
# Amplify automatically builds and deploys
```

**What Happens**:
- Amplify detects push to main branch
- Runs `npm install` and `npm run build`
- Deploys to CloudFront CDN
- No Docker build needed ✅

---

### 2. Backend Lambda Deployment (Occasional)
**When**: You change Lambda function code (non-Docker)

**Time**: 2-5 minutes

**Process**: Update CloudFormation
```bash
aws cloudformation deploy \
  --template-file backend/infrastructure/cloudformation-template-simple.yaml \
  --stack-name ChordScout-Pipeline-dev \
  --capabilities CAPABILITY_NAMED_IAM
```

**What Happens**:
- CloudFormation updates Lambda functions
- Uses inline code from template
- No Docker build needed ✅

---

### 3. Chord Detector Deployment (Rare)
**When**: You change ML code or dependencies

**Time**: 
- **First time**: 30-40 minutes (building Docker image)
- **After that**: 5-10 minutes (using cached image)

**Process**: 
#### Option A: GitHub Actions (Recommended)
```bash
# Just push your changes
git add backend/functions/chord-detector-ml/
git commit -m "Update chord detector"
git push origin main
# GitHub Actions builds and pushes Docker image automatically
```

#### Option B: Local Build
```bash
# Build image (30-40 min first time, 2-5 min after with cache)
docker build --platform linux/amd64 -t chordscout-chord-detector backend/functions/chord-detector-ml/

# Push to ECR (5-10 min)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 090130568474.dkr.ecr.us-east-1.amazonaws.com
docker tag chordscout-chord-detector:latest 090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest
docker push 090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest
```

**What Happens**:
- Docker builds image with ML libraries
- **First time**: Downloads all packages (~600MB)
- **Subsequent builds**: Uses Docker layer cache (much faster)
- Pushes to ECR
- Lambda uses image from ECR

---

## Docker Build Optimization

### Why First Build is Slow
1. **TensorFlow**: ~500MB
2. **scipy**: ~38MB  
3. **librosa**: ~10MB
4. **Other dependencies**: ~50MB
5. **Total**: ~600MB to download

### How Docker Caching Works
Docker caches each layer. If nothing changes, it reuses the cached layer:

```dockerfile
# Layer 1: Base image (cached after first time)
FROM public.ecr.aws/lambda/python:3.11

# Layer 2: System deps (cached after first time)
RUN yum install -y libsndfile ffmpeg

# Layer 3: pip upgrade (cached after first time)
RUN pip install --upgrade pip wheel

# Layer 4: Python packages (cached if requirements.txt unchanged)
RUN pip install -r requirements.txt

# Layer 5: Your code (only this rebuilds when you change code)
COPY handler.py chord_utils.py ./
```

**Result**: If you only change `handler.py`, Docker skips layers 1-4 and only rebuilds layer 5 (seconds, not minutes).

---

## Recommended Workflow

### For Development
1. **Use GitHub Actions** for Docker builds
   - Builds happen in the cloud
   - You don't wait locally
   - Automatic on push

2. **Test locally without Docker**
   - Use Python virtual environment
   - Test chord detection logic
   - Only build Docker when ready to deploy

### For Production
1. **Set up CI/CD Pipeline**
   - GitHub Actions builds Docker images
   - Automatic CloudFormation updates
   - Zero manual steps

2. **Use Image Tags**
   - Tag images with version numbers
   - Easy rollback if needed
   - Track what's deployed

---

## Setup GitHub Actions (One-Time)

### 1. Create AWS IAM User for GitHub
```bash
aws iam create-user --user-name github-actions-chordscout

aws iam attach-user-policy \
  --user-name github-actions-chordscout \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

aws iam create-access-key --user-name github-actions-chordscout
# Save the AccessKeyId and SecretAccessKey
```

### 2. Add Secrets to GitHub
Go to: `https://github.com/DannyWilsonCodeShop/music-transcription-app/settings/secrets/actions`

Add:
- `AWS_ACCESS_KEY_ID`: (from step 1)
- `AWS_SECRET_ACCESS_KEY`: (from step 1)

### 3. Push Workflow File
```bash
git add .github/workflows/build-chord-detector.yml
git commit -m "Add GitHub Actions workflow for Docker builds"
git push origin main
```

### 4. Trigger Build
- **Automatic**: Push changes to `backend/functions/chord-detector-ml/`
- **Manual**: Go to Actions tab → "Build Chord Detector Docker Image" → "Run workflow"

---

## Deployment Checklist

### First Time Setup (One-Time)
- [ ] Build Docker image (30-40 min)
- [ ] Push to ECR (5-10 min)
- [ ] Deploy CloudFormation stack (5-10 min)
- [ ] Set up GitHub Actions (5 min)
- [ ] Test end-to-end pipeline (10 min)

**Total First Time**: ~1 hour

### Regular Deployments (Every Time)
- [ ] Make code changes (varies)
- [ ] Commit and push (1 min)
- [ ] Wait for Amplify build (5-7 min)
- [ ] Test changes (5-10 min)

**Total Regular**: ~15 minutes

---

## Cost Optimization

### Docker Image Storage
- **ECR Storage**: $0.10 per GB/month
- **Chord Detector Image**: ~1.5 GB
- **Cost**: ~$0.15/month

### Build Costs
- **GitHub Actions**: 2,000 minutes/month free
- **Docker Build**: ~10 minutes per build
- **Cost**: Free for most usage

### Lambda Costs
- **First 1M requests**: Free
- **After that**: $0.20 per 1M requests
- **Typical usage**: Well within free tier

---

## Troubleshooting

### Docker Build Fails
**Problem**: Out of memory or timeout

**Solution**:
```bash
# Increase Docker memory (Docker Desktop → Settings → Resources)
# Or use GitHub Actions (8GB RAM available)
```

### ECR Push Fails
**Problem**: Authentication error

**Solution**:
```bash
# Re-authenticate
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  090130568474.dkr.ecr.us-east-1.amazonaws.com
```

### Lambda Can't Pull Image
**Problem**: Lambda execution role lacks ECR permissions

**Solution**: Already configured in CloudFormation template ✅

---

## Summary

### You Only Wait 30-40 Minutes:
- ✅ **Once** for initial Docker build
- ✅ Never again (unless you change ML dependencies)

### Regular Deployments Take:
- ✅ **5-7 minutes** for frontend changes
- ✅ **2-5 minutes** for backend changes
- ✅ **Automatic** via Amplify and GitHub Actions

### Best Practice:
- ✅ Use GitHub Actions for Docker builds
- ✅ Let CI/CD handle deployments
- ✅ You focus on coding, not waiting

---

## Next Steps

1. **Wait for current Docker build to finish** (one time)
2. **Set up GitHub Actions** (5 minutes)
3. **Never wait for Docker builds again** ✨

After initial setup, your deployment workflow will be:
```bash
git add .
git commit -m "Add new feature"
git push origin main
# ☕ Grab coffee, come back in 5-7 minutes, feature is live!
```
