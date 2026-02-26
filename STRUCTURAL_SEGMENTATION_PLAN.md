# Structural Segmentation Implementation Plan

**Date:** February 5, 2026  
**Goal:** Implement robust music structure analysis (Verse/Chorus/Bridge detection)

---

## Current State

**What We Have:**
- ✅ Chord detection (librosa + essentia)
- ✅ Beat tracking and tempo detection
- ✅ Pattern detection (repeating chord progressions)
- ✅ Lyrics transcription (Deepgram)
- ⚠️ Basic structure detection (rule-based, not very accurate)

**What's Missing:**
- ❌ Reliable section boundary detection
- ❌ Accurate Verse/Chorus/Bridge labeling
- ❌ Audio embedding-based analysis
- ❌ Multi-modal approach (audio + chords + lyrics)

---

## Recommended Approach: Multi-Modal Pipeline

Based on research and practical considerations, here's the optimal pipeline:

### Phase 1: Audio Embeddings + Segmentation (MSAF)

**Tool:** MSAF (Music Structure Analysis Framework)  
**Why:** Well-maintained, pretrained, works today

**Capabilities:**
- Detects segment boundaries (where sections change)
- Identifies repeated sections (A-B-A-C pattern)
- Multiple algorithms available (Foote, Spectral Clustering, CNN)

**Output:**
```python
{
  'segments': [
    {'start': 0, 'end': 23, 'label': 'A'},
    {'start': 23, 'end': 47, 'label': 'B'},
    {'start': 47, 'end': 70, 'label': 'A'},  # Repeated section
    {'start': 70, 'end': 95, 'label': 'C'}
  ]
}
```

**Installation:**
```bash
pip install msaf
```

**Usage:**
```python
import msaf

# Analyze structure
boundaries, labels = msaf.process(audio_file, boundaries_id='cnmf')

# Get segments with repetition info
segments = msaf.io.get_segments(boundaries, labels)
```

### Phase 2: Intelligent Labeling (Rule-Based + Heuristics)

**Inputs:**
1. MSAF segments (A, B, A, C)
2. Chord progressions (from our existing system)
3. Lyrics timing (from Deepgram)
4. Energy/loudness analysis (librosa)
5. Vocal activity detection

**Labeling Rules:**

```python
def label_sections(segments, chords, lyrics, audio_features):
    """
    Intelligent section labeling based on multiple signals
    """
    
    for segment in segments:
        # 1. CHORUS: Most repeated + high energy
        if segment['repetition_count'] >= 3 and segment['energy'] > 0.7:
            segment['label'] = 'Chorus'
        
        # 2. VERSE: Repeated 2-3 times + has lyrics + moderate energy
        elif segment['repetition_count'] >= 2 and segment['has_lyrics'] and segment['energy'] < 0.7:
            segment['label'] = 'Verse'
        
        # 3. BRIDGE: Unique section + appears after 50% of song
        elif segment['repetition_count'] == 1 and segment['position'] > 0.5:
            segment['label'] = 'Bridge'
        
        # 4. INTRO: First section + low vocal activity
        elif segment['position'] == 0 and segment['vocal_activity'] < 0.3:
            segment['label'] = 'Intro'
        
        # 5. OUTRO: Last section + decreasing energy
        elif segment['position'] > 0.9 and segment['energy_trend'] == 'decreasing':
            segment['label'] = 'Outro'
        
        # 6. PRE-CHORUS: Appears before chorus + building energy
        elif segment['next_section'] == 'Chorus' and segment['energy_trend'] == 'increasing':
            segment['label'] = 'Pre-Chorus'
        
        else:
            segment['label'] = 'Section'
    
    return segments
```

### Phase 3: Multi-Modal Features

**Audio Features (librosa):**
```python
# Energy/loudness
rms = librosa.feature.rms(y=audio)

# Spectral centroid (brightness)
centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)

# Zero crossing rate (noisiness)
zcr = librosa.feature.zero_crossing_rate(audio)
```

**Vocal Activity Detection:**
```python
# Use Demucs stems (we already have this!)
vocals = demucs_stems['vocals']
vocal_energy = np.mean(librosa.feature.rms(y=vocals))

# High vocal energy = likely verse/chorus
# Low vocal energy = likely intro/outro/instrumental
```

**Chord Progression Matching:**
```python
# Match segment chords to our detected patterns
for segment in segments:
    segment_chords = get_chords_in_range(chords, segment['start'], segment['end'])
    
    # Check if this matches a known pattern
    for pattern in detected_patterns:
        if chords_match(segment_chords, pattern['progression']):
            segment['pattern_id'] = pattern['id']
            segment['pattern_count'] = pattern['occurrences']
```

**Lyrics Density:**
```python
# More lyrics = likely verse
# Repeated lyrics = likely chorus
for segment in segments:
    segment_lyrics = get_lyrics_in_range(lyrics, segment['start'], segment['end'])
    
    segment['word_count'] = len(segment_lyrics.split())
    segment['words_per_second'] = segment['word_count'] / segment['duration']
    
    # Check for repeated lyrics
    segment['lyrics_repetition'] = check_lyrics_repetition(segment_lyrics, all_lyrics)
```

---

## Implementation Steps

### Step 1: Install MSAF (ECS Container)

**Update Dockerfile:**
```dockerfile
# Add MSAF
RUN pip install msaf

# MSAF dependencies
RUN pip install scikit-learn scipy
```

### Step 2: Add MSAF to Chord Detector

**Update `app.py`:**
```python
import msaf

def detect_structure_msaf(audio_path):
    """
    Use MSAF for structural segmentation
    Returns segments with boundaries and labels
    """
    log("🎵 Detecting structure with MSAF...")
    
    try:
        # Run MSAF analysis
        boundaries, labels = msaf.process(
            audio_path,
            boundaries_id='cnmf',  # CNN-based method
            labels_id='cnmf'
        )
        
        # Convert to our format
        segments = []
        for i in range(len(boundaries) - 1):
            segments.append({
                'start': float(boundaries[i]),
                'end': float(boundaries[i + 1]),
                'label': labels[i],
                'duration': float(boundaries[i + 1] - boundaries[i])
            })
        
        log(f"✓ MSAF detected {len(segments)} segments")
        return segments
        
    except Exception as e:
        log(f"MSAF failed: {e}", "WARNING")
        return []
```

### Step 3: Add Multi-Modal Analysis

**New function:**
```python
def analyze_segment_features(segment, audio, sr, chords, lyrics, demucs_stems=None):
    """
    Extract multi-modal features for a segment
    """
    start_sample = int(segment['start'] * sr)
    end_sample = int(segment['end'] * sr)
    segment_audio = audio[start_sample:end_sample]
    
    features = {}
    
    # 1. Energy
    rms = librosa.feature.rms(y=segment_audio)
    features['energy'] = float(np.mean(rms))
    features['energy_std'] = float(np.std(rms))
    
    # 2. Spectral features
    centroid = librosa.feature.spectral_centroid(y=segment_audio, sr=sr)
    features['brightness'] = float(np.mean(centroid))
    
    # 3. Vocal activity (if stems available)
    if demucs_stems:
        vocal_audio = demucs_stems['vocals'][start_sample:end_sample]
        vocal_rms = librosa.feature.rms(y=vocal_audio)
        features['vocal_activity'] = float(np.mean(vocal_rms))
    
    # 4. Chord progression
    segment_chords = [
        c for c in chords 
        if segment['start'] <= c['start'] < segment['end']
    ]
    features['chord_count'] = len(segment_chords)
    features['chords'] = [c['chord'] for c in segment_chords]
    
    # 5. Lyrics
    segment_lyrics = [
        w for w in lyrics 
        if segment['start'] <= w['start'] < segment['end']
    ]
    features['word_count'] = len(segment_lyrics)
    features['words_per_second'] = len(segment_lyrics) / segment['duration']
    
    return features
```

### Step 4: Intelligent Labeling

**New function:**
```python
def label_segments_intelligent(segments, features_list, pattern_info):
    """
    Apply intelligent labeling rules
    """
    # Count repetitions
    segment_signatures = {}
    for i, seg in enumerate(segments):
        sig = tuple(features_list[i]['chords'])
        if sig not in segment_signatures:
            segment_signatures[sig] = []
        segment_signatures[sig].append(i)
    
    # Label based on repetition and features
    for i, segment in enumerate(segments):
        features = features_list[i]
        sig = tuple(features['chords'])
        repetition_count = len(segment_signatures[sig])
        position = segment['start'] / segments[-1]['end']
        
        # CHORUS: Most repeated + high energy
        if repetition_count >= 3 and features['energy'] > 0.6:
            segment['label'] = 'Chorus'
        
        # VERSE: Repeated 2-3 times + lyrics
        elif repetition_count >= 2 and features['words_per_second'] > 1.5:
            segment['label'] = 'Verse'
        
        # BRIDGE: Unique + late in song
        elif repetition_count == 1 and position > 0.5:
            segment['label'] = 'Bridge'
        
        # INTRO: First + low vocals
        elif i == 0 and features.get('vocal_activity', 1) < 0.3:
            segment['label'] = 'Intro'
        
        # OUTRO: Last + low energy
        elif i == len(segments) - 1 and features['energy'] < 0.4:
            segment['label'] = 'Outro'
        
        else:
            segment['label'] = 'Section'
        
        segment['repetition_count'] = repetition_count
        segment['features'] = features
    
    return segments
```

### Step 5: Integration

**Update main detection flow:**
```python
def detect_chords(audio_path, job_id):
    # ... existing code ...
    
    # 1. Detect structure with MSAF
    msaf_segments = detect_structure_msaf(audio_path)
    
    # 2. Analyze features for each segment
    segment_features = []
    for segment in msaf_segments:
        features = analyze_segment_features(
            segment, y, sr, chords, lyrics, 
            demucs_stems=detector.demucs_model
        )
        segment_features.append(features)
    
    # 3. Intelligent labeling
    labeled_segments = label_segments_intelligent(
        msaf_segments, segment_features, pattern_info
    )
    
    # 4. Return enhanced structure
    return {
        'chords': chords,
        'key': key,
        'songStructure': labeled_segments,  # Enhanced!
        # ... rest of data ...
    }
```

---

## Expected Results

### Before (Current System)

```json
{
  "songStructure": [
    {"label": "Section", "measureStart": 1, "measureEnd": 8},
    {"label": "Section", "measureStart": 9, "measureEnd": 16}
  ]
}
```

**Issues:**
- Generic "Section" labels
- Based only on chord patterns
- No audio analysis
- Misses intro/outro

### After (MSAF + Multi-Modal)

```json
{
  "songStructure": [
    {
      "label": "Intro",
      "start": 0,
      "end": 8.5,
      "measureStart": 1,
      "measureEnd": 4,
      "repetition_count": 1,
      "features": {
        "energy": 0.35,
        "vocal_activity": 0.12,
        "chord_count": 4
      }
    },
    {
      "label": "Verse",
      "start": 8.5,
      "end": 32.1,
      "measureStart": 5,
      "measureEnd": 16,
      "repetition_count": 2,
      "features": {
        "energy": 0.58,
        "vocal_activity": 0.75,
        "words_per_second": 2.3
      }
    },
    {
      "label": "Chorus",
      "start": 32.1,
      "end": 48.7,
      "measureStart": 17,
      "measureEnd": 24,
      "repetition_count": 4,
      "features": {
        "energy": 0.82,
        "vocal_activity": 0.88,
        "words_per_second": 1.8
      }
    }
  ]
}
```

**Benefits:**
- ✅ Accurate labels (Verse, Chorus, Bridge)
- ✅ Based on multiple signals
- ✅ Includes audio features
- ✅ Repetition tracking
- ✅ Time-based boundaries

---

## Timeline

### Phase 1: MSAF Integration (2-3 hours)
- Add MSAF to Dockerfile
- Implement basic segmentation
- Test with sample songs

### Phase 2: Feature Extraction (2-3 hours)
- Add energy/spectral analysis
- Integrate vocal activity detection
- Extract lyrics density

### Phase 3: Intelligent Labeling (2-3 hours)
- Implement labeling rules
- Test with multiple songs
- Tune thresholds

### Phase 4: Testing & Refinement (2-3 hours)
- Test with diverse genres
- Adjust rules based on results
- Document accuracy

**Total:** 8-12 hours of development

---

## Alternative: OpenL3 + Clustering

If MSAF doesn't work well, we can try:

```python
import openl3
import sklearn.cluster

# 1. Extract embeddings
audio, sr = librosa.load(audio_path)
embeddings, timestamps = openl3.get_audio_embedding(audio, sr)

# 2. Cluster embeddings
kmeans = sklearn.cluster.KMeans(n_clusters=5)
labels = kmeans.fit_predict(embeddings)

# 3. Find boundaries (where labels change)
boundaries = np.where(np.diff(labels) != 0)[0]
```

---

## Summary

**Recommended Approach:**
1. ✅ MSAF for segment boundaries
2. ✅ Multi-modal features (audio + chords + lyrics)
3. ✅ Rule-based intelligent labeling
4. ✅ Leverage existing Demucs stems

**Why This Works:**
- Proven tools (MSAF is research-grade)
- Multi-modal = more accurate
- Leverages our existing pipeline
- Practical and maintainable

**Next Steps:**
1. Add MSAF to requirements.txt
2. Update Dockerfile
3. Implement segmentation function
4. Test with "Like The Dew"
5. Refine labeling rules

---

**Ready to implement?** This will give us much better structure detection than our current pattern-only approach.
