# Data Quality Issues - Analysis & Action Plan

## Issues Identified

### 1. ❌ Lyrics Start Too Late
**Problem:** Deepgram detected lyrics starting at 161.81s (2:41), but actual lyrics start at ~16s  
**Impact:** Missing first 2+ minutes of lyrics  
**Root Cause:** Deepgram may have detected silence/instrumental intro incorrectly

### 2. ❌ Lyrics End with "..."
**Problem:** Lyrics are truncated and don't finish  
**Impact:** Incomplete transcription  
**Root Cause:** Unknown - need to check Deepgram response

### 3. ❌ Syllables Not Divided
**Problem:** Syllables not properly segmented  
**Impact:** Poor alignment with chords  
**Root Cause:** Need to verify syllable extraction logic

### 4. ❌ Wrong Key Detection
**Problem:** Key detected as G, but actual key is different  
**Impact:** Incorrect Nashville numbers  
**Root Cause:** Simple chromagram-based detection without stem separation

### 5. ❌ Tempo Hardcoded to 120 BPM
**Problem:** Tempo always shows 120 BPM regardless of actual tempo  
**Impact:** Inaccurate tempo information  
**Root Cause:** Tempo not being detected/calculated

### 6. ❌ Wrong Chords
**Problem:** Chord detection inaccurate  
**Impact:** Incorrect chord sheet  
**Root Cause:** Simple peak detection without stem separation

### 7. ❌ Lyrics Show at "Verse 17"
**Problem:** PDF layout shows lyrics starting at wrong verse number  
**Impact:** Confusing presentation  
**Root Cause:** Measure calculation based on wrong start time

---

## Root Cause Analysis

### Deepgram Transcription Issue

**What Deepgram Returned:**
```json
{
  "transcript": "Now you're sitting next to someone tonight...",
  "words": [
    {
      "word": "now",
      "start": 161.81,  // ❌ Should be ~16s
      "end": 162.12999,
      "confidence": 0.23474017
    }
  ]
}
```

**Possible Causes:**
1. **Audio file issue:** The MP3 might have metadata/padding that shifts timestamps
2. **Deepgram VAD (Voice Activity Detection):** May have detected silence for first 2 minutes
3. **Audio quality:** Poor quality in first 2 minutes causing Deepgram to skip
4. **Deepgram bug:** Timestamp offset issue

### Chord Detection Issues

**Current Method:**
- Simple chromagram analysis
- Peak detection in chroma energy
- No stem separation (disabled for performance)
- No tempo detection
- Basic key detection from overall chroma

**Why It's Inaccurate:**
- Drums and vocals interfere with chord detection
- No harmonic isolation
- Simple peak detection misses chord changes
- No beat/tempo analysis

---

## Immediate Actions

### Action 1: Debug Deepgram Timestamp Issue

**Test 1: Check Audio File**
```bash
# Download the audio file and check duration/metadata
aws s3 cp s3://chordscout-audio-temp-dev-090130568474/audio/c3ab9fe9-b43d-408a-9a04-5aef7fcf59c9.mp3 /tmp/test.mp3 --profile chordscout

# Check with ffprobe
ffprobe -v quiet -print_format json -show_format -show_streams /tmp/test.mp3
```

**Test 2: Manual Deepgram Test**
```bash
# Send audio directly to Deepgram and check timestamps
curl -X POST "https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true&word_timestamps=true" \
  -H "Authorization: Token $DEEPGRAM_API_KEY" \
  -H "Content-Type: audio/mpeg" \
  --data-binary @/tmp/test.mp3 \
  | jq '.results.channels[0].alternatives[0].words[0:5]'
```

**Test 3: Check YouTube Source**
```bash
# Verify the YouTube video timestamps
# URL: https://www.youtube.com/watch?v=Q-RKhgsZu64
# Listen at 16s and 161s to confirm where lyrics actually start
```

### Action 2: Fix Tempo Detection

**Add Tempo Detection to Chord Detector:**
```python
def detect_tempo(y, sr):
    """Detect tempo using librosa beat tracking"""
    import librosa
    
    # Detect tempo
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    
    log(f"Tempo detected: {tempo:.1f} BPM")
    log(f"Beats detected: {len(beats)}")
    
    return float(tempo)
```

**Update in `app.py`:**
```python
# After loading audio
tempo = detect_tempo(y, sr)

# Include in chords_data
return {
    'chords': chords,
    'key': key,
    'duration': round(duration, 2),
    'totalChords': len(chords),
    'tempo': round(tempo, 1),  # ADD THIS
    'model': 'librosa-chromagram'
}
```

### Action 3: Improve Key Detection

**Better Key Detection:**
```python
def detect_key_improved(chroma, sr):
    """Improved key detection using Krumhansl-Schmuckler algorithm"""
    import numpy as np
    
    # Krumhansl-Schmuckler key profiles
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    
    # Average chroma over time
    chroma_mean = np.mean(chroma, axis=1)
    
    # Normalize
    chroma_mean = chroma_mean / np.sum(chroma_mean)
    
    # Calculate correlation with each key
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    best_corr = -1
    best_key = 'C'
    best_mode = 'major'
    
    for i in range(12):
        # Rotate profiles
        major_rot = np.roll(major_profile, i)
        minor_rot = np.roll(minor_profile, i)
        
        # Calculate correlation
        major_corr = np.corrcoef(chroma_mean, major_rot)[0, 1]
        minor_corr = np.corrcoef(chroma_mean, minor_rot)[0, 1]
        
        if major_corr > best_corr:
            best_corr = major_corr
            best_key = chord_names[i]
            best_mode = 'major'
        
        if minor_corr > best_corr:
            best_corr = minor_corr
            best_key = chord_names[i] + 'm'
            best_mode = 'minor'
    
    return best_key, best_mode, best_corr
```

### Action 4: Fix Deepgram Timestamp Offset

**Option A: Adjust Timestamps in Post-Processing**
```javascript
// In lyrics-transcriber/index.js
function adjustTimestamps(words, expectedStartTime = 0) {
  if (words.length === 0) return words;
  
  // Check if first word starts much later than expected
  const firstWordStart = words[0].start;
  const offset = firstWordStart - expectedStartTime;
  
  // If offset is > 10 seconds, likely a timestamp issue
  if (offset > 10) {
    console.log(`⚠️ Detected timestamp offset: ${offset}s`);
    console.log(`Adjusting all timestamps by -${offset}s`);
    
    return words.map(word => ({
      ...word,
      start: Math.max(0, word.start - offset),
      end: Math.max(0, word.end - offset)
    }));
  }
  
  return words;
}
```

**Option B: Use Deepgram's `detect_language` and `diarize` Features**
```javascript
const params = new URLSearchParams({
  model: 'nova-3',
  smart_format: 'true',
  punctuate: 'true',
  detect_language: 'true',  // Better language detection
  diarize: 'false',
  word_timestamps: 'true',
  syllable_timestamps: 'true',
  vad_turnoff: '0.5'  // Adjust Voice Activity Detection threshold
});
```

### Action 5: Re-enable Stem Separation (Optimized)

**Problem:** Chord detection is inaccurate without stem separation  
**Solution:** Re-enable with optimizations

**Option A: Use Lighter Model + Larger Chunks**
```python
# In app.py
CHUNK_DURATION = 60  # 60-second chunks instead of 30
self.demucs_model = get_model('mdx')  # Even lighter than mdx_extra
```

**Option B: Skip Stem Separation for Short Songs**
```python
if duration < 180:  # Less than 3 minutes
    log("Short song detected, skipping stem separation for speed")
    y, sr = librosa.load(audio_path, sr=22050)
else:
    log("Using stem separation for better accuracy")
    y, sr = detector.separate_harmonic_stem_chunked(audio_path)
```

**Option C: Use Spleeter Instead of Demucs**
```python
# Faster, lighter alternative
from spleeter.separator import Separator

separator = Separator('spleeter:2stems')  # Just vocals/accompaniment
prediction = separator.separate(audio_path)
harmonic = prediction['accompaniment']  # Use accompaniment for chords
```

---

## Testing Plan

### Test 1: Verify Audio File
```bash
# Download and inspect
aws s3 cp s3://chordscout-audio-temp-dev-090130568474/audio/c3ab9fe9-b43d-408a-9a04-5aef7fcf59c9.mp3 /tmp/test.mp3 --profile chordscout

# Check duration
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 /tmp/test.mp3

# Play first 30 seconds to verify lyrics start at ~16s
ffplay -t 30 /tmp/test.mp3
```

### Test 2: Manual Deepgram Test
```bash
# Test with different parameters
curl -X POST "https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true&word_timestamps=true&vad_turnoff=0.1" \
  -H "Authorization: Token $DEEPGRAM_API_KEY" \
  -H "Content-Type: audio/mpeg" \
  --data-binary @/tmp/test.mp3 \
  > deepgram-response.json

# Check first word timestamp
jq '.results.channels[0].alternatives[0].words[0]' deepgram-response.json
```

### Test 3: Test Tempo Detection Locally
```python
import librosa
import numpy as np

# Load audio
y, sr = librosa.load('/tmp/test.mp3', sr=22050)

# Detect tempo
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
print(f"Tempo: {tempo:.1f} BPM")
print(f"Beats: {len(beats)}")

# Detect key
chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
chroma_mean = np.mean(chroma, axis=1)
key_index = np.argmax(chroma_mean)
keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
print(f"Key: {keys[key_index]}")
```

---

## Priority Order

### P0 (Critical - Fix Now)
1. **Debug Deepgram timestamp issue** - Lyrics starting at wrong time
2. **Add tempo detection** - Currently hardcoded to 120 BPM
3. **Fix lyrics truncation** - Ending with "..."

### P1 (High - Fix This Week)
4. **Improve key detection** - Using better algorithm
5. **Re-enable stem separation** - With optimizations for speed
6. **Fix chord detection accuracy** - Better algorithm or stem separation

### P2 (Medium - Fix Next Week)
7. **Improve syllable segmentation** - Better alignment
8. **Fix verse numbering** - Based on correct timestamps
9. **Add confidence scores** - Show accuracy metrics

---

## Expected Outcomes

### After Fixes:
- ✅ Lyrics start at correct time (~16s)
- ✅ Complete lyrics (no truncation)
- ✅ Accurate tempo detection
- ✅ Better key detection
- ✅ More accurate chords (with stem separation)
- ✅ Proper syllable alignment
- ✅ Correct verse numbering

---

## Next Steps

1. **Investigate audio file** - Download and verify timestamps
2. **Test Deepgram directly** - Rule out API issues
3. **Implement tempo detection** - Quick win
4. **Fix timestamp offset** - If confirmed
5. **Re-enable stem separation** - With optimizations
6. **Test end-to-end** - Verify all fixes work together

---

**Status: INVESTIGATION REQUIRED**

The system is working (job completes), but data quality needs significant improvement.
