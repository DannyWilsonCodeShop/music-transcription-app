# Task 16.2 Complete: Environment Variables Updated for Phase 3

**Date**: 2026-03-05  
**Task**: 16.2 Update environment variables for Phase 3  
**Status**: ✅ COMPLETE

## Summary

Successfully updated the ECS task definition to enable lyrics and key confirmation features for ChordScout v3.0 Phase 3.

## What Was Done

### 1. Switched to Correct AWS Account
- Identified correct profile: `chordscout` (account: 090130568474)
- Verified account access

### 2. Created Genius API Secret in Target Account
- Copied secret from source account (463470937777)
- Created secret in target account (090130568474)
- Secret name: `chordscout/genius-api-token`
- Secret ARN: `arn:aws:secretsmanager:us-east-1:090130568474:secret:chordscout/genius-api-token-TIzd2O`

### 3. Updated ECS Task Definition
- Fetched current task definition (revision 13)
- Added environment variables:
  - `ENABLE_LYRICS=true` (NEW)
  - `ENABLE_SONG_ID=true` (NEW)
  - `ENABLE_MULTI_STEM=true` (from Phase 2)
  - `ENABLE_STEM_SEPARATION=false` (existing)
- Added secret reference:
  - `GENIUS_ACCESS_TOKEN` → Secret ARN
- Registered new task definition: **revision 14**

### 4. Granted IAM Permissions
- Task role: `chordscout-v2-dev-ECSTaskRole-QBhvp2gMiDG7`
- Policy name: `GeniusAPISecretAccess`
- Permissions granted:
  - `secretsmanager:GetSecretValue`
  - `secretsmanager:DescribeSecret`
- Resource: Genius API secret ARN

## Configuration Summary

### Task Definition: chordscout-chord-detector-dev:14

**Environment Variables:**
```
ENABLE_STEM_SEPARATION = false
ENABLE_LYRICS = true          ← NEW
ENABLE_SONG_ID = true         ← NEW
ENABLE_MULTI_STEM = true
CHUNK_DURATION = 30
S3_AUDIO_BUCKET = chordscout-audio-temp-dev-090130568474
PDF_GENERATOR_FUNCTION = chordscout-v2-pdf-generator-dev
DYNAMODB_JOBS_TABLE = ChordScout-Jobs-V2-dev
```

**Secrets:**
```
GENIUS_ACCESS_TOKEN → arn:aws:secretsmanager:us-east-1:090130568474:secret:chordscout/genius-api-token-TIzd2O:GENIUS_ACCESS_TOKEN::
```

## Files Created

1. `create-genius-secret-8474.sh` - Script to copy secret between accounts
2. `update-task-def-phase3.sh` - Script to update task definition
3. `TASK_16.2_COMPLETE.md` - This summary document

## Verification

✅ Secret exists in correct account (090130568474)  
✅ Task definition updated (revision 14)  
✅ Environment variables configured  
✅ Secret reference added  
✅ IAM permissions granted  

## Next Steps

### Task 16.3: Deploy Updated ECS Task
- Build and push Docker image (v3.0-phase3)
- Update ECS service to use revision 14
- Deploy to development environment

### Task 16.4: Validate Phase 3 Deployment
- Test song identification
- Verify lyrics fetching from Genius
- Test key detection and confirmation
- Verify lyrics in PDF output
- Test complete end-to-end workflow

## Commands for Next Steps

### Update ECS Service (Task 16.3)
```bash
export AWS_PROFILE=chordscout

aws ecs update-service \
  --cluster chordscout-dev \
  --service chordscout-chord-detector-dev \
  --task-definition chordscout-chord-detector-dev:14 \
  --region us-east-1
```

### Verify Deployment
```bash
aws ecs describe-services \
  --cluster chordscout-dev \
  --services chordscout-chord-detector-dev \
  --region us-east-1 \
  --query 'services[0].{taskDefinition:taskDefinition,runningCount:runningCount,desiredCount:desiredCount}'
```

## Notes

- The Docker image doesn't need to be rebuilt since all new modules were already included in Phase 2
- The task definition now has all Phase 3 features enabled
- The ECS service needs to be updated to use the new task definition
- Once deployed, the system will have access to the Genius API for lyrics fetching

## AWS Account Information

- **Target Account**: 090130568474
- **AWS Profile**: chordscout
- **Region**: us-east-1
- **Task Family**: chordscout-chord-detector-dev
- **Current Revision**: 14
