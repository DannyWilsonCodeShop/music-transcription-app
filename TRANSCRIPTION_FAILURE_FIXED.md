# Transcription Failure - Fixed

## Issue
Job failed with: `AccessDeniedException` - ECS task role not authorized to invoke PDF generator Lambda

## Root Cause
The ECS task role (`chordscout-v2-dev-ECSTaskRole-QBhvp2gMiDG7`) was missing the `lambda:InvokeFunction` permission needed to trigger the PDF generator.

## What Worked ✅
1. **Stem separation disabled** - Processing completed in 23 seconds (vs 18 minutes)
2. **Chord detection successful** - 258 chords detected, key: G
3. **Decimal conversion working** - Chords saved to DynamoDB without float errors
4. **Job reached 80%** - CHORDS_DETECTED status

## What Failed ❌
- **PDF generation trigger** - Permission denied when ECS task tried to invoke Lambda

## Fix Applied
Added Lambda invoke permission to ECS task role:

```json
{
  "Effect": "Allow",
  "Action": ["lambda:InvokeFunction"],
  "Resource": "arn:aws:lambda:us-east-1:090130568474:function:chordscout-v2-pdf-generator-dev"
}
```

## Timeline of Job Execution

```
06:33:58 - Job started
06:33:58 - Status: DETECTING_CHORDS (70%)
06:33:58 - Audio downloaded (6.09 MB in 0.20s)
06:34:15 - Audio loaded (371.5s duration, 17.07s load time)
06:34:21 - Chromagram computed (5.82s)
06:34:21 - Chord detection complete (0.07s, 258 chords)
06:34:21 - Status: CHORDS_DETECTED (80%)
06:34:21 - ❌ PDF generation failed (AccessDeniedException)
06:34:21 - Status: FAILED (0%)
```

**Total time:** 23 seconds (before failure)

## Performance Metrics

### With Stem Separation Disabled
- Audio download: 0.20s
- Audio loading: 17.07s
- Chromagram computation: 5.82s
- Chord detection: 0.07s
- **Total: ~23 seconds** ✅

### Previous (With Stem Separation)
- Model loading: ~10s
- Chunk processing: 84s × 13 chunks = 1,092s
- **Total: ~18 minutes** ❌

**Improvement: 47x faster!**

## Logs Analysis

### Success Indicators
```
[INFO] Stem separation disabled (ENABLE_STEM_SEPARATION=false)
[INFO] ✓ Audio downloaded successfully
[INFO] ✓ Audio loaded successfully
[INFO] ✓ Chromagram computed
[INFO] ✓ Chord detection complete
[INFO] Converting float values to Decimal for DynamoDB...
[INFO] ✓ Converted 258 chords to DynamoDB format
[INFO] ✓ Job updated with chord data (status: CHORDS_DETECTED, progress: 80%)
```

### Failure Point
```
[INFO] Step 5: Triggering PDF generation Lambda...
[ERROR] ERROR invoking PDF generation Lambda: An error occurred (AccessDeniedException)
[ERROR] FATAL ERROR in chord detection: An error occurred (AccessDeniedException)
[INFO] Updating job status: FAILED (0%)
```

## Next Test Expected Behavior

With the permission fix applied, the next job should:

1. **0-20%:** Download YouTube audio (~5s)
2. **20-60%:** Transcribe lyrics with Deepgram (~10s)
3. **60-80%:** Detect chords without stem separation (~23s)
4. **80-100%:** Generate PDF (~5s)

**Total expected time: ~45 seconds**

## Status

✅ **Permission fixed** - ECS task can now invoke PDF Lambda  
✅ **Stem separation disabled** - Fast processing enabled  
✅ **Decimal conversion working** - No more DynamoDB errors  
✅ **Ready for next test**

## Test Command

Submit a new job and it should complete successfully in ~45 seconds.

Monitor with:
```bash
aws logs tail /ecs/chordscout-chord-detector-dev --follow --profile chordscout
```

---

**Status: READY FOR TESTING** 🎵
