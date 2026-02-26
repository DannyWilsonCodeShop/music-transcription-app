# Chord Detection Rebuild - Account 090130568474

**Date**: February 10, 2026  
**Status**: In Progress - Docker image building via GitHub Actions

## What We're Doing

Rebuilding the enhanced chord detection (84 templates) in the correct AWS account (090130568474) to integrate with the new file upload pipeline.

## Architecture

```
User Upload → S3 → Lambda (process-audio) → ECS Task (chord-detection) → DynamoDB
                                                                              ↓
                                                                         Job Complete
```

## Components Created

### 1. Docker Image
**Location**: `simple-pipeline/chord-detection/`
- **Dockerfile**: Python 3.9 with librosa, scipy, numpy
- **app.py**: Enhanced chord detection with 84 templates
- **requirements.txt**: Minimal dependencies (no Demucs/MSAF for faster builds)

**Features**:
- 84 chord templates (major, minor, 7th, maj7, m7, sus4, dim)
- Half-beat resolution for better temporal accuracy
- Pattern-based key detection
- Song structure detection
- Nashville Number System conversion

### 2. ECS Infrastructure
**CloudFormation**: `cloudformation-chord-detection.yaml`
- ECS Cluster: `music-transcription-test`
- Task Definition: `music-transcription-chord-detection`
- Fargate: 2 vCPU, 4 GB RAM
- IAM roles for S3 and DynamoDB access

### 3. GitHub Actions Workflow
**File**: `.github/workflows/build-chord-detection.yml`
- Triggers on push to `simple-pipeline/chord-detection/**`
- Builds Docker image
- Pushes to ECR: `090130568474.dkr.ecr.us-east-1.amazonaws.com/music-transcription-chord-detection`

### 4. Processing Lambda Update
**Modified**: `simple-pipeline/deploy-processing.sh`
- Now launches ECS tasks instead of simulating completion
- Passes job ID, bucket, and key as environment variables
- Updates job status to PROCESSING (5%)

## Deployment Steps

### Step 1: Build Docker Image ✅
```bash
git push origin dev  # Triggers GitHub Actions
```
**Status**: Running - check https://github.com/YOUR_REPO/actions

### Step 2: Deploy ECS Infrastructure (Waiting for Docker image)
```bash
cd simple-pipeline/chord-detection
chmod +x deploy-infrastructure.sh
./deploy-infrastructure.sh
```

### Step 3: Update Processing Lambda (After ECS deployed)
```bash
cd simple-pipeline
./deploy-processing.sh  # Re-deploy with ECS configuration
```

### Step 4: Test End-to-End
```bash
./test-upload.sh path/to/audio.mp3
```

## Changes from Old System

### Removed
- ❌ Demucs (stem separation) - too heavy, slow builds
- ❌ MSAF (audio segmentation) - optional dependency
- ❌ Essentia - build issues, using librosa instead
- ❌ PDF generation trigger - simplified for now
- ❌ Cross-account complexity

### Kept
- ✅ Enhanced 84-template chord detection
- ✅ Pattern-based key detection
- ✅ Song structure detection
- ✅ Nashville Number System
- ✅ Half-beat resolution
- ✅ Confidence scoring

### Simplified
- Environment variables match new pipeline
- Status flow: UPLOADING → PROCESSING → COMPLETED
- No intermediate states (DETECTING_CHORDS, CHORDS_DETECTED)
- Direct DynamoDB updates (no PDF trigger yet)

## Environment Variables

### ECS Task
- `JOB_ID`: Job identifier
- `AUDIO_BUCKET`: S3 bucket name
- `AUDIO_KEY`: S3 object key
- `JOBS_TABLE`: DynamoDB table name

### Processing Lambda
- `JOBS_TABLE`: DynamoDB table name
- `ECS_CLUSTER`: ECS cluster name
- `ECS_TASK_DEFINITION`: Task definition name
- `ECS_SUBNETS`: Comma-separated subnet IDs
- `ECS_SECURITY_GROUPS`: Comma-separated security group IDs

## Expected Performance

Based on previous deployments:
- **Build time**: 3-5 minutes (GitHub Actions)
- **Cold start**: 10-15 seconds (ECS task launch)
- **Processing time**: 30-60 seconds for 3-minute song
- **Total time**: ~1-2 minutes from upload to completion

## Testing Plan

1. **Upload small file** (30 seconds)
   - Verify ECS task launches
   - Check CloudWatch logs
   - Confirm chord data in DynamoDB

2. **Upload medium file** (3 minutes)
   - Verify full processing
   - Check chord count and quality
   - Verify key detection

3. **Upload large file** (5+ minutes)
   - Verify no timeouts
   - Check memory usage
   - Verify complete results

## Monitoring

### CloudWatch Logs
```bash
aws logs tail /ecs/music-transcription-chord-detection --follow --profile production
```

### ECS Tasks
```bash
aws ecs list-tasks --cluster music-transcription-test --profile production
```

### DynamoDB Jobs
```bash
aws dynamodb scan --table-name MusicTranscription-Jobs-test --profile production
```

## Rollback Plan

If issues occur:
1. Keep file upload pipeline (it's working)
2. Revert processing Lambda to simulation mode
3. Debug ECS task separately
4. Re-deploy when fixed

## Next Steps After This Works

1. Add PDF generation back
2. Add lyrics extraction
3. Add frontend to display results
4. Add user authentication
5. Add rate limiting
6. Add cost monitoring

## Cost Estimate

- **ECS Fargate**: ~$0.08 per hour (2 vCPU, 4 GB)
- **Per song**: ~$0.001-0.002 (1-2 minutes runtime)
- **S3 storage**: ~$0.023 per GB/month
- **DynamoDB**: Free tier covers testing
- **Total**: < $1/month for testing, ~$1-2 per 1000 songs in production

## Files Modified/Created

```
simple-pipeline/
├── chord-detection/
│   ├── Dockerfile                          # NEW
│   ├── requirements.txt                    # NEW
│   ├── app.py                             # NEW (copied from backend)
│   ├── cloudformation-chord-detection.yaml # NEW
│   ├── deploy-ecs.sh                      # NEW
│   └── deploy-infrastructure.sh           # NEW
├── deploy-processing.sh                    # MODIFIED (ECS trigger)
└── CHORD_DETECTION_REBUILD.md             # NEW (this file)

.github/workflows/
└── build-chord-detection.yml              # NEW
```

## Current Status

- [x] Code written and pushed to GitHub
- [ ] Docker image building (GitHub Actions running)
- [ ] ECS infrastructure deployed
- [ ] Processing Lambda updated
- [ ] End-to-end test passed

**Check build status**: https://github.com/DannyWilsonCodeShop/music-transcription-app/actions
