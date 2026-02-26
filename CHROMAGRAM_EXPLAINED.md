# What is a Chromagram?

## Simple Explanation

A **chromagram** is like a "piano roll" that shows which musical notes are playing at each moment in a song.

Think of it as a heat map that answers: "How much of each note (C, C#, D, D#, E, F, F#, G, G#, A, A#, B) is present at this moment?"

---

## Visual Analogy

Imagine a piano with 12 keys (one octave):

```
C  C# D  D# E  F  F# G  G# A  A# B
█  ░  █  ░  █  █  ░  █  ░  █  ░  █
```

A chromagram shows how "bright" each key is over time:

```
Time →
     0s    1s    2s    3s    4s
C    ███   ░░░   ███   ░░░   ███
C#   ░░░   ░░░   ░░░   ░░░   ░░░
D    ░░░   ███   ░░░   ███   ░░░
D#   ░░░   ░░░   ░░░   ░░░   ░░░
E    ███   ░░░   ███   ░░░   ███
F    ░░░   ░░░   ░░░   ░░░   ░░░
F#   ░░░   ░░░   ░░░   ░░░   ░░░
G    ███   ███   ███   ███   ███
G#   ░░░   ░░░   ░░░   ░░░   ░░░
A    ░░░   ░░░   ░░░   ░░░   ░░░
A#   ░░░   ░░░   ░░░   ░░░   ░░░
B    ░░░   ░░░   ░░░   ░░░   ░░░
```

In this example:
- At 0s: C, E, G are bright → **C major chord**
- At 1s: D, G are bright → **G chord** (with D)
- At 2s: C, E, G again → **C major chord**

---

## How It Works

### 1. Audio → Frequencies
```
Audio waveform
  ↓
Fourier Transform (FFT)
  ↓
Frequency spectrum
```

The audio is broken down into individual frequencies (like 440 Hz = A note).

### 2. Frequencies → Notes
```
Frequency spectrum
  ↓
Group by musical notes
  ↓
12 note bins (C, C#, D, ..., B)
```

All frequencies that correspond to "C" (any octave) are grouped together:
- C2 (65 Hz)
- C3 (130 Hz)
- C4 (261 Hz)
- C5 (523 Hz)
- etc.

### 3. Notes → Chromagram
```
12 note bins over time
  ↓
Chromagram (12 rows × time columns)
```

Result: A 2D array showing note intensity over time.

---

## Why "Chroma"?

**Chroma** = the "color" or "quality" of a note, ignoring octave.

- C2, C3, C4, C5 all have the same **chroma** (they're all "C")
- Different octaves, same note quality

This is perfect for chord detection because:
- A C major chord is C-E-G in ANY octave
- We don't care if it's C3-E3-G3 or C4-E4-G4
- We just care that C, E, and G are present

---

## Two Types We Use

### 1. Full Spectrum Chromagram
**Analyzes**: All frequencies (20 Hz - 20,000 Hz)

**Purpose**: Captures the overall harmonic content
- Vocals
- Guitars
- Piano
- Strings
- Everything

**Shape**: 12 notes × ~4800 time frames (for 3-minute song)

### 2. Bass Chromagram
**Analyzes**: Only bass frequencies (65 Hz - 262 Hz = C2 to C4)

**Purpose**: Focuses on the bass line
- Bass guitar
- Kick drum (filtered out with HPSS)
- Low piano notes
- Low strings

**Shape**: 12 notes × ~4800 time frames

**Why separate?**: Bass notes are often the chord root, so we weight them heavily.

---

## How We Use It for Chord Detection

### Step 1: Compute Chromagrams
```python
# Full spectrum
chroma = librosa.feature.chroma_cqt(y=audio, sr=22050)
# Shape: (12, 4800) - 12 notes, 4800 time frames

# Bass only
bass_chroma = librosa.feature.chroma_cqt(
    y=audio, 
    sr=22050,
    fmin=65,      # C2
    n_octaves=2   # C2 to C4
)
# Shape: (12, 4800)
```

### Step 2: Weight Bass Heavily
```python
# Bass gets 2x weight for chord detection
weighted_chroma = (chroma + 2.0 * bass_chroma) / 3.0
```

**Why?**: Bass notes are usually the chord root, so they're more important.

### Step 3: Match Against Chord Templates
```python
# C major template: C=1.0, E=0.7, G=0.8
c_major = [1.0, 0, 0, 0, 0.7, 0, 0, 0.8, 0, 0, 0, 0]

# Compare weighted_chroma to template
score = dot_product(weighted_chroma, c_major)
```

### Step 4: Find Best Match
```python
# Try all 84 chord templates
best_chord = max(scores)  # Highest score wins
```

---

## Example: Detecting a C Major Chord

### Audio at 2.5 seconds:
```
Piano playing: C4, E4, G4
Bass playing: C2
```

### Full Spectrum Chromagram:
```
C:  0.85  (C4 from piano + C2 from bass)
C#: 0.02
D:  0.03
D#: 0.02
E:  0.65  (E4 from piano)
F:  0.03
F#: 0.02
G:  0.70  (G4 from piano)
G#: 0.02
A:  0.03
A#: 0.02
B:  0.03
```

### Bass Chromagram:
```
C:  0.95  (C2 from bass - very strong!)
C#: 0.01
D:  0.02
D#: 0.01
E:  0.05  (some bleed from E4)
F:  0.02
F#: 0.01
G:  0.08  (some bleed from G4)
G#: 0.01
A:  0.02
A#: 0.01
B:  0.02
```

### Weighted Chromagram (2:1 bass weighting):
```
C:  (0.85 + 2×0.95) / 3 = 0.92  ← Very strong!
E:  (0.65 + 2×0.05) / 3 = 0.25
G:  (0.70 + 2×0.08) / 3 = 0.29
```

### Match Against Templates:
```
C major (C, E, G):     Score = 0.95  ← Best match!
C minor (C, Eb, G):    Score = 0.72
G major (G, B, D):     Score = 0.45
Am (A, C, E):          Score = 0.58
```

**Result**: C major chord detected!

---

## Why Chromagrams Are Useful

### 1. Octave-Invariant
- Don't care if it's C2 or C4
- Same chord in any octave

### 2. Polyphonic
- Can detect multiple notes at once
- Works with full mixes (not just single instruments)

### 3. Robust
- Works with vocals, drums, noise
- Doesn't need perfect audio

### 4. Fast
- Efficient computation
- Real-time capable

---

## Limitations

### 1. Tuning Issues
- Assumes standard tuning (A=440 Hz)
- Detuned instruments can confuse it

### 2. Noise Sensitivity
- Drums can add noise
- We use HPSS to remove percussion

### 3. Harmonic Confusion
- Overtones can create false notes
- E.g., a strong C note creates harmonics at G, E, etc.

### 4. Temporal Resolution
- Trade-off between time and frequency resolution
- Can't detect very fast chord changes

---

## Our Implementation

```python
# 1. Separate harmonics from drums
y_harmonic, y_percussive = librosa.effects.hpss(audio)

# 2. Compute full spectrum chromagram
chroma = librosa.feature.chroma_cqt(
    y=y_harmonic,
    sr=22050,
    hop_length=2048,
    n_chroma=12,
    bins_per_octave=36
)

# 3. Compute bass chromagram
bass_chroma = librosa.feature.chroma_cqt(
    y=y_harmonic,
    sr=22050,
    hop_length=2048,
    n_chroma=12,
    bins_per_octave=36,
    fmin=librosa.note_to_hz('C2'),
    n_octaves=2
)

# 4. Weight bass heavily
weighted = (chroma + 2.0 * bass_chroma) / 3.0

# 5. Match against 84 chord templates
# (major, minor, 7th, maj7, m7, sus4, dim for all 12 roots)
```

---

## Summary

**Chromagram** = A visual representation of which notes are playing over time

**Purpose**: Detect chords by matching note patterns against templates

**Our approach**: 
- Compute two chromagrams (full + bass)
- Weight bass 2:1
- Sample at downbeats only
- Match against 84 chord templates

**Result**: Accurate chord detection that focuses on the most important musical information!
