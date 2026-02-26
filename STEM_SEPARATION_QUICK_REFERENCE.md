# Stem Separation - Quick Reference

## Status: ✅ DEPLOYED

### What Changed?
- **Memory:** 3GB → 4GB
- **Feature:** Demucs stem separation enabled (chunked processing)
- **Model:** `mdx_extra` (lightweight, optimized for chord detection)
- **Processing:** 30-second chunks to prevent OOM

### How It Works
1. Audio is split into 30-second chunks
2. Each chunk is processed through Demucs to separate:
   - Drums (discarded)
   - Bass (kept)
   - Other/Harmonic (kept - piano, strings, synths)
   - Vocals (discarded)
3. Bass + Other stems are combined for chord detection
4. Chunks are concatenated and analyzed

### Configuration

#### Enable/Disable
```bash
# Enable (current setting)
ENABLE_STEM_SEPARATION=true

# Disable (fallback to full mix)
ENABLE_STEM_SEPARATION=false
```

#### Adjust Chunk Size
```bash
# Current: 30 seconds
CHUNK_DURATION=30

# Smaller chunks (more memory efficient, slower)
CHUNK_DURATION=20

# Larger chunks (faster, more memory)
CHUNK_DURATION=40
```

### Expected Performance

| Song Length | Processing Time | Peak Memory | Cost/Job |
|-------------|----------------|-------------|----------|
| 3 minutes   | ~2 minutes     | 2.5 GB      | $0.010   |
| 6 minutes   | ~3-4 minutes   | 3.0 GB      | $0.015   |
| 10 minutes  | ~5-6 minutes   | 3.5 GB      | $0.025   |

### Monitoring Commands

```bash
# Watch logs in real-time
aws logs tail /ecs/chordscout-chord-detector-dev --follow --profile chordscout

# Check memory usage
aws ecs describe-tasks \
  --cluster ChordScout-dev \
  --tasks <task-arn> \
  --profile chordscout \
  --query 'tasks[0].containers[0].memory'

# View stem separation logs
aws logs filter-log-events \
  --log-group-name /ecs/chordscout-chord-detector-dev \
  --filter-pattern "stem separation" \
  --profile chordscout
```

### Troubleshooting

#### If OOM Errors Occur
1. Check actual memory usage in CloudWatch
2. Reduce chunk size: `CHUNK_DURATION=20`
3. Or increase memory: `Memory: '8192'` (8GB)

#### If Processing Too Slow
1. Increase chunk size: `CHUNK_DURATION=40`
2. Or disable stem separation: `ENABLE_STEM_SEPARATION=false`

#### If Quality Issues
1. Check logs for "Stem separation failed" warnings
2. Verify Demucs model loaded successfully
3. Compare results with stem separation on/off

### Quick Disable (Emergency)

If you need to quickly disable stem separation:

```bash
# Update task definition
aws ecs register-task-definition \
  --cli-input-json file://task-def-no-stem.json \
  --profile chordscout

# Or just set environment variable to false
# (requires new task definition registration)
```

### Logs to Look For

**Success:**
```
[INFO] Loading Demucs model for stem separation...
[INFO] ✓ Demucs model loaded successfully
[INFO] 🎵 Starting chunked stem separation...
[INFO] Processing in 12 chunks of 30s each
[INFO] Processing chunk 1/12...
[INFO] ✓ Chunk 1/12 complete (2.3s)
...
[INFO] ✓ Stem separation complete (harmonic stem extracted)
```

**Fallback:**
```
[WARNING] Stem separation failed: <error>
[WARNING] Falling back to full mix
[INFO] Using full mix (no stem separation)
```

### Current Deployment

- **Task Definition:** `chordscout-chord-detector-dev:7`
- **Image:** `090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest`
- **Digest:** `sha256:aec95ed61f0a993ff5615ae323fff9d99a4ae31be49d9f203d6b1383eb0e912e`
- **Memory:** 4096 MB (4GB)
- **CPU:** 1024 (1 vCPU)
- **Status:** ACTIVE

### Next Test

Submit a new job and watch for:
1. Job reaches 70% (DETECTING_CHORDS)
2. Logs show "Loading Demucs model..."
3. Logs show "Processing in N chunks..."
4. Job reaches 80% (CHORDS_DETECTED)
5. Chord data saved to DynamoDB
6. Job completes at 100%

---

**Ready for testing!** 🎵
