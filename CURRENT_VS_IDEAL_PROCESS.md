# Current vs Ideal Chord Detection Process

## Process Comparison

### Step 1: Find Tempo and Time Signature

**Your Ideal Process:**
> Find the tempo and time signature

**Current Implementation:**
```python
# ✅ Tempo detection working
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
# Result: 136.0 BPM

# ⚠️ Time signature detection basic
time_signature = "4/4"  # Currently defaulting
beats_per_measure = 4
```

**Status:** ✅ Tempo working, ⚠️ Time signature needs improvement

**Improvements Needed:**
- Detect actual time signature (3/4, 6/8, etc.)
- Use beat strength analysis to identify meter
- Validate with Essentia's RhythmExtractor

---

### Step 2: Find Downbeat of First Measure

**Your Ideal Process:**
> Find the downbeat of the first measure

**Current Implementation:**
```python
# ❌ NOT IMPLEMENTED
# Currently just using first detected beat
first_beat = beats[0]  # Could be beat 1, 2, 3, or 4!
```

**Status:** ❌ Missing - Critical issue!

**Why This Matters:**
- First beat at 0.720s might be beat 2 or 3, not beat 1
- Measures won't align correctly
- Chord sheet will show wrong measure numbers

**Improvements Needed:**
```python
def detect_downbeat(audio, beats, time_signature):
    """
    Identify which beat is the downbeat (measure start)
    
    Methods:
    1. Beat strength analysis - downbeats are stronger
    2. Onset detection - look for strong onsets
    3. User confirmation - play with click track
    """
    # Analyze beat strength
    onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
    
    # Find strongest beats (likely downbeats)
    beat_strengths = [onset_env[beat_frame] for beat_frame in beat_frames]
    
    # In 4/4, every 4th beat should be strongest
    # Find the pattern
    downbeat_candidates = find_periodic_peaks(beat_strengths, period=4)
    
    # Return first downbeat
    return downbeat_candidates[0]
```

---

### Step 3: Subdivide from Downbeat

**Your Ideal Process:**
> Subdivide the song from that point on into measures then into 16th notes

**Current Implementation:**
```python
# ⚠️ Subdividing from first beat, not downbeat
subdivisions = generate_subdivisions(beats, level=4)
# Result: 1784 16th-note timestamps starting from first beat
```

**Status:** ⚠️ Working but not aligned to measures

**Improvements Needed:**
```python
def subdivide_from_downbeat(downbeat, tempo, time_signature, duration):
    """
    Create measure-aligned subdivision grid
    
    1. Start from downbeat
    2. Create measures (4 beats in 4/4)
    3. Subdivide each beat into 16th notes
    """
    beats_per_measure = int(time_signature.split('/')[0])
    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * beats_per_measure
    
    # Create measure grid
    measures = []
    current_time = downbeat
    while current_time < duration:
        measures.append(current_time)
        current_time += measure_duration
    
    # Subdivide each measure into 16th notes
    subdivisions = []
    for measure_start in measures:
        for beat in range(beats_per_measure):
            for sixteenth in range(4):
                time = measure_start + (beat * beat_duration) + (sixteenth * beat_duration / 4)
                subdivisions.append(time)
    
    return measures, subdivisions
```

---

### Step 4: Calculate Frames to Average

**Your Ideal Process:**
> Calculate the beginning and end frame of each 16th note, then calculate the number of frames that should be averaged

**Current Implementation:**
```python
# ✅ WORKING
def align_chroma_to_grid(chroma, subdivisions, sr, hop_length):
    """
    For each subdivision, average chroma frames within window
    """
    for i, subdivision_time in enumerate(subdivisions):
        # Convert time to frame index
        frame_idx = librosa.time_to_frames(subdivision_time, sr=sr, hop_length=hop_length)
        
        # Define window to next subdivision
        window_duration = subdivisions[i+1] - subdivision_time
        window_frames = int(window_duration * sr / hop_length)
        
        # Average chroma within window
        aligned[:, i] = np.mean(chroma[:, frame_idx:frame_idx+window_frames], axis=1)
```

**Status:** ✅ Working correctly

**Current Results:**
- At 136 BPM: ~5.5 chroma samples per 16th note
- At 120 BPM: ~6.3 chroma samples per 16th note
- Proper averaging within each subdivision window

---

### Step 5: Weight Strong Tones in Chords

**Your Ideal Process:**
> Analyze and average the chords weighing the strong tones in each chord greater to overshadow the noise

**Current Implementation:**
```python
# ⚠️ Equal weighting
major_template = np.zeros(12)
major_template[[0, 4, 7]] = [1.0, 0.8, 0.9]  # Root, 3rd, 5th
```

**Status:** ⚠️ Basic weighting, needs improvement

**Improvements Needed:**
```python
def create_weighted_chord_templates():
    """
    Weight chord tones by importance:
    - Root: Highest weight (defines the chord)
    - 3rd: High weight (major vs minor)
    - 5th: Medium weight (stability)
    - 7th: Medium weight (color)
    - Extensions: Lower weight (9th, 11th, 13th)
    """
    major_template = np.zeros(12)
    major_template[[0, 4, 7]] = [1.0, 0.9, 0.7]  # Root, 3rd, 5th
    
    maj7_template = np.zeros(12)
    maj7_template[[0, 4, 7, 11]] = [1.0, 0.9, 0.7, 0.5]  # Root, 3rd, 5th, 7th
    
    # Normalize so root is always strongest
    return normalize_templates(templates)
```

**Also Need:**
- Bass note weighting (bass defines harmony)
- Harmonic series weighting (overtones)
- Temporal weighting (sustained notes vs passing tones)

---

### Step 6: Determine Key from Patterns

**Your Ideal Process:**
> Look for repeating patterns and frequent downbeats to determine the key of the song

**Current Implementation:**
```python
# ⚠️ Using statistical profiles only
def detect_key_from_chromagram(chroma):
    # Krumhansl-Schmuckler key profiles
    major_profile = [6.35, 2.23, 3.48, ...]
    
    # Correlate with chroma
    correlation = np.corrcoef(chroma_mean, major_profile)
```

**Status:** ⚠️ Works but misses musical context

**Improvements Needed:**
```python
def detect_key_from_progression(chords):
    """
    Analyze chord progression patterns to determine key
    
    Look for:
    1. I-IV-V progressions (most common)
    2. ii-V-I (jazz)
    3. I-vi-IV-V (pop)
    4. Cadences (V-I, IV-I)
    5. Tonic chord frequency (I appears most)
    """
    # Count chord roots
    root_frequency = count_chord_roots(chords)
    
    # Find common progressions
    progressions = find_progressions(chords)
    
    # Look for I-IV-V patterns
    for key in all_keys:
        I, IV, V = get_scale_degrees(key)
        if has_progression(chords, [I, IV, V]):
            return key
    
    # Look for cadences
    for key in all_keys:
        V, I = get_scale_degrees(key, [5, 1])
        if has_cadence(chords, V, I):
            return key
    
    # Fall back to most frequent root
    return most_frequent_root
```

---

### Step 7: Nashville Number System

**Your Ideal Process:**
> Find the NNS number of each chord given the determined key on the sheet music

**Current Implementation:**
```python
# ❌ NOT IMPLEMENTED
# Currently showing absolute chord names
chords = ["Fmaj7", "D#m7", "G#maj7", ...]
```

**Status:** ❌ Missing

**Improvements Needed:**
```python
def convert_to_nns(chord_name, key, scale):
    """
    Convert absolute chord to Nashville Number System
    
    Examples in C major:
    - C → 1 (I)
    - Dm → 2m (ii)
    - Em → 3m (iii)
    - F → 4 (IV)
    - G → 5 (V)
    - Am → 6m (vi)
    - Bdim → 7° (vii°)
    
    With qualities:
    - Cmaj7 → 1maj7
    - G7 → 5⁷
    - Dm7 → 2m7
    """
    # Parse chord
    root, quality = parse_chord(chord_name)
    
    # Find scale degree
    scale_notes = get_scale_notes(key, scale)
    degree = scale_notes.index(root) + 1
    
    # Format with quality
    if 'm' in quality and 'maj' not in quality:
        return f"{degree}m{quality.replace('m', '')}"
    else:
        return f"{degree}{quality}"
```

**Example Output:**
```
Key: C# major

Measure 1: 2maj7 (D#maj7)
Measure 2: 2m7 (D#m7)
Measure 3: 2maj7 (D#maj7)
Measure 4: 1maj7 (C#maj7)
```

---

### Step 8: User Input for Alignment

**Your Ideal Process:**
> Is there a way to solicit user input with downbeat and first measure alignment?

**Current Implementation:**
```python
# ❌ NOT IMPLEMENTED
# Fully automatic, no user interaction
```

**Status:** ❌ Missing - Important for accuracy!

**Improvements Needed:**

#### Option 1: Click Track Playback
```python
def verify_downbeat_with_user(audio_path, detected_downbeat, tempo):
    """
    Play audio with click track for user verification
    
    1. Generate click track at detected tempo
    2. Emphasize downbeats (louder click)
    3. Play first 10 seconds with clicks
    4. Ask user: "Does the loud click align with measure 1?"
    5. If no, ask for offset adjustment
    """
    import sounddevice as sd
    
    # Load audio
    audio, sr = librosa.load(audio_path, duration=10)
    
    # Generate click track
    clicks = generate_click_track(tempo, duration=10, downbeat=detected_downbeat)
    
    # Mix audio + clicks
    mixed = audio + clicks * 0.3
    
    # Play
    sd.play(mixed, sr)
    sd.wait()
    
    # Get user feedback
    response = input("Does the loud click align with the first downbeat? (y/n): ")
    
    if response.lower() == 'n':
        offset = float(input("Enter offset in seconds (+ or -): "))
        return detected_downbeat + offset
    
    return detected_downbeat
```

#### Option 2: Visual Waveform with Beat Markers
```python
def show_beat_alignment_ui(audio_path, beats, downbeat_candidate):
    """
    Show waveform with beat markers for visual confirmation
    
    1. Display waveform
    2. Show detected beats as vertical lines
    3. Highlight downbeat candidate in red
    4. Allow user to click to adjust downbeat
    5. Return confirmed downbeat
    """
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Button
    
    # Load and display waveform
    y, sr = librosa.load(audio_path, duration=10)
    times = np.arange(len(y)) / sr
    
    fig, ax = plt.subplots(figsize=(15, 4))
    ax.plot(times, y)
    
    # Draw beat markers
    for beat in beats[:20]:
        ax.axvline(beat, color='blue', alpha=0.5)
    
    # Highlight downbeat
    ax.axvline(downbeat_candidate, color='red', linewidth=2)
    
    # Add click handler
    def onclick(event):
        nonlocal downbeat_candidate
        downbeat_candidate = event.xdata
        # Redraw
    
    fig.canvas.mpl_connect('button_press_event', onclick)
    plt.show()
    
    return downbeat_candidate
```

#### Option 3: Web UI (Best for Production)
```javascript
// Frontend component
function DownbeatAlignmentTool({ audioUrl, detectedBeats, detectedDownbeat }) {
  const [downbeat, setDownbeat] = useState(detectedDownbeat);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const playWithClickTrack = () => {
    // Play audio with click track
    const audio = new Audio(audioUrl);
    const clickTrack = generateClickTrack(tempo, downbeat);
    
    // Mix and play
    playMixed(audio, clickTrack);
  };
  
  return (
    <div>
      <h3>Verify Downbeat Alignment</h3>
      <Waveform 
        audioUrl={audioUrl}
        beats={detectedBeats}
        downbeat={downbeat}
        onDownbeatChange={setDownbeat}
      />
      <button onClick={playWithClickTrack}>
        Play with Click Track
      </button>
      <input 
        type="number" 
        value={downbeat}
        onChange={(e) => setDownbeat(e.target.value)}
        step="0.01"
      />
      <button onClick={() => confirmDownbeat(downbeat)}>
        Confirm
      </button>
    </div>
  );
}
```

---

## Summary of Gaps

### Critical (Must Fix)
1. ❌ **Downbeat detection** - Currently missing, causes measure misalignment
2. ❌ **User confirmation** - No way to verify/adjust alignment
3. ❌ **Nashville Number System** - Not converting to scale degrees

### Important (Should Fix)
4. ⚠️ **Chord tone weighting** - Equal weighting, should emphasize root/3rd/5th
5. ⚠️ **Pattern-based key detection** - Only using statistical profiles
6. ⚠️ **Time signature detection** - Defaulting to 4/4

### Nice to Have
7. ⚠️ **Measure-aligned subdivision** - Works but not from true downbeat
8. ✅ **Tempo detection** - Working well
9. ✅ **Frame averaging** - Working correctly

---

## Implementation Priority

### Phase 1: Downbeat Detection (Critical)
1. Implement beat strength analysis
2. Detect downbeat candidates
3. Create user confirmation tool (click track)
4. Adjust subdivision grid to start from downbeat

### Phase 2: Nashville Number System
1. Implement chord-to-NNS conversion
2. Update chord sheet to show both absolute and NNS
3. Add key-aware chord analysis

### Phase 3: Improved Key Detection
1. Add progression pattern analysis
2. Weight by chord frequency and duration
3. Look for cadences (V-I, IV-I)
4. Combine with statistical profiles

### Phase 4: Chord Tone Weighting
1. Weight root/3rd/5th more heavily
2. Add bass note emphasis
3. Consider harmonic series
4. Test with complex chords

---

## Next Steps

Would you like me to:
1. **Implement downbeat detection** with user confirmation?
2. **Add Nashville Number System** conversion?
3. **Create click track verification** tool?
4. **All of the above** in priority order?

