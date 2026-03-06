# Phase 3 Deployment Issue and Fix

**Date**: 2026-03-05  
**Issue**: Phase 3 features not working despite task definition update

## Problem Identified

The Phase 3 test completed successfully but song identification, lyrics fetching, and key detection did not run. Investigation revealed:

1. ✅ Task definition revision 15 has correct environment variables
2. ✅ Genius API secret is accessible
3. ✅ IAM permissions are correct
4. ❌ **Docker image was not rebuilt with v3.0 code**

The ECS task is using the `:latest` Docker image tag, but that image still contains the old v2.0 code. The new modules (`song_metadata_lyrics.py`, `stem_transcription.py`, updated `bass_note_transcription.py`) exist locally but were never built into a Docker image and pushed to ECR.

## Evidence

### Log Analysis
```
[2026-03-05 23:37:22] [INFO] 🎤 Extracting lyrics from: /tmp/test-phase3-1772753540-audio.mp3
```

This shows the old Whisper-based lyrics extraction running, not the new Genius API integration.

### Missing from Logs
- No "ENABLE_SONG_ID" or "ENABLE_LYRICS" environment variable logging
- No "Identifying song..." status messages
- No Genius API calls
- No key detection from transcribed notes

## Root Cause

Task 16.3 stated: "Build and push Docker image (v3.0-phase3)" but this step was skipped. We only:
1. ✅ Updated task definition environment variables
2. ✅ Fixed secret reference format
3. ❌ Did NOT rebuild Docker image
4. ❌ Did NOT push to ECR

## Solution

### Step 1: Build Docker Image with v3.0 Code

The Docker image needs to include:
- `song_metadata_lyrics.py` - Song identification and Genius API integration
- `stem_transcription.py` - Multi-stem transcription
- Updated `bass_note_transcription.py` - 8th note quantization
- Updated `app.py` - v3.0 pipeline orchestration
- Updated `requirements.txt` - New dependencies (mutagen, lyricsgenius, etc.)

### Step 2: Push to ECR

Tag and push the image:
```bash
docker tag chordscout-chord-detector:v3.0-phase3 \
  090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:v3.0-phase3

docker push 090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:v3.0-phase3

# Also update :latest tag
docker tag chordscout-chord-detector:v3.0-phase3 \
  090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest

docker push 090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest
```

### Step 3: Verify New Image

After pushing, trigger a new ECS task and verify:
1. Environment variables are logged correctly
2. Song identification runs
3. Genius API is called for lyrics
4. Key detection runs
5. Phase 3 features appear in DynamoDB

## Secret Reference Fix

During testing, we discovered the secret reference format was incorrect:

**Before (Revision 14)**:
```
arn:aws:secretsmanager:us-east-1:090130568474:secret:chordscout/genius-api-token-TIzd2O:GENIUS_ACCESS_TOKEN::
```

**After (Revision 15)**:
```
arn:aws:secretsmanager:us-east-1:090130568474:secret:chordscout/genius-api-token-TIzd2O
```

The `:GENIUS_ACCESS_TOKEN::` suffix is not valid for ECS secret references. ECS automatically retrieves the entire secret value (which is a JSON string with the token).

## Current Status

- ✅ Task definition revision 15 is correct
- ✅ Secret reference format is fixed
- ✅ IAM permissions are correct
- ❌ Docker image needs to be built and pushed
- ⏳ Phase 3 testing pending image deployment

## Next Steps

1. Build Docker image with v3.0 code
2. Push to ECR with tags: `v3.0-phase3` and `latest`
3. Trigger new ECS task
4. Run Phase 3 end-to-end test again
5. Verify all Phase 3 features work:
   - Song identification
   - Lyrics from Genius API
   - Key detection
   - Lyrics in PDF output

## Files Created

- `fix-secret-reference.sh` - Fixed secret ARN format (created revision 15)
- `PHASE3_DEPLOYMENT_FIX.md` - This document

## Lessons Learned

1. Task definition updates alone are not sufficient
2. Docker image must be rebuilt when code changes
3. Always verify which image version is running
4. Check logs to confirm new code is executing
5. Secret reference format for ECS is different from direct API calls

