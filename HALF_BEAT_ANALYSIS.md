# Half-Beat Analysis & Multi-Measure Patterns

**Date:** February 5, 2026  
**Status:** ⏳ Building in GitHub Actions

---

## Problem Identified

The pattern detection was finding useless patterns like:
- **F → F → F** (3 chords, all the same)
- **C → C → C** (3 chords, all the same)

This happened because:
1. **Too few analysis points** - Only analyzing at beat positions missed chord changes between beats
2. **Too short patterns** - Looking for 3-8 chord patterns often captured just 1 measure
3. **Single-measure patterns** - Not meaningful for identifying verse/chorus structures

---

## Solution Implemented

### 1. Half-Beat Analysis (2x Temporal Resolution)

**Before:**
```python
# Analyze only at beat positions
beat_frames = librosa.time_to_frames(beats, sr=sr, hop_length=2048)
# Result: ~76 analysis points for 371s song (one per beat)
```

**After:**
```python
# Generate half-beat positions
half_beat_times = []
for i in range(len(beat_times) - 1):
    half_beat_times.append(beat_times[i])
    # Add midpoint between this beat and next
    half_beat_times.append((beat_times[i] + beat_times[i + 1]) / 2)

# Result: ~152 analysis points for 371s song (two per beat)
```

**Benefits:**
- ✅ Captures chord changes that happen between beats
- ✅ Better temporal resolution for fast progressions
- ✅ More accurate chord timing
- ✅ Detects syncopated chord changes

### 2. Multi-Measure Pattern Detection

**Before:**
```python
for pattern_length in range(3, 9):  # 3-8 chords
    # Often just 1 measure in 4/4 time
    # Example: F → F → F (not useful)
```

**After:**
```python
for pattern_length in range(6, 17):  # 6-16 chords
    # 1.5 to 4 measures
    # Example: F → Dm → Gm → C → F → Dm → Gm → C (useful!)
```

**Why 6-16 chords?**
- **6 chords minimum** = ~1.5 measures
  - Captures meaningful progressions
  - Avoids single-chord repetitions
- **16 chords maximum** = ~4 measures
  - Typical verse/chorus length
  - Not too long to find repetitions

**Benefits:**
- ✅ Focuses on multi-measure progressions
- ✅ Avoids detecting F-F-F as a pattern
- ✅ Better for identifying verse/chorus structures
- ✅ More musically meaningful patterns

---

## Expected Results

### Before (Beat Analysis, Short Patterns)

**Analysis Points:** ~76 (one per beat)  
**Pattern Length:** 3-8 chords (often 1 measure)

**Patterns Found:**
```
Pattern 1: F → F → F (not useful)
Pattern 2: C → C → C (not useful)
Pattern 3: C → F → C (too short)
```

**Issues:**
- ❌ Missing chord changes between beats
- ❌ Patterns too short to be meaningful
- ❌ Single-chord repetitions detected as patterns

### After (Half-Beat Analysis, Multi-Measure Patterns)

**Analysis Points:** ~152 (two per beat)  
**Pattern Length:** 6-16 chords (1.5-4 measures)

**Expected Patterns:**
```
Pattern 1: F → Dm → Gm → C → F → Dm → Gm → C (2 measures, useful!)
Pattern 2: F → Dm → Gm → C → Bb → C → F → Dm (2 measures, useful!)
Pattern 3: Dm → Gm → C → F → Dm → Gm (1.5 measures, useful!)
```

**Benefits:**
- ✅ Captures all chord changes
- ✅ Patterns are musically meaningful
- ✅ Better verse/chorus identification
- ✅ More accurate progressions

---

## Technical Details

### Half-Beat Generation

```python
# For each pair of consecutive beats
beat_times = [0.0, 0.8, 1.6, 2.4, 3.2, ...]

# Generate half-beats
half_beat_times = [
    0.0,           # Beat 1
    0.4,           # Half-beat (midpoint)
    0.8,           # Beat 2
    1.2,           # Half-beat (midpoint)
    1.6,           # Beat 3
    2.0,           # Half-beat (midpoint)
    ...
]
```

### Pattern Length Calculation

**In 4/4 time at 76 BPM:**
- 1 beat = ~0.79 seconds
- 1 measure = 4 beats = ~3.16 seconds
- With half-beat analysis: 8 analysis points per measure

**After consolidation:**
- Typical: 2-4 unique chords per measure
- 2 measures: 4-8 unique chords
- 3 measures: 6-12 unique chords
- 4 measures: 8-16 unique chords

**Pattern range 6-16 chords = 1.5 to 4 measures** ✅

---

## Example: "Like The Dew" (F major, 76 BPM)

### Before

**Total Chords:** 48  
**Analysis Points:** ~76 beats

**Pattern 1:**
```
F → F → F (3 chords, 1 measure)
Occurrences: 5 times
```

**Problem:** This is just one chord held for a measure, not a progression.

### After (Expected)

**Total Chords:** ~80-100 (more from half-beat analysis)  
**Analysis Points:** ~152 half-beats

**Pattern 1:**
```
F → Dm → Gm → C → F → Dm → Gm → C (8 chords, 2 measures)
Occurrences: 4 times
Roman: I → vi → ii → V → I → vi → ii → V
```

**Benefit:** This is the actual verse/chorus progression!

---

## Impact on Pattern Detection

### Minimum Pattern Length

**Old:** 3 chords  
**New:** 6 chords

**Why:** Avoids single-chord repetitions like F-F-F

### Maximum Pattern Length

**Old:** 8 chords  
**New:** 16 chords

**Why:** Captures full verse/chorus sections (2-4 measures)

### Pattern Repetition Requirement

**Unchanged:** Still requires 2+ occurrences

**Why:** Only patterns that repeat are meaningful for structure detection

---

## Testing

Once the build completes, test with:

```bash
# Submit new job
curl -X POST https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev/jobs \
  -H "Content-Type: application/json" \
  -d '{"youtubeUrl": "https://www.youtube.com/watch?v=Q-RKhgsZu64"}'
```

### What to Look For

**Chord Count:**
- Should increase from 48 to ~80-100
- More chords due to half-beat analysis

**Pattern Quality:**
- No more F-F-F patterns
- Patterns should be 6-16 chords long
- Should see actual progressions like F → Dm → Gm → C

**Pattern Examples:**
```
✅ GOOD: F → Dm → Gm → C → F → Dm → Gm → C (8 chords, 2 measures)
✅ GOOD: Dm → Gm → C → F → Dm → Gm (6 chords, 1.5 measures)
❌ BAD:  F → F → F (3 chords, not a progression)
❌ BAD:  C → C (2 chords, too short)
```

---

## Summary

**Changes:**
1. ✅ Half-beat analysis (2x temporal resolution)
2. ✅ Multi-measure patterns (6-16 chords instead of 3-8)

**Benefits:**
- More accurate chord detection
- Better temporal resolution
- Musically meaningful patterns
- Better verse/chorus identification
- No more single-chord "patterns"

**Status:** Building in GitHub Actions  
**ETA:** 3-5 minutes

---

**Build Status:** https://github.com/DannyWilsonCodeShop/music-transcription-app/actions
