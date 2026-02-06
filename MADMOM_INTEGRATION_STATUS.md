# Madmom Integration - Building via GitHub Actions

**Date:** February 5, 2026  
**Status:** ⏳ Building in GitHub Actions

---

## What We Did

### 1. Integrated Madmom Pre-trained Model ✅

Added madmom library for deep learning-based chord detection:

```python
def detect_chords_madmom(audio_path, job_id):
    """
    Detect chords using madmom's pre-trained deep learning model
    This is more accurate than template matching, especially for minor chords
    """
    # Use madmom's DeepChromaChordRecognitionProcessor
    dcp = madmom.features.chords.DeepChromaChordRecognitionProcessor()
    chord_results = dcp(audio_path)
    
    # Convert madmom format ("C:maj", "D:min") to our format ("C", "Dm")
    # Filter short chords, consolidate consecutive identical chords
    # Return structured chord data
```

### 2. Updated Requirements ✅

Added to `requirements.txt`:
- `Cython` (required for madmom build)
- `madmom` (pre-trained chord detection)

### 3. Modified Dockerfile ✅

Install Cython and numpy first (required for madmom):
```dockerfile
# Install Cython first (required for madmom)
RUN pip install --no-cache-dir --timeout=1000 Cython numpy

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=1000 --retries=5 -r requirements.txt
```

### 4. Fallback Logic ✅

If madmom is unavailable, falls back to librosa:
```python
def detect_chords(audio_path, job_id):
    if MADMOM_AVAILABLE:
        return detect_chords_madmom(audio_path, job_id)
    else:
        return detect_chords_librosa(audio_path, job_id)
```

### 5. Pushed to GitHub ✅

Committed and pushed to `dev` branch:
```bash
git add backend/functions-v2/chord-detector-ecs/
git commit -m "feat: integrate madmom pre-trained chord detection model"
git push origin dev
```

---

## Why GitHub Actions?

Building locally was timing out due to:
1. **Large downloads** - torch (888 MB), madmom (20 MB)
2. **Network issues** - intermittent connection problems
3. **Build time** - Cython compilation takes time

GitHub Actions has:
- ✅ Better network connectivity
- ✅ More reliable downloads
- ✅ Faster build servers
- ✅ Automatic ECR push

---

## GitHub Actions Workflow

The workflow is already configured in `.github/workflows/build-chord-detector.yml`:

**Triggers:**
- Push to `main` or `dev` branch
- Changes in `backend/functions-v2/chord-detector-ecs/**`
- Manual trigger via workflow_dispatch

**Steps:**
1. Checkout code
2. Configure AWS credentials
3. Login to Amazon ECR
4. Set up Docker Buildx
5. Build and push Docker image
6. Tag as `:latest` and `:${{ github.sha }}`

**Status:** Check at https://github.com/DannyWilsonCodeShop/music-transcription-app/actions

---

## Expected Results

Once the build completes, madmom will:

### Better Minor Chord Detection ✅
- Trained on real music data
- Recognizes minor thirds accurately
- Should detect Dm, Gm, Am, etc.

### More Accurate Chord Recognition ✅
- Deep neural network model
- Better than template matching
- Handles complex harmonies

### Improved Key Detection ✅
- With accurate minor chords, key detection will improve
- Should detect F major correctly (not C major or A minor)
- Pattern recognition will find I-vi-ii-V progressions

### Expected Output for "Like The Dew"
```
Key: F major ✅
Total Chords: 40-60 ✅
Pattern 1: F → Dm → Gm → C (I → vi → ii → V) ✅
Minor chords detected: Dm, Gm ✅
```

---

## How to Monitor Build

### 1. Check GitHub Actions
Visit: https://github.com/DannyWilsonCodeShop/music-transcription-app/actions

Look for:
- Workflow: "Build Chord Detector Docker Image"
- Branch: dev
- Commit: "feat: integrate madmom pre-trained chord detection model"

### 2. Build Status

**Running:** Yellow circle icon  
**Success:** Green checkmark  
**Failed:** Red X  

### 3. View Logs

Click on the workflow run to see:
- Build output
- Docker push status
- Any errors

---

## After Build Completes

### 1. Verify Image in ECR

```bash
aws ecr describe-images \
  --repository-name chordscout-chord-detector \
  --profile chordscout \
  --region us-east-1 \
  --query 'sort_by(imageDetails,& imagePushedAt)[-1]'
```

Look for the latest image with tag `:latest`

### 2. Test with New Job

```bash
node test-roman-numerals.cjs
```

This will:
- Submit a new job for "Like The Dew"
- ECS will pull the new `:latest` image
- Madmom will be used for chord detection
- Results should show minor chords

### 3. Expected Improvements

**Before (librosa template matching):**
- Chords: 180-383 (too many)
- Key: C major or A minor ❌
- Minor chords: 0 detected ❌
- Pattern: C → C → F (not useful)

**After (madmom pre-trained):**
- Chords: 40-60 (reasonable)
- Key: F major ✅
- Minor chords: Dm, Gm detected ✅
- Pattern: F → Dm → Gm → C (I-vi-ii-V) ✅

---

## Troubleshooting

### If Build Fails

**Check logs for:**
1. Cython installation errors
2. Madmom build errors
3. Network timeout issues

**Solutions:**
- Increase timeout values
- Add more retries
- Split into multiple RUN commands

### If Build Succeeds But Madmom Not Working

**Check ECS logs:**
```bash
aws logs tail /aws/ecs/chordscout-chord-detector-dev \
  --since 5m \
  --follow \
  --profile chordscout
```

Look for:
- "Using madmom pre-trained model" ✅
- "Madmom not available, using librosa" ❌

### If Still Not Detecting Minor Chords

**Possible issues:**
1. Madmom model not loading correctly
2. Audio quality too low
3. Song doesn't have clear minor chords
4. Need to adjust consolidation thresholds

---

## Next Steps

### 1. Wait for Build (5-10 minutes)

GitHub Actions will:
- Install dependencies
- Build Docker image
- Push to ECR
- Tag as `:latest`

### 2. Test New Image

Once build completes:
```bash
node test-roman-numerals.cjs
```

### 3. Verify Results

Check for:
- ✅ Minor chords detected (Dm, Gm)
- ✅ Correct key (F major)
- ✅ Expected pattern (F → Dm → Gm → C)
- ✅ Reasonable chord count (40-60)

### 4. If Successful

- Switch back to full PDF generator
- Deploy to production
- Document the improvements

### 5. If Still Issues

- Try different test song
- Analyze madmom output directly
- Adjust post-processing thresholds
- Consider ensemble approach (madmom + librosa)

---

## Files Changed

### Modified
- `backend/functions-v2/chord-detector-ecs/app.py` - Added madmom integration
- `backend/functions-v2/chord-detector-ecs/requirements.txt` - Added madmom
- `backend/functions-v2/chord-detector-ecs/Dockerfile` - Install Cython first

### Added
- `CHORD_DETECTION_IMPROVEMENTS_V2.md` - Documentation of improvements
- `ROMAN_NUMERALS_WORKING.md` - Roman numeral status
- `ROMAN_NUMERAL_NOTATION_STATUS.md` - Implementation details
- `test-roman-numerals.cjs` - Test script
- `MADMOM_INTEGRATION_STATUS.md` - This file

---

## Summary

We've integrated madmom's pre-trained chord detection model to improve accuracy, especially for minor chords. The Docker image is building in GitHub Actions with better network connectivity. Once complete, we'll test and should see significant improvements in chord detection accuracy and key detection.

**Current Status:** ⏳ Building in GitHub Actions  
**Next:** Wait for build, then test with new job  
**Expected:** Minor chords detected, correct key, accurate patterns

---

**Monitor build at:** https://github.com/DannyWilsonCodeShop/music-transcription-app/actions
