# Docker Image Fix - Chord Detection ECS

**Date**: January 29, 2026  
**Status**: ✅ Fixed

## Problem

The chord detection was getting stuck because the ECS task couldn't pull the Docker image from ECR.

**Error**:
```
CannotPullContainerError: pull image manifest has been retried 7 time(s): 
failed to resolve ref 463470937777.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest: 
not found
```

## Root Cause

The ECR repository existed but was empty - no Docker image had been pushed to it.

## Solution

Built and pushed the Docker image to ECR:

```bash
# 1. Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  463470937777.dkr.ecr.us-east-1.amazonaws.com

# 2. Build image for linux/amd64 (ECS Fargate platform)
docker build --platform linux/amd64 \
  -t chordscout-chord-detector:latest \
  backend/functions-v2/chord-detector-ecs/

# 3. Tag image
docker tag chordscout-chord-detector:latest \
  463470937777.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest

# 4. Push to ECR
docker push 463470937777.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest
```

## Test Results

✅ **Chord Detection Working!**

Test job: `ed0b0ed2-fbd6-499b-8648-cde5fc62f93b`

1. ✅ YouTube download (RapidAPI) - SUCCESS
2. ✅ Chord detection (ECS) - SUCCESS  
3. ❌ Lyrics transcription - FAILED (missing dependencies)
4. ❌ PDF generation - FAILED (missing jspdf module)

**Chord Detection Status**: `CHORDS_DETECTED` (85% progress)

The ECS task successfully:
- Pulled the Docker image from ECR
- Downloaded audio from S3
- Analyzed chords using librosa
- Updated DynamoDB with results

## Remaining Issues

### 1. Lyrics Transcriber Lambda
**Error**: Missing dependencies
**Fix Needed**: Deploy Lambda with all node_modules

### 2. PDF Generator Lambda  
**Error**: `Cannot find module 'jspdf'`
**Fix Needed**: Deploy Lambda with jspdf and dependencies

## Docker Image Details

**Image**: `463470937777.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest`
**Digest**: `sha256:e19df1511e1741291f24ff31768534589c723d313e6075397c3e0ae03ba2ce73`
**Size**: 856 bytes (manifest)
**Platform**: linux/amd64
**Base**: python:3.9-slim

**Contents**:
- Python 3.9
- librosa (for chord detection)
- boto3 (for AWS SDK)
- soundfile, ffmpeg (for audio processing)
- numpy, scipy (for signal processing)

## Verification

```bash
# Check image exists in ECR
aws ecr list-images --repository-name chordscout-chord-detector --region us-east-1

# Output:
{
    "imageIds": [
        {
            "imageDigest": "sha256:e19df1511e1741291f24ff31768534589c723d313e6075397c3e0ae03ba2ce73",
            "imageTag": "latest"
        }
    ]
}
```

## Next Steps

1. ✅ Chord detection - WORKING
2. ⏳ Fix lyrics transcriber Lambda dependencies
3. ⏳ Fix PDF generator Lambda dependencies
4. ⏳ Test complete end-to-end workflow

## Notes

- The Docker image uses librosa (not madmom) for chord detection
- Image is built for linux/amd64 platform (required for ECS Fargate)
- Image is cached locally, so rebuilds are fast
- ECR repository has no lifecycle policy - images won't be automatically deleted
