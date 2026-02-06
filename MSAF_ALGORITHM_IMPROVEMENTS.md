# MSAF Algorithm Improvements

**Date:** February 5, 2026  
**Status:** ✅ Implemented and building

---

## Problem

MSAF with single algorithm (CNMF) wasn't detecting segments well:
- Sometimes too few segments (1-2)
- Sometimes too many segments (50+)
- Not adapting to different music styles
- No fallback if algorithm failed

---

## Solution

Implemented **multi-algorithm fallback chain** with quality validation.

### Algorithm Chain

Tries algorithms in order until one succeeds:

1. **sf (Spectral Clustering)** - Best for pop/rock
   - Uses spectral features
   - Good for clear section boundaries
   - Fast and reliable

2. **foote (Foote Novelty)** - Fast and reliable
   - Novelty-based detection
   - Works across genres
   - Computationally efficient

3. **olda (Online Learning)** - Good for varied music
   - Adaptive algorithm
   - Handles complex structures
   - Uses CQT features

4. **cnmf (CNN)** - Deep learning based
   - Most sophisticated
   - Slowest to compute
   - Last resort fallback

### Quality Validation

Each algorithm's results are validated:

```python
# Too few segments
if num_segments < 2:
    continue  # Try next algorithm

# Too many segments
if num_segments > 50:
    continue  # Try next algorithm

# Reasonable range (3-20)
if 3 <= num_segments <= 20:
    return segments  # Success!
```

### Final Fallback

If all MSAF algorithms fail or return poor results:
- Falls back to pattern-based detection
- Uses chord progression patterns
- Always returns something useful

---

## How It Works

### 1. Try Each Algorithm

```python
algorithms = [
    ('sf', 'scluster', 'mfcc'),      # Spectral clustering
    ('foote', 'fmc2d', 'mfcc'),      # Foote novelty
    ('olda', 'scluster', 'cqt'),     # Online learning
    ('cnmf', 'cnmf', 'mfcc'),        # CNN
]

for boundaries_id, labels_id, feature in algorithms:
    try:
        boundaries, labels = msaf.process(
            audio_path,
            boundaries_id=boundaries_id,
            labels_id=labels_id,
            feature=feature
        )
        
        # Validate results
        if is_valid(boundaries, labels):
            return convert_to_segments(boundaries, labels)
    except:
        continue  # Try next algorithm
```

### 2. Validate Results

```python
num_segments = len(boundaries) - 1

# Check segment count
if num_segments < 2:
    log("Too few segments, trying next algorithm")
    continue

if num_segments > 50:
    log("Too many segments, trying next algorithm")
    continue

# Success!
return segments
```

### 3. Track Algorithm Used

```python
segment = {
    'start': 0.0,
    'end': 23.5,
    'label': 'A',
    'duration': 23.5,
    'algorithm': 'sf'  # Track which algorithm worked
}
```

---

## Expected Improvements

### Before (Single Algorithm)

```
MSAF detected 1 segment
  A: 0.0s - 371.0s (entire song)
  
⚠️ Only 1 segment, falling back to pattern-based
```

**Issues:**
- No useful segmentation
- Always falling back
- Not adapting to music style

### After (Multi-Algorithm)

```
Trying algorithm: sf with mfcc features...
✓ sf detected 6 segments

Segments:
  A: 0.0s - 8.3s (intro)
  B: 8.3s - 32.1s (verse)
  B: 32.1s - 48.7s (verse)
  A: 48.7s - 70.2s (intro)
  C: 70.2s - 95.8s (bridge)
  B: 95.8s - 120.5s (verse)

Label distribution: {'B': 3, 'A': 2, 'C': 1}
✓ Using MSAF audio-based segmentation: 6 segments
Algorithm: sf
```

**Benefits:**
- ✅ Reasonable segment count
- ✅ Identifies repeated sections (B appears 3 times)
- ✅ Clear boundaries
- ✅ Tracks which algorithm worked

---

## Algorithm Characteristics

### Spectral Clustering (sf)

**Best for:** Pop, rock, electronic music  
**Speed:** Fast  
**Accuracy:** High for clear boundaries  
**Features:** MFCC

**When it works well:**
- Clear verse/chorus structure
- Distinct instrumentation changes
- Pop/rock arrangements

### Foote Novelty (foote)

**Best for:** General purpose  
**Speed:** Very fast  
**Accuracy:** Good across genres  
**Features:** MFCC

**When it works well:**
- Any music with section changes
- Reliable fallback
- Computationally efficient

### Online Learning (olda)

**Best for:** Complex, varied music  
**Speed:** Medium  
**Accuracy:** Good for non-standard structures  
**Features:** CQT

**When it works well:**
- Progressive rock
- Jazz
- Classical
- Non-standard structures

### CNN (cnmf)

**Best for:** Deep learning approach  
**Speed:** Slow  
**Accuracy:** High when it works  
**Features:** MFCC

**When it works well:**
- Complex arrangements
- When other methods fail
- Has training data for genre

---

## Testing

### Test with Different Songs

**Pop/Rock (Clear Structure):**
- Expected: sf or foote succeeds
- Segments: 4-8
- Clear verse/chorus

**Jazz/Complex:**
- Expected: olda or cnmf succeeds
- Segments: 6-12
- More varied structure

**Simple Songs:**
- Expected: Any algorithm works
- Segments: 3-5
- Basic structure

### Check Logs

Look for:
```
Trying algorithm: sf with mfcc features...
✓ sf detected 6 segments
✓ Using MSAF audio-based segmentation: 6 segments
Algorithm: sf
```

Or fallback:
```
Trying algorithm: sf with mfcc features...
⚠️ Only 1 segment(s) detected, trying next algorithm...
Trying algorithm: foote with mfcc features...
✓ foote detected 5 segments
```

---

## Fallback Behavior

### MSAF Success (3-20 segments)
```
✓ Using MSAF audio-based segmentation: 6 segments
Algorithm: sf
```

### MSAF Out of Range
```
⚠️ MSAF returned 2 segments (outside 3-20 range), using pattern-based
✓ Using pattern-based structure detection: 4 sections
```

### MSAF Failed
```
All MSAF algorithms failed, falling back to pattern-based
✓ Using pattern-based structure detection: 4 sections
```

---

## Benefits

### 1. Robustness
- Multiple algorithms = higher success rate
- Automatic fallback chain
- Always returns useful results

### 2. Adaptability
- Different algorithms for different music
- Tries best algorithm first
- Falls back to simpler methods

### 3. Quality Control
- Validates segment count
- Rejects poor results
- Uses pattern-based as safety net

### 4. Transparency
- Logs which algorithm succeeded
- Tracks algorithm in segment data
- Easy to debug

---

## Next Steps

### If Still Not Working Well

1. **Adjust segment count range**
   - Currently: 3-20
   - Could try: 2-15 or 4-25

2. **Try different feature combinations**
   - MFCC (current)
   - CQT (harmonic content)
   - Tempogram (rhythm-based)

3. **Hybrid approach**
   - Use MSAF for boundaries
   - Use patterns for labeling
   - Combine both signals

4. **Manual tuning**
   - Add genre detection
   - Adjust per genre
   - Custom thresholds

---

## Summary

**Problem:** Single MSAF algorithm not working well  
**Solution:** Multi-algorithm fallback chain with validation

**Improvements:**
- ✅ 4 algorithms tried automatically
- ✅ Quality validation (3-20 segments)
- ✅ Pattern-based fallback
- ✅ Algorithm tracking

**Status:** Building in GitHub Actions

**Next:** Test with real songs and see which algorithms work best!

---

**This should significantly improve segmentation quality!** The system will now try multiple approaches and use the best one that works.
