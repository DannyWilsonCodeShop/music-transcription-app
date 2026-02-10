# Pipeline Quality Testing Guide

**Date:** February 5, 2026  
**Purpose:** Diagnose chord detection accuracy issues by testing each pipeline stage

---

## Current Pipeline Workflow

```
1. YouTube URL submitted
   ↓
2. YouTube Downloader ECS Task
   - Uses yt-dlp to extract audio
   - Converts to MP3 (192 kbps target)
   - Uploads to S3: audio/{jobId}/youtube_audio.mp3
   ↓
3. Chord Detector ECS Task
   - Downloads MP3 from S3
   - Loads audio with librosa (22050 Hz)
   - Detects chords with 84 templates
   - Detects key with frequency + progression analysis
   - Saves results to DynamoDB
   ↓
4. PDF Generator Lambda
   - Generates chord sheet PDF
   ↓
5. Frontend displays results
```

---

## Problem Statement

You're experiencing:
- ❌ Incorrect chords detected
- ❌ Wrong key detection
- ❌ Incorrect progressions

**Root cause could be at any stage:**
1. **Audio quality** - Poor MP3 extraction from YouTube
2. **Audio processing** - Librosa loading/resampling issues
3. **Chord detection** - Algorithm accuracy
4. **Key detection** - Frequency analysis issues

---

## Testing Tools

### Tool 1: Full Pipeline Test

**Script:** `test-pipeline-quality.js`

**What it does:**
- Submits a new job
- Waits for completion
- Downloads the MP3 file
- Analyzes all stages
- Saves audio for manual inspection

**Usage:**
```bash
node test-pipeline-quality.js "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Output:**
- `pipeline-test-output/{jobId}.mp3` - The actual MP3 file
- `pipeline-test-output/{jobId}-full-data.json` - Complete job data
- Terminal analysis of each stage

### Tool 2: Download Existing Job Audio

**Script:** `download-job-audio.js`

**What it does:**
- Downloads MP3 from an existing job
- Shows audio quality metrics
- Displays detected chords for comparison

**Usage:**
```bash
# Get job ID from your frontend or API
node download-job-audio.js abc123-def456-ghi789
```

**Output:**
- `downloaded-audio/{jobId}.mp3` - The MP3 file
- Terminal shows bitrate, chords, key

---

## Diagnostic Process

### Step 1: Test Audio Quality

**Goal:** Verify the MP3 extracted from YouTube is high quality

**Process:**
1. Run the download script for a recent job:
   ```bash
   node download-job-audio.js YOUR_JOB_ID
   ```

2. Listen to the MP3 file:
   ```bash
   open downloaded-audio/YOUR_JOB_ID.mp3
   ```

3. Check for:
   - ✅ Clear audio (no distortion)
   - ✅ All instruments audible
   - ✅ Good bitrate (192+ kbps)
   - ✅ No compression artifacts

**If audio quality is poor:**
- Problem is in YouTube download stage
- Check yt-dlp settings in `backend/functions-v2/youtube-downloader-ecs/app.py`
- Current settings: `bestaudio/best`, 192 kbps MP3

**If audio quality is good:**
- Problem is in chord detection stage
- Continue to Step 2

### Step 2: Manual Chord Identification

**Goal:** Establish ground truth for comparison

**Process:**
1. Listen to the MP3 file
2. Manually identify:
   - What key is the song in?
   - What are the first 10 chords?
   - What chord types do you hear? (major, minor, 7th, etc.)

3. Compare with detected results:
   ```bash
   # The download script shows detected chords
   node download-job-audio.js YOUR_JOB_ID
   ```

**Example comparison:**
```
Manual identification:
  Key: C major
  Chords: C, Am, F, G, C, Am, Dm, G

Detected by system:
  Key: D major (WRONG!)
  Chords: D, Bm, G, A, D, Bm, Em, A (ALL WRONG!)
```

### Step 3: Analyze Detection Patterns

**Goal:** Understand what's going wrong

**Common issues:**

#### Issue 1: Wrong Key Detection
**Symptom:** Key is off by 1-2 semitones  
**Cause:** Frequency analysis picking wrong tonic  
**Solution:** Improve key detection algorithm

#### Issue 2: All Chords Wrong
**Symptom:** Every chord is incorrect  
**Cause:** Key detection is wrong, so Nashville numbers are wrong  
**Solution:** Fix key detection first

#### Issue 3: Some Chords Right, Some Wrong
**Symptom:** Mix of correct and incorrect chords  
**Cause:** Template matching issues  
**Solution:** Adjust confidence thresholds or add more templates

#### Issue 4: Missing Chord Types
**Symptom:** Only detecting major/minor, missing 7ths  
**Cause:** Using old essentia detection instead of enhanced librosa  
**Solution:** Verify revision 9 is deployed (we just fixed this)

### Step 4: Test with Known Songs

**Goal:** Use songs with known chords to benchmark accuracy

**Recommended test songs:**

1. **"Let It Be" - The Beatles**
   - Key: C major
   - Chords: C, G, Am, F (simple, well-known)
   - Good baseline test

2. **"Wonderwall" - Oasis**
   - Key: F# minor
   - Chords: F#m, A, E, B (simple progressions)
   - Tests minor key detection

3. **"The Girl from Ipanema"**
   - Key: Db/Eb major
   - Chords: Complex jazz with 7ths
   - Tests advanced chord detection

**Process:**
```bash
# Test each song
node test-pipeline-quality.js "https://www.youtube.com/watch?v=SONG_URL"

# Compare detected chords with known chords
# Calculate accuracy percentage
```

---

## Current System Configuration

### YouTube Downloader Settings

**File:** `backend/functions-v2/youtube-downloader-ecs/app.py`

```python
ydl_opts = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'audioquality': '192',  # 192 kbps
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
}
```

**Quality:** Should produce 192 kbps MP3 files

### Chord Detection Settings

**File:** `backend/functions-v2/chord-detector-ecs/app.py`

```python
# Audio loading
y, sr = librosa.load(audio_path, sr=22050)  # 22.05 kHz sample rate

# Chord detection
- 84 templates (7 types × 12 keys)
- Half-beat resolution
- Confidence threshold: 0.08
- Minimum duration: 0.5s

# Key detection
- Chord frequency analysis (10x weight for most common)
- Progression pattern analysis
- Combined scoring
```

---

## Expected Results

### Good Audio Quality

**Bitrate:** 192+ kbps  
**File size:** ~1.4 MB per minute  
**Sample rate:** 44.1 kHz or 48 kHz (before librosa resampling)

### Good Chord Detection

**Accuracy:** 80-90% for simple songs  
**Chord types:** Should detect all 7 types (major, minor, 7th, maj7, m7, sus4, dim)  
**Key detection:** Should match most common chord

### Red Flags

❌ **Bitrate < 128 kbps** - Audio quality too low  
❌ **All chords wrong** - Key detection failed  
❌ **Only major/minor detected** - Using old essentia detection  
❌ **Key confidence < 0.2** - Uncertain key detection  
❌ **< 20 chords for 4-min song** - Detection too conservative

---

## Troubleshooting

### Problem: Audio file not found in S3

**Error:** `NoSuchKey: The specified key does not exist`

**Causes:**
1. Job hasn't reached audio download stage yet
2. YouTube download failed
3. S3 key format changed

**Solution:**
```bash
# Check job status
aws dynamodb get-item \
  --table-name ChordScout-Jobs-V2-dev \
  --key '{"jobId": {"S": "YOUR_JOB_ID"}}' \
  --region us-east-1

# List S3 objects for job
aws s3 ls s3://chordscout-audio-temp-dev-463470937777/audio/YOUR_JOB_ID/
```

### Problem: Low bitrate MP3

**Symptom:** Bitrate < 128 kbps

**Causes:**
1. YouTube source is low quality
2. yt-dlp not getting best audio
3. FFmpeg conversion issues

**Solution:**
1. Test with different YouTube videos
2. Check yt-dlp logs in CloudWatch
3. Verify FFmpeg is installed in Docker image

### Problem: Chords all wrong but audio is good

**Symptom:** Audio quality is fine, but chords don't match

**Causes:**
1. Key detection is wrong (most likely)
2. Template matching issues
3. Using wrong detection method

**Solution:**
1. Check CloudWatch logs for: `"Using ENHANCED librosa chord detection (84 templates)"`
2. If not present, revision 9 isn't deployed
3. Verify Lambda trigger uses revision 9:
   ```bash
   aws lambda get-function-configuration \
     --function-name chordscout-v2-chord-detector-trigger-dev \
     --region us-east-1 \
     --query 'Environment.Variables.TASK_DEFINITION'
   ```

---

## Next Steps Based on Findings

### If Audio Quality is Poor

1. **Increase bitrate:**
   - Change `audioquality` from `'192'` to `'320'`
   - Rebuild and redeploy YouTube downloader

2. **Try different format:**
   - Change `format` from `'bestaudio/best'` to `'bestaudio[ext=m4a]/bestaudio'`
   - M4A often has better quality than MP3

3. **Use RapidAPI instead:**
   - Switch to RapidAPI YouTube downloader
   - May have better audio extraction

### If Chord Detection is Inaccurate

1. **Improve key detection:**
   - Increase weight for most common chord
   - Add more progression patterns
   - Use chromagram-based detection as primary

2. **Adjust thresholds:**
   - Increase confidence threshold (0.08 → 0.15)
   - Increase minimum duration (0.5s → 1.0s)
   - Reduce false positives

3. **Add more templates:**
   - Add augmented chords
   - Add 9th, 11th, 13th chords
   - Add slash chords (inversions)

4. **Try external service:**
   - Use Spotify's Basic Pitch
   - Use Chordify API
   - Use AudioKeychain API

---

## Reporting Template

After testing, report findings using this template:

```
## Test Results

**Song:** [Song name]
**YouTube URL:** [URL]
**Job ID:** [Job ID]

### Audio Quality
- Bitrate: [X kbps]
- File size: [X MB]
- Duration: [X seconds]
- Quality assessment: [Good/Medium/Poor]
- Issues: [Any audio issues noticed]

### Manual Chord Identification
- Key: [Your assessment]
- First 10 chords: [List chords you hear]
- Chord types heard: [major, minor, 7th, etc.]

### Detected Results
- Key: [Detected key]
- Key confidence: [X]
- First 10 chords: [List detected chords]
- Chord types detected: [List types]
- Model: [Model identifier]

### Comparison
- Key match: [Yes/No]
- Chord accuracy: [X%]
- Issues identified: [List specific issues]

### Conclusion
[Audio quality issue / Chord detection issue / Key detection issue]

### Recommended Fix
[Specific recommendation]
```

---

## Summary

**Use these tools to:**
1. ✅ Download and inspect MP3 files
2. ✅ Verify audio quality
3. ✅ Compare detected vs actual chords
4. ✅ Identify root cause of inaccuracy

**The goal:**
- Isolate whether the problem is audio quality or chord detection
- Provide concrete examples of what's wrong
- Guide improvements to the right part of the pipeline

---

**Start with:** `node download-job-audio.js YOUR_RECENT_JOB_ID`

This will download the MP3 so you can listen and compare!
