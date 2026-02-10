# Quality Diagnosis - Action Plan

**Date:** February 5, 2026  
**Issue:** Chord detection accuracy is not meeting expectations  
**Status:** Diagnostic tools created, ready to test

---

## Your Concern

> "The chords are not right, the key is not right, the progressions are not right."

**You're absolutely right to question this.** We need to isolate where the problem is occurring.

---

## The Pipeline

Your app processes audio in these stages:

```
YouTube URL
  ↓
1. YouTube Downloader (yt-dlp)
   - Extracts audio from video
   - Converts to MP3 (192 kbps)
   - Uploads to S3
  ↓
2. Chord Detector (librosa + templates)
   - Downloads MP3 from S3
   - Loads audio (22050 Hz)
   - Detects chords with 84 templates
   - Detects key with frequency analysis
  ↓
3. Results displayed on frontend
```

**Problem could be at ANY stage:**
- ❌ Stage 1: Poor audio quality from YouTube
- ❌ Stage 2: Chord detection algorithm issues
- ❌ Stage 3: (unlikely - just displays data)

---

## Diagnostic Tools Created

### 1. Download Job Audio Script ⭐ START HERE

**File:** `download-job-audio.js`

**What it does:**
- Downloads the actual MP3 file from S3
- Shows audio quality metrics (bitrate, size)
- Displays detected chords for comparison

**Usage:**
```bash
# Get a recent job ID from your frontend
node download-job-audio.js abc123-def456-ghi789
```

**Output:**
- MP3 file saved to `downloaded-audio/`
- You can LISTEN to it and verify quality
- Compare what you hear vs what was detected

**This is the KEY diagnostic tool!**

### 2. Full Pipeline Test

**File:** `test-pipeline-quality.js`

**What it does:**
- Submits a new job
- Waits for completion
- Downloads MP3
- Analyzes all stages

**Usage:**
```bash
node test-pipeline-quality.js "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 3. Deployment Status Check

**File:** `check-deployment-status.sh`

**What it does:**
- Verifies revision 9 is deployed
- Checks CloudWatch logs
- Shows current configuration

**Usage:**
```bash
./check-deployment-status.sh
```

---

## Step-by-Step Diagnosis

### Step 1: Download and Listen to MP3

```bash
# Get your most recent job ID from the frontend
# Then download the audio file
node download-job-audio.js YOUR_JOB_ID
```

**This will:**
1. Download the MP3 file
2. Show you the bitrate and quality
3. Display the detected chords

**Then:**
```bash
# Listen to the MP3
open downloaded-audio/YOUR_JOB_ID.mp3
```

**Ask yourself:**
- Is the audio clear and high quality?
- Can you hear all the instruments?
- Is there any distortion or compression artifacts?

### Step 2: Compare What You Hear vs What Was Detected

**While listening, identify:**
1. What key is the song in?
2. What are the first 5-10 chords?
3. What chord types do you hear? (major, minor, 7th, etc.)

**Compare with the detected results** (shown by the download script)

**Example:**
```
What YOU hear:
  Key: C major
  Chords: C, Am, F, G, C, Am, Dm, G

What was DETECTED:
  Key: D major (WRONG!)
  Chords: D, Bm, G, A, D, Bm, Em, A (ALL WRONG!)
```

### Step 3: Determine Root Cause

**Scenario A: Audio quality is poor**
- Distorted, low bitrate, missing frequencies
- **Root cause:** YouTube download stage
- **Solution:** Improve yt-dlp settings or use different source

**Scenario B: Audio is good, but chords are all wrong**
- Clear audio, but detected chords don't match
- **Root cause:** Chord detection algorithm
- **Solution:** Improve detection algorithm or use external service

**Scenario C: Audio is good, some chords right, some wrong**
- Mixed accuracy
- **Root cause:** Template matching or threshold issues
- **Solution:** Fine-tune detection parameters

---

## What to Look For

### Audio Quality Red Flags

❌ **Bitrate < 128 kbps** - Too low for accurate detection  
❌ **Muffled sound** - Missing high frequencies  
❌ **Distortion** - Clipping or compression artifacts  
❌ **Mono audio** - Should be stereo for best results

### Chord Detection Red Flags

❌ **Key is wrong** - Most common issue, affects all chords  
❌ **Only major/minor detected** - Missing 7ths, sus4, dim  
❌ **Too few chords** - Detection too conservative  
❌ **Too many chords** - Detection too sensitive  
❌ **Confidence < 0.1** - Algorithm is guessing

---

## Current System Settings

### YouTube Downloader

**Target quality:** 192 kbps MP3  
**Format:** bestaudio/best  
**Expected file size:** ~1.4 MB per minute

### Chord Detector

**Model:** librosa-enhanced-84-templates  
**Templates:** 84 (7 types × 12 keys)  
**Sample rate:** 22050 Hz  
**Confidence threshold:** 0.08  
**Min duration:** 0.5s

---

## Expected vs Actual

### What SHOULD Happen

**Good audio:**
- Bitrate: 192+ kbps
- Clear, no distortion
- All instruments audible

**Good detection:**
- 80-90% chord accuracy
- Correct key detection
- All 7 chord types detected
- Confidence > 0.15

### What Might Be Happening

**Possible issues:**
1. YouTube audio quality varies by video
2. Some videos have low-quality audio
3. Chord detection algorithm needs improvement
4. Key detection is failing (most likely)
5. Using wrong detection method (we just fixed this)

---

## Immediate Actions

### Action 1: Test Current Deployment ⭐ DO THIS FIRST

```bash
# Check what's deployed
./check-deployment-status.sh

# Should show revision 9
# If not, we need to redeploy
```

### Action 2: Download and Inspect Audio

```bash
# Get a recent job ID
# Download the MP3
node download-job-audio.js YOUR_JOB_ID

# Listen to it
open downloaded-audio/YOUR_JOB_ID.mp3
```

### Action 3: Report Findings

After listening, tell me:
1. **Audio quality:** Good / Medium / Poor
2. **What key do YOU hear?**
3. **What chords do YOU hear?** (first 5-10)
4. **What was detected?** (shown by script)
5. **Bitrate:** (shown by script)

---

## Next Steps Based on Findings

### If Audio Quality is Poor

**Options:**
1. Increase bitrate to 320 kbps
2. Try different YouTube videos
3. Use RapidAPI instead of yt-dlp
4. Use M4A format instead of MP3

### If Chord Detection is Inaccurate

**Options:**
1. Improve key detection algorithm
2. Adjust confidence thresholds
3. Add more chord templates
4. Use external service (Spotify Basic Pitch, Chordify)
5. Try different audio processing (stem separation)

---

## Why This Approach?

**You said:** "I want to know what is happening in the app right now and test the quality at each state."

**This approach:**
- ✅ Lets you HEAR the actual MP3 file
- ✅ Isolates each stage of the pipeline
- ✅ Provides concrete evidence of where the problem is
- ✅ Guides us to the right solution

**Instead of guessing, we'll KNOW:**
- Is the audio quality good enough?
- Is the chord detection algorithm working?
- Where exactly is the failure occurring?

---

## Summary

**Created:**
1. ✅ `download-job-audio.js` - Download and inspect MP3 files
2. ✅ `test-pipeline-quality.js` - Full pipeline test
3. ✅ `check-deployment-status.sh` - Verify deployment
4. ✅ `PIPELINE_QUALITY_TESTING_GUIDE.md` - Complete guide

**Next:**
1. ⏳ Run `./check-deployment-status.sh` to verify deployment
2. ⏳ Run `node download-job-audio.js YOUR_JOB_ID` to get MP3
3. ⏳ Listen to MP3 and compare with detected chords
4. ⏳ Report findings so we can fix the right thing

---

**Start with:** `node download-job-audio.js YOUR_RECENT_JOB_ID`

This will download the MP3 so you can listen and tell me what you hear vs what was detected!
