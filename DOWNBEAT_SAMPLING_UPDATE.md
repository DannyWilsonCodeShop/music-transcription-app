# Downbeat-Only Sampling Update

## Change Summary

**Previous Approach**: Half-beat sampling
- Analyzed chords at every beat AND midpoint between beats
- ~2x more analysis points
- Captured passing tones and non-chord tones
- More temporal resolution but noisier results

**New Approach**: Downbeat-only sampling
- Analyzes chords ONLY at first beat of each measure
- Reduces analysis points by 4x (in 4/4 time)
- Focuses on strong beats where chord changes typically occur
- Cleaner signal, less noise from passing tones

---

## How It Works

### 1. Time Signature Detection
```
4/4 time → 4 beats per measure → sample every 4th beat
3/4 time → 3 beats per measure → sample every 3rd beat
6/8 time → 2 beats per measure → sample every 2nd beat
```

### 2. Downbeat Extraction
```python
# Example: 4/4 time with 100 beats
beats = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, ...]
downbeats = [0.0, 2.0, 4.0, 6.0, ...]  # Every 4th beat
```

### 3. Chord Analysis
- For each downbeat:
  - Extract chromagram at that position
  - Extract bass chromagram at that position
  - Combine with 2:1 bass weighting
  - Match against 84 chord templates
  - Select best match

### 4. Consolidation
- Merge consecutive identical chords
- Calculate duration for each chord
- Filter out very short chords (<0.5s)

---

## Benefits

### 1. Reduced Noise
- Passing tones occur between beats
- Non-chord tones are less prominent on downbeats
- Cleaner harmonic content on strong beats

### 2. Better Accuracy
- Chord changes typically happen on downbeats
- Musicians emphasize downbeats
- Bass notes are clearest on downbeats

### 3. Faster Processing
- 4x fewer analysis points (in 4/4)
- Faster chord detection
- Less data to consolidate

### 4. More Musical
- Aligns with how musicians think about harmony
- Matches typical chord change patterns
- Better for transcription purposes

---

## Example Comparison

### Before (Half-beat sampling)
```
Song: 4/4 time, 120 BPM, 3 minutes
Beats: 360 beats
Analysis points: 720 (every half-beat)
Detected chords: 250 (many short, noisy chords)
```

### After (Downbeat sampling)
```
Song: 4/4 time, 120 BPM, 3 minutes
Beats: 360 beats
Analysis points: 90 (every 4th beat = downbeats)
Detected chords: 80 (cleaner, more stable chords)
```

---

## Logging Output

You'll now see:
```
Detecting chord changes (downbeat-synchronized with enhanced templates)...
  Time signature: 4/4 (4 beats per measure)
  Total beats: 360
  Downbeats (first beat of each measure): 90
  Sampling strategy: DOWNBEAT-ONLY (reduces noise from passing tones)
  Analyzing at 90 downbeat positions
  Detected 85 chords at downbeat positions
  Consolidating consecutive identical chords...
  Final chord count: 78
```

---

## Trade-offs

### Advantages ✅
- Cleaner chord detection
- Less noise from passing tones
- Faster processing
- More musically meaningful
- Better for key detection

### Disadvantages ⚠️
- Might miss very fast chord changes (within a measure)
- Less temporal resolution
- Could miss syncopated chord changes

### When This Works Best
- Standard pop, rock, country, R&B
- Songs with chord changes on downbeats
- 4/4 or 3/4 time signatures
- Clear harmonic structure

### When This Might Struggle
- Jazz with rapid chord changes
- Highly syncopated music
- Chord changes on off-beats
- Complex polyrhythmic music

---

## Testing

Upload a file and check the logs:
```bash
aws logs tail /ecs/music-transcription-chord-detection \
  --since 5m \
  --profile production \
  --format short | grep -A 10 "downbeat"
```

You should see:
1. Time signature detected
2. Number of downbeats extracted
3. Sampling strategy explanation
4. Fewer but cleaner chords detected

---

## Next Steps

1. ✅ Downbeat sampling implemented
2. 🎯 Test with your E minor/G major song
3. 📊 Compare chord accuracy
4. 🔧 Adjust if needed (could try every 2 beats instead of 4)

---

**Status**: DEPLOYED  
**Docker Image**: Built and pushed  
**Ready for Testing**: YES
