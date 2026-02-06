# Bass Note Support for Nashville Number System

**Date:** February 5, 2026  
**Status:** ✅ Slash chord support implemented, 🔄 Bass detection planned

---

## Overview

Enhanced Nashville Number System to support **slash chords** and **bass notes**, following the Nashville convention where the bass line determines harmonic function.

---

## Why This Matters

In Nashville Number System, the **bass note is crucial**:

### Example: C/G in key of C

**Without bass notation:**
- Chord: C
- NNS: 1
- Missing info: G is in the bass!

**With bass notation:**
- Chord: C/G
- NNS: 1/5
- Complete info: I chord with V in bass (second inversion)

### Musical Significance

**Bass line determines function:**
- C/C = 1 (root position)
- C/E = 1/3 (first inversion)
- C/G = 1/5 (second inversion)

**Walking bass lines:**
- F → F/E → Dm → Dm/C
- 4 → 4/3 → 2m → 2m/1
- Shows the descending bass line clearly!

---

## Implementation

### Phase 1: Slash Chord Support ✅

**Implemented:** Automatic detection and conversion of slash chords

```python
def convert_chord_to_nashville(chord_name, key='C', bass_note=None):
    """
    Convert chord to NNS with optional bass note
    
    Examples:
    - C in key of C = "1"
    - C/G in key of C = "1/5"
    - F/C in key of C = "4/1"
    - Dm/A in key of C = "2m/6"
    """
```

**Features:**
- Automatic slash chord detection (C/G)
- Manual bass note parameter
- Proper interval calculation for bass
- Clean notation (1/5, 4/1, etc.)

### Phase 2: Bass Detection (Planned) 🔄

**Goal:** Automatically detect bass notes from audio

**Strategy:**
1. Use Demucs to separate bass stem
2. Analyze bass frequencies at each chord timing
3. Detect fundamental frequency (lowest note)
4. Map frequency to note name
5. Return bass note for each chord

**Placeholder added:**
```python
def detect_bass_notes_from_stem(audio_path, chords, demucs_model=None):
    """
    Detect bass notes from Demucs bass stem
    
    TODO: Implement bass note detection
    Currently returns None (uses chord root)
    """
    return [None] * len(chords)
```

---

## Examples

### Slash Chord Notation

**In key of C major:**

| Chord | NNS | Meaning |
|-------|-----|---------|
| C | 1 | I chord, root in bass |
| C/E | 1/3 | I chord, 3rd in bass (first inversion) |
| C/G | 1/5 | I chord, 5th in bass (second inversion) |
| F/C | 4/1 | IV chord, I in bass |
| G/B | 5/3 | V chord, 3rd in bass |
| Am/C | 6m/1 | vi chord, I in bass |

**In key of F major:**

| Chord | NNS | Meaning |
|-------|-----|---------|
| F | 1 | I chord, root in bass |
| F/A | 1/3 | I chord, 3rd in bass |
| F/C | 1/5 | I chord, 5th in bass |
| Bb/F | 4/1 | IV chord, I in bass |
| C/E | 5/3 | V chord, 3rd in bass |
| Dm/F | 6m/1 | vi chord, I in bass |

### Walking Bass Lines

**Progression:**
```
F → F/E → Dm → Dm/C → Bb → C → F
```

**NNS (in F major):**
```
1 → 1/7 → 6m → 6m/5 → 4 → 5 → 1
```

**Bass line:**
```
F → E → D → C → Bb → C → F
(descending then resolving)
```

This clearly shows the **descending bass line** that's crucial to the progression!

---

## Current Behavior

### With Slash Chords in Input

If chord detection returns "C/G":
```python
convert_chord_to_nashville("C/G", "C")
# Returns: "1/5"
```

### Without Slash Chords

If chord detection returns "C":
```python
convert_chord_to_nashville("C", "C")
# Returns: "1"
```

### Future: With Bass Detection

When bass detection is implemented:
```python
chords = [
    {'chord': 'C', 'start': 0.0, 'bass': 'G'},  # Bass detected
    {'chord': 'F', 'start': 2.0, 'bass': 'C'},  # Bass detected
]

# Will automatically show as:
# C with G bass → 1/5
# F with C bass → 4/1
```

---

## Benefits

### 1. Accurate Harmonic Function

**Without bass:**
- F → Dm → Gm → C
- 1 → 6m → 2m → 5

**With bass:**
- F → Dm/A → Gm/Bb → C/E
- 1 → 6m/3 → 2m/b3 → 5/3

Shows the **voice leading** and **inversions**!

### 2. Walking Bass Lines

**Progression:**
```
C → C/B → Am → Am/G → F → G → C
```

**NNS:**
```
1 → 1/7 → 6m → 6m/5 → 4 → 5 → 1
```

**Bass line visible:**
```
C → B → A → G → F → G → C
(descending then resolving)
```

### 3. Nashville Convention

Follows standard Nashville practice:
- Bass note determines function
- Slash notation for inversions
- Clear voice leading
- Matches what session musicians expect

---

## Future Enhancement: Bass Detection

### Approach

**1. Separate Bass Stem (Demucs)**
```python
# Already available in our pipeline!
sources = apply_model(demucs_model, audio)
bass_stem = sources[1]  # Bass track
```

**2. Pitch Detection**
```python
import librosa

# For each chord timing
for chord in chords:
    start = chord['start']
    end = chord['end']
    
    # Extract bass audio segment
    bass_segment = bass_stem[start_sample:end_sample]
    
    # Detect fundamental frequency
    f0 = librosa.yin(bass_segment, fmin=40, fmax=400)
    
    # Convert to note name
    bass_note = frequency_to_note(f0)
    
    chord['bass'] = bass_note
```

**3. Weight Bass Notes**
```python
# If bass note differs from chord root
if bass_note != chord_root:
    # Use slash notation
    nns = f"{chord_degree}/{bass_degree}"
```

### Libraries Needed

- ✅ **Demucs** - Already integrated (bass separation)
- ✅ **librosa** - Already available (pitch detection)
- 🔄 **YIN algorithm** - For fundamental frequency detection

### Challenges

1. **Accuracy** - Bass detection can be noisy
2. **Octave errors** - Need to handle octave ambiguity
3. **Performance** - Pitch detection adds processing time
4. **Validation** - Need to verify bass notes make sense

### Timeline

- **Phase 1** ✅ - Slash chord support (done)
- **Phase 2** 🔄 - Bass detection (2-3 hours)
- **Phase 3** 🔄 - Validation and tuning (1-2 hours)

---

## Testing

### Test Slash Chords

```python
# Test cases
test_cases = [
    ("C/G", "C", "1/5"),
    ("F/C", "C", "4/1"),
    ("Dm/A", "C", "2m/6"),
    ("G/B", "C", "5/3"),
    ("Am/C", "C", "6m/1"),
]

for chord, key, expected in test_cases:
    result = convert_chord_to_nashville(chord, key)
    assert result == expected, f"{chord} in {key} should be {expected}, got {result}"
```

### Test Bass Detection (Future)

```python
# When implemented
bass_notes = detect_bass_notes_from_stem(audio_path, chords, demucs_model)

for chord, bass in zip(chords, bass_notes):
    if bass and bass != chord['root']:
        print(f"{chord['chord']}/{bass} → {convert_chord_to_nashville(chord['chord'], key, bass)}")
```

---

## Summary

**Implemented:** ✅ Slash chord support
- Automatic detection of C/G notation
- Manual bass note parameter
- Proper NNS conversion (1/5, 4/1, etc.)

**Planned:** 🔄 Automatic bass detection
- Use Demucs bass stem
- Pitch detection with librosa
- Weight bass notes appropriately
- Show voice leading clearly

**Benefits:**
- Accurate harmonic function
- Walking bass lines visible
- Follows Nashville convention
- Better for session musicians

---

**Status:** Slash chord support is live! Bass detection coming soon.
