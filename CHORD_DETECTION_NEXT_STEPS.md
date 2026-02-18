# Chord Detection - Next Steps & Improvements

## Current Status

✅ **Working**: Simple template matching with median filtering
- Detecting ~1000 chords for 3.5-minute song
- Average chord duration: 0.20s
- Key detection: C# major (correct!)
- Processing speed: 2.0x realtime

## Issues to Address

### 1. Tempo-Dependent Processing ⚠️

**Problem**: Current approach uses fixed parameters regardless of tempo

**Current**:
- 20ms hop length for chromagram (fixed)
- 16th-note subdivisions (fixed)
- Median filter window=3 (fixed)

**Should be**:
- Faster songs (>140 BPM): Might need coarser resolution
- Slower songs (<80 BPM): Could use finer resolution
- Very fast songs (>180 BPM): 16th notes might be too fine

**Solution**:
```python
if tempo < 80:
    # Slow ballad - use 32nd notes
    subdivision_level = 8
    hop_length_ms = 10
elif tempo < 140:
    # Normal tempo - use 16th notes
    subdivision_level = 4
    hop_length_ms = 20
else:
    # Fast tempo - use 8th notes
    subdivision_level = 2
    hop_length_ms = 30
```

### 2. Downbeat Alignment ⚠️

**Current Status**:
- First beat detected at 0.720s (720ms into song)
- Only 0.24% of audio energy before first beat
- Beat intervals are consistent (std = 0.011s)

**Analysis**:
- ✓ Beat tracking is working correctly
- ✓ Minimal audio before first beat (likely silence/intro)
- ⚠️ First beat might not be measure downbeat (could be beat 2, 3, or 4)

**Problem**: 
Librosa's `beat_track()` finds beats but doesn't identify which is the downbeat (measure start). We're assuming the first beat is beat 1 of measure 1, but it could be any beat.

**Solutions**:

1. **Use Essentia's BeatTracker with downbeat detection**:
```python
import essentia.standard as es

# This can detect downbeats (measure starts)
beat_tracker = es.BeatTrackerMultiFeature()
beats, confidence = beat_tracker(audio)

# Or use RhythmExtractor2013 which includes downbeat detection
rhythm = es.RhythmExtractor2013()
bpm, beats, beats_confidence, estimates, beats_intervals = rhythm(audio)
```

2. **Manual downbeat detection using onset strength**:
```python
# Detect strong beats (likely downbeats)
onset_env = librosa.onset.onset_strength(y=y, sr=sr)
# Find peaks that are significantly stronger (downbeats)
downbeats = librosa.util.peak_pick(onset_env, ...)
```

3. **User confirmation**:
- Play first few seconds with click track
- Ask user: "Does the click align with the beat?"
- Allow manual offset adjustment

### 3. Too Many Chord Changes 🎵

**Current**: 1005 chords in 206s = 4.9 chords/second

**Analysis**:
Looking at the beat view, we see rapid changes like:
```
Beat:    1     2     3     4     5     6     7     8
Chord:   -     -   Em7  D#m7 A#sus  D#m7 Bmaj7  A#m7
```

This is 6 different chords in 8 beats (2 measures). That's very fast!

**Possible Causes**:
1. **Noise in chroma**: Even with stem separation, some noise remains
2. **Passing chords**: Brief transitional chords that aren't musically significant
3. **Enharmonic confusion**: D#m7 vs E♭m7 being detected as different
4. **Over-sensitivity**: Median filter (window=3) might not be enough

**Solutions**:

1. **Increase median filter window**:
```python
# Try window=5 or window=7 for more smoothing
filtered_sequence = apply_median_filter_to_chords(chord_sequence, window=5)
```

2. **Add minimum duration filter** (but smarter):
```python
# Remove chords shorter than 1/8 note (but keep if high confidence)
if chord_duration < eighth_note_duration and confidence < 0.7:
    merge_with_neighbor()
```

3. **Confidence thresholding**:
```python
# Only keep chords with confidence > threshold
if confidence < 0.6:
    use_previous_chord()
```

4. **Chord simplification**:
```python
# Group similar chords
# Fmaj7, F6, Fsus4 → F
# D#m7, D#m6, D#m → D#m
```

### 4. Sheet Music Visualization 📄

**Quick Options** (no full PDF):

1. **Text-based chord chart** (already implemented):
```
Measure:    1           2           3           4
Time:       00:00.72    00:01.16    00:01.60    00:02.04
Chords:     D#m7        Fmaj7       G#maj7      Fm7
```

2. **ASCII art with bar lines**:
```
| D#m7  Fmaj7 | G#maj7  Fm7 | D#m7  Fmaj7 | G#maj7  Fm7 |
```

3. **Simple HTML/CSS**:
```html
<div class="measure">
  <div class="chord">D#m7</div>
  <div class="chord">Fmaj7</div>
</div>
```

4. **LilyPond format** (can render to PDF):
```lilypond
\chordmode {
  d:m7 f:maj7 gis:maj7 f:m7
}
```

5. **MusicXML** (can open in MuseScore, Finale, etc.):
```xml
<harmony>
  <root><root-step>D</root-step><root-alter>1</root-alter></root>
  <kind>minor-seventh</kind>
</harmony>
```

**Recommendation**: Start with LilyPond or MusicXML since they can be rendered to professional sheet music.

## Immediate Action Items

### Priority 1: Reduce Chord Noise
1. Increase median filter window to 5 or 7
2. Add confidence threshold (>0.6)
3. Add minimum duration (1/8 note for chords <0.6 confidence)
4. Test with "That's What I Like"

### Priority 2: Verify Downbeat Alignment
1. Implement Essentia downbeat detection
2. Create diagnostic that plays audio with click track
3. Allow manual offset adjustment
4. Test with multiple songs

### Priority 3: Tempo-Dependent Parameters
1. Add tempo-based subdivision selection
2. Adjust hop length based on tempo
3. Adjust median filter window based on tempo
4. Test with slow (60 BPM) and fast (180 BPM) songs

### Priority 4: Sheet Music Export
1. Implement LilyPond export
2. Create simple chord chart renderer
3. Add measure numbers and bar lines
4. Test rendering

## Testing Plan

### Test Songs Needed:
1. **Slow ballad** (60-80 BPM): Test slow tempo handling
2. **Fast dance** (140-180 BPM): Test fast tempo handling
3. **Jazz standard** (100-120 BPM): Test complex harmony
4. **Simple pop** (120 BPM): Test basic progressions

### Validation Criteria:
- Chord count should be reasonable (not 1000+ for 3-minute song)
- Average chord duration should be 1-4 seconds for pop
- Key detection should be accurate
- Downbeat should align with actual measure starts
- Chord progression should make musical sense

## Code Changes Needed

### File: `chord_detection_v2.py`

1. Add tempo-dependent parameters:
```python
def get_analysis_parameters(tempo: float) -> dict:
    """Get optimal parameters based on tempo"""
    if tempo < 80:
        return {
            'subdivision_level': 8,  # 32nd notes
            'hop_length_ms': 10,
            'median_window': 7
        }
    elif tempo < 140:
        return {
            'subdivision_level': 4,  # 16th notes
            'hop_length_ms': 20,
            'median_window': 5
        }
    else:
        return {
            'subdivision_level': 2,  # 8th notes
            'hop_length_ms': 30,
            'median_window': 3
        }
```

2. Add confidence filtering:
```python
def filter_low_confidence_chords(
    chord_sequence: List[str],
    confidences: List[float],
    threshold: float = 0.6
) -> List[str]:
    """Replace low-confidence chords with previous high-confidence chord"""
    filtered = []
    last_good_chord = chord_sequence[0]
    
    for chord, conf in zip(chord_sequence, confidences):
        if conf >= threshold:
            filtered.append(chord)
            last_good_chord = chord
        else:
            filtered.append(last_good_chord)
    
    return filtered
```

3. Add downbeat detection:
```python
def detect_downbeats(audio_path: str) -> np.ndarray:
    """Detect measure downbeats using Essentia"""
    import essentia.standard as es
    
    loader = es.MonoLoader(filename=audio_path, sampleRate=44100)
    audio = loader()
    
    # Use RhythmExtractor with downbeat detection
    rhythm = es.RhythmExtractor2013()
    bpm, beats, confidence, estimates, intervals = rhythm(audio)
    
    # Identify downbeats (every 4th beat for 4/4 time)
    # This is simplified - real implementation needs beat strength analysis
    downbeats = beats[::4]
    
    return downbeats
```

## Next Session Goals

1. Implement confidence filtering
2. Increase median filter window
3. Test with adjusted parameters
4. Create LilyPond export
5. Verify downbeat alignment with click track

