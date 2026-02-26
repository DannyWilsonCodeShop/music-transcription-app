# Week 1-2: Chord Detection Algorithm Rewrite

**Goal**: Replace downbeat-only approach with beat-aligned, 16th-note resolution system that handles syncopated chord changes.

**Status**: Planning Phase  
**Timeline**: 2 weeks  
**Priority**: CRITICAL - Foundation for entire system

---

## Current vs. Target

### Current System ❌
```python
# Downbeat-only sampling
downbeats = beats[::4]  # Every 4th beat in 4/4
for downbeat in downbeats:
    chroma = extract_chroma(downbeat)
    chord = match_template(chroma)
```

**Problems**:
- Misses chord changes between downbeats
- Can't detect syncopated changes (8th/16th notes)
- Analyzes only ~25% of the song (1 out of 4 beats)

### Target System ✅
```python
# 16th-note resolution
subdivisions = generate_16th_note_grid(beats)
for subdivision in subdivisions:
    chroma = extract_chroma(subdivision)
    averaged_chroma = average_window(chroma, subdivision)
    chord = match_template_with_hmm(averaged_chroma)
    enforce_min_duration(chord, eighth_note_duration)
```

**Benefits**:
- Detects ALL chord changes
- Handles syncopation (8th/16th note positions)
- Clean signal (no passing tones)
- Musically accurate timing

---

## Implementation Plan

### Part 1: Tempo & Beat Detection (Days 1-2)

**Objective**: Establish precise timing grid

**Tasks**:
1. Implement robust tempo detection
2. Generate full beat grid
3. Create 16th-note subdivisions
4. Validate timing accuracy

**Code Structure**:
```python
def detect_tempo_and_beats(audio_path):
    """
    Detect tempo and generate beat grid with subdivisions
    
    Returns:
        tempo: BPM (float)
        beats: Beat timestamps (array)
        subdivisions: 16th note timestamps (array)
        time_signature: e.g., "4/4"
    """
    # Load audio
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Detect tempo using multiple methods for robustness
    tempo_librosa, beats_librosa = librosa.beat.beat_track(y=y, sr=sr)
    
    # Optional: Use Essentia for comparison
    if ESSENTIA_AVAILABLE:
        tempo_essentia, beats_essentia = detect_tempo_essentia(audio_path)
        # Use most confident result
        tempo = select_best_tempo(tempo_librosa, tempo_essentia)
        beats = select_best_beats(beats_librosa, beats_essentia)
    else:
        tempo = float(tempo_librosa)
        beats = librosa.frames_to_time(beats_librosa, sr=sr)
    
    # Detect time signature
    time_signature = detect_time_signature(beats)
    
    # Generate 16th note subdivisions
    subdivisions = generate_subdivisions(beats, level=4)
    
    return tempo, beats, subdivisions, time_signature

def generate_subdivisions(beats, level=4):
    """
    Generate subdivisions between beats
    
    Args:
        beats: Beat timestamps
        level: 4 = 16th notes, 2 = 8th notes
    
    Returns:
        Array of subdivision timestamps
    """
    subdivisions = []
    for i in range(len(beats) - 1):
        beat_duration = beats[i+1] - beats[i]
        subdivision_duration = beat_duration / level
        
        for j in range(level):
            subdivisions.append(beats[i] + j * subdivision_duration)
    
    # Add subdivisions for last beat (estimate)
    last_beat_duration = beats[-1] - beats[-2]
    for j in range(level):
        subdivisions.append(beats[-1] + j * last_beat_duration / level)
    
    return np.array(subdivisions)
```

**Testing**:
- Test with songs at different tempos (60-180 BPM)
- Verify subdivision accuracy
- Check edge cases (tempo changes, irregular beats)

---

### Part 2: Stem Separation (Days 3-5)

**Objective**: Isolate harmonic content (remove drums + vocals)

**Tasks**:
1. Integrate Demucs for stem separation
2. Remove drums and vocals
3. Combine bass + other stems
4. Optimize for memory efficiency

**Code Structure**:
```python
def separate_stems(audio_path):
    """
    Separate audio into stems and isolate harmonic content
    
    Returns:
        harmonic_audio: Bass + other (no drums, no vocals)
        sr: Sample rate
    """
    import torch
    from demucs import pretrained
    from demucs.apply import apply_model
    import torchaudio
    
    # Load Demucs model (use htdemucs for best quality)
    model = pretrained.get_model('htdemucs')
    model.eval()
    
    # Load audio
    wav, sr = torchaudio.load(audio_path)
    
    # Ensure stereo
    if wav.shape[0] == 1:
        wav = wav.repeat(2, 1)
    
    # Resample if needed
    if sr != model.samplerate:
        resampler = torchaudio.transforms.Resample(sr, model.samplerate)
        wav = resampler(wav)
        sr = model.samplerate
    
    # Separate stems
    with torch.no_grad():
        sources = apply_model(model, wav[None], device='cpu')[0]
    
    # Extract stems
    # sources: [drums, bass, other, vocals]
    drums = sources[0]
    bass = sources[1]
    other = sources[2]  # Guitar, piano, strings, synths
    vocals = sources[3]
    
    # Combine harmonic content (no drums, no vocals)
    harmonic = bass + other
    
    # Convert to mono
    harmonic_mono = torch.mean(harmonic, dim=0).numpy()
    
    # Resample to 22050 for librosa
    if sr != 22050:
        harmonic_mono = librosa.resample(harmonic_mono, orig_sr=sr, target_sr=22050)
        sr = 22050
    
    return harmonic_mono, sr

def separate_stems_chunked(audio_path, chunk_duration=30):
    """
    Memory-efficient chunked stem separation
    Processes audio in chunks to avoid OOM errors
    """
    # Similar to current implementation but with vocals removal
    # Process in 30-second chunks
    # Concatenate results
    pass
```

**Memory Optimization**:
- Process in 30-second chunks
- Clear memory after each chunk
- Target: <4GB RAM usage

**Testing**:
- Verify drums are removed
- Verify vocals are removed
- Check harmonic content quality
- Test with different audio formats

---

### Part 3: CQT Chromagram with Beat Alignment (Days 6-8)

**Objective**: Compute high-resolution chromagram aligned to 16th notes

**Tasks**:
1. Implement CQT chromagram computation
2. Align chroma frames to 16th note grid
3. Average chroma within each window
4. Validate alignment accuracy

**Code Structure**:
```python
def compute_beat_aligned_chromagram(audio, sr, subdivisions, hop_length_ms=20):
    """
    Compute CQT chromagram aligned to beat subdivisions
    
    Args:
        audio: Harmonic audio (no drums/vocals)
        sr: Sample rate
        subdivisions: 16th note timestamps
        hop_length_ms: Hop length in milliseconds (20ms default, 10ms for fast changes)
    
    Returns:
        aligned_chroma: Chromagram aligned to subdivisions [12 x n_subdivisions]
    """
    # Compute CQT chromagram
    hop_length = int(sr * hop_length_ms / 1000)
    
    chroma = librosa.feature.chroma_cqt(
        y=audio,
        sr=sr,
        hop_length=hop_length,
        n_chroma=12,
        bins_per_octave=36,  # High resolution
        window='blackmanharris',
        fmin=librosa.note_to_hz('C2'),  # Start at C2
        n_octaves=7  # Cover full range
    )
    
    # Apply median filtering to reduce noise
    from scipy.ndimage import median_filter
    chroma = median_filter(chroma, size=(1, 5))
    
    # Align to subdivisions
    aligned_chroma = align_chroma_to_grid(chroma, subdivisions, sr, hop_length)
    
    return aligned_chroma

def align_chroma_to_grid(chroma, subdivisions, sr, hop_length):
    """
    Align chromagram frames to subdivision grid
    Average chroma within each subdivision window
    """
    n_subdivisions = len(subdivisions)
    aligned = np.zeros((12, n_subdivisions))
    
    for i, subdivision_time in enumerate(subdivisions):
        # Convert time to frame index
        frame_idx = librosa.time_to_frames(subdivision_time, sr=sr, hop_length=hop_length)
        
        # Define window around this subdivision
        # Window size = time until next subdivision
        if i < n_subdivisions - 1:
            next_time = subdivisions[i + 1]
            window_duration = next_time - subdivision_time
        else:
            window_duration = subdivisions[-1] - subdivisions[-2]
        
        window_frames = int(window_duration * sr / hop_length)
        
        # Average chroma within window
        start_frame = max(0, frame_idx)
        end_frame = min(chroma.shape[1], frame_idx + window_frames)
        
        if start_frame < end_frame:
            aligned[:, i] = np.mean(chroma[:, start_frame:end_frame], axis=1)
        else:
            # Edge case: use single frame
            if frame_idx < chroma.shape[1]:
                aligned[:, i] = chroma[:, frame_idx]
    
    return aligned
```

**Parameters**:
- Window size: 4096 samples
- Hop length: 20ms (adjustable to 10ms)
- CQT bins per octave: 36 (high resolution)
- Frequency range: C2 to C9

**Testing**:
- Verify alignment accuracy
- Check chroma quality
- Test with different hop lengths
- Validate window averaging

---

### Part 4: Template Matching with HMM (Days 9-11)

**Objective**: Detect chords with temporal smoothing and minimum duration

**Tasks**:
1. Create comprehensive chord templates (84+ chords)
2. Implement HMM for temporal smoothing
3. Enforce minimum duration (1/8 note)
4. Handle chord transitions

**Code Structure**:
```python
def detect_chords_with_hmm(aligned_chroma, tempo, subdivisions):
    """
    Detect chords using template matching + HMM
    
    Args:
        aligned_chroma: Beat-aligned chromagram
        tempo: BPM
        subdivisions: Timing grid
    
    Returns:
        chords: List of detected chords with timing
    """
    # Create chord templates
    templates = create_chord_templates()
    
    # Template matching at each subdivision
    chord_probabilities = []
    for i in range(aligned_chroma.shape[1]):
        chroma_vector = aligned_chroma[:, i]
        
        # Normalize
        if np.sum(chroma_vector) > 0:
            chroma_vector = chroma_vector / np.sum(chroma_vector)
        
        # Calculate similarity to each template
        probs = {}
        for chord_name, template in templates.items():
            # Cosine similarity
            similarity = np.dot(chroma_vector, template) / (
                np.linalg.norm(chroma_vector) * np.linalg.norm(template) + 1e-10
            )
            probs[chord_name] = max(0, similarity)
        
        chord_probabilities.append(probs)
    
    # Apply HMM for temporal smoothing
    chord_sequence = apply_hmm_smoothing(chord_probabilities, tempo)
    
    # Enforce minimum duration
    min_duration = calculate_eighth_note_duration(tempo)
    filtered_chords = enforce_minimum_duration(
        chord_sequence, 
        subdivisions, 
        min_duration
    )
    
    return filtered_chords

def create_chord_templates():
    """
    Create comprehensive chord templates
    
    Returns:
        Dictionary of chord_name -> chroma template
    """
    templates = {}
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    for root_idx in range(12):
        root = chord_names[root_idx]
        
        # Major (1, 3, 5)
        major = np.zeros(12)
        major[[0, 4, 7]] = [1.0, 0.8, 0.9]
        templates[root] = np.roll(major, root_idx)
        
        # Minor (1, b3, 5)
        minor = np.zeros(12)
        minor[[0, 3, 7]] = [1.0, 0.8, 0.9]
        templates[root + 'm'] = np.roll(minor, root_idx)
        
        # Dominant 7th (1, 3, 5, b7)
        dom7 = np.zeros(12)
        dom7[[0, 4, 7, 10]] = [1.0, 0.7, 0.8, 0.6]
        templates[root + '7'] = np.roll(dom7, root_idx)
        
        # Major 7th (1, 3, 5, 7)
        maj7 = np.zeros(12)
        maj7[[0, 4, 7, 11]] = [1.0, 0.7, 0.8, 0.6]
        templates[root + 'maj7'] = np.roll(maj7, root_idx)
        
        # Minor 7th (1, b3, 5, b7)
        min7 = np.zeros(12)
        min7[[0, 3, 7, 10]] = [1.0, 0.7, 0.8, 0.6]
        templates[root + 'm7'] = np.roll(min7, root_idx)
        
        # Sus4 (1, 4, 5)
        sus4 = np.zeros(12)
        sus4[[0, 5, 7]] = [1.0, 0.7, 0.9]
        templates[root + 'sus4'] = np.roll(sus4, root_idx)
        
        # Diminished (1, b3, b5)
        dim = np.zeros(12)
        dim[[0, 3, 6]] = [1.0, 0.8, 0.8]
        templates[root + 'dim'] = np.roll(dim, root_idx)
        
        # Add more: sus2, add9, 6, m6, aug, etc.
    
    return templates

def apply_hmm_smoothing(chord_probabilities, tempo):
    """
    Apply Hidden Markov Model for temporal smoothing
    Prevents rapid chord changes that are musically unlikely
    """
    from hmmlearn import hmm
    
    # Define transition probabilities
    # Higher probability of staying on same chord
    # Lower probability of rapid changes
    
    # Simplified: Use Viterbi algorithm for most likely sequence
    # This smooths out noisy detections
    
    pass

def enforce_minimum_duration(chord_sequence, subdivisions, min_duration):
    """
    Enforce minimum chord duration (1/8 note)
    Merge chords shorter than minimum
    """
    filtered = []
    current_chord = chord_sequence[0]
    current_start = subdivisions[0]
    
    for i in range(1, len(chord_sequence)):
        if chord_sequence[i] != current_chord:
            # Chord changed
            duration = subdivisions[i] - current_start
            
            if duration >= min_duration:
                # Keep this chord
                filtered.append({
                    'chord': current_chord,
                    'start': current_start,
                    'end': subdivisions[i],
                    'duration': duration
                })
                current_chord = chord_sequence[i]
                current_start = subdivisions[i]
            else:
                # Too short, merge with next
                # Keep current chord, don't update
                pass
    
    # Add last chord
    duration = subdivisions[-1] - current_start
    if duration >= min_duration:
        filtered.append({
            'chord': current_chord,
            'start': current_start,
            'end': subdivisions[-1],
            'duration': duration
        })
    
    return filtered

def calculate_eighth_note_duration(tempo):
    """
    Calculate duration of 1/8 note in seconds
    
    Args:
        tempo: BPM
    
    Returns:
        Duration in seconds
    """
    quarter_note_duration = 60.0 / tempo
    eighth_note_duration = quarter_note_duration / 2
    return eighth_note_duration
```

**HMM Parameters**:
- Transition probability (same chord): 0.9
- Transition probability (different chord): 0.1 / (n_chords - 1)
- Emission probability: From template matching

**Testing**:
- Test with syncopated songs
- Verify minimum duration enforcement
- Check chord transition smoothness
- Validate against ground truth

---

### Part 5: ML-Based Key Detection (Days 12-14)

**Objective**: Replace frequency-based key detection with ML model

**Tasks**:
1. Integrate Essentia KeyExtractor
2. Implement confidence scoring
3. Prepare for user validation
4. Handle edge cases (modulation, atonal)

**Code Structure**:
```python
def detect_key_ml(audio_path, chroma=None):
    """
    Detect key using Essentia ML model
    
    Args:
        audio_path: Path to audio file
        chroma: Optional pre-computed chromagram
    
    Returns:
        key: Key name (e.g., "C")
        scale: "major" or "minor"
        confidence: 0.0 to 1.0
    """
    if not ESSENTIA_AVAILABLE:
        # Fallback to chromagram-based
        return detect_key_chromagram(chroma)
    
    import essentia.standard as es
    
    # Load audio
    loader = es.MonoLoader(filename=audio_path, sampleRate=44100)
    audio = loader()
    
    # Use Essentia KeyExtractor
    key_extractor = es.KeyExtractor(profileType='temperley')
    
    key, scale, strength = key_extractor(audio)
    
    # Convert to our format
    confidence = float(strength)
    
    # Log for debugging
    log(f"ML Key Detection: {key} {scale} (confidence: {confidence:.2f})")
    
    return key, scale, confidence

def detect_key_chromagram(chroma):
    """
    Fallback: Krumhansl-Schmuckler key detection from chromagram
    """
    # Existing implementation
    pass

def prepare_key_for_validation(key, scale, confidence):
    """
    Prepare key detection result for user validation
    
    Returns:
        validation_data: Data to send to frontend for confirmation
    """
    return {
        'detected_key': key,
        'detected_scale': scale,
        'confidence': confidence,
        'needs_validation': confidence < 0.7,  # Low confidence = ask user
        'alternatives': []  # Could suggest alternatives
    }
```

**Confidence Thresholds**:
- High confidence (>0.7): Auto-accept, but still show to user
- Medium confidence (0.4-0.7): Ask user to confirm
- Low confidence (<0.4): Ask user to select from options

**Testing**:
- Test with songs in various keys
- Test with modulating songs
- Verify confidence scores
- Check edge cases

---

## Integration & Testing (Days 13-14)

### Integration Tasks
1. Combine all components into single pipeline
2. Add comprehensive logging
3. Optimize performance
4. Handle edge cases

### Testing Strategy
```python
def test_new_chord_detection():
    """
    Test suite for new chord detection system
    """
    test_songs = [
        {
            'path': 'test_songs/simple_4-4.mp3',
            'expected_tempo': 120,
            'expected_key': 'C major',
            'expected_chords': ['C', 'F', 'G', 'C'],
            'has_syncopation': False
        },
        {
            'path': 'test_songs/syncopated_gospel.mp3',
            'expected_tempo': 140,
            'expected_key': 'G major',
            'has_syncopation': True,
            'expected_16th_note_changes': True
        },
        {
            'path': 'test_songs/jazz_complex.mp3',
            'expected_tempo': 180,
            'expected_key': 'Bb major',
            'has_fast_changes': True,
            'use_10ms_hop': True
        }
    ]
    
    for song in test_songs:
        result = detect_chords_new_system(song['path'])
        validate_results(result, song)
```

### Performance Targets
- Processing time: <2 minutes for 3-minute song
- Memory usage: <4GB RAM
- Chord detection accuracy: >90% (will improve with user validation)

---

## Deployment Plan

### Docker Image Updates
```dockerfile
# Add Demucs
RUN pip install demucs

# Add HMM library
RUN pip install hmmlearn

# Update librosa
RUN pip install --upgrade librosa

# Add Essentia (if not already installed)
RUN pip install essentia
```

### Environment Variables
```bash
# Chord detection parameters
CHORD_HOP_LENGTH_MS=20  # or 10 for fast changes
CHORD_MIN_DURATION_BEATS=0.5  # 1/8 note
ENABLE_STEM_SEPARATION=true
STEM_SEPARATION_MODEL=htdemucs
```

### Rollout Strategy
1. Deploy to test environment
2. Test with 10-20 songs
3. Compare with old system
4. Gradual rollout to production

---

## Success Criteria

### Must Have ✅
- [ ] Detects chord changes at 16th-note resolution
- [ ] Handles syncopated chord changes
- [ ] Removes drums and vocals from analysis
- [ ] Enforces minimum 1/8 note duration
- [ ] ML-based key detection with confidence scores
- [ ] Processing time <2 minutes per song

### Nice to Have 🎯
- [ ] Adaptive hop length (10ms for fast sections)
- [ ] Chord inversion detection
- [ ] Extended chord detection (9th, 11th, 13th)
- [ ] Real-time progress updates

---

## Next Steps After Week 1-2

Once chord detection is solid:
1. **Week 3**: Add user validation flow (frontend + backend)
2. **Week 4**: Integrate lyrics extraction (Whisper)
3. **Week 5**: Build professional PDF generator

---

## Questions & Decisions Needed

1. **Demucs Model**: Use `htdemucs` (best quality) or `mdx_extra` (faster)?
2. **HMM Library**: Use `hmmlearn` or implement custom Viterbi?
3. **Hop Length**: Default 20ms or make it adaptive?
4. **Testing**: Need ground truth chord annotations for validation?

Ready to start implementation?
