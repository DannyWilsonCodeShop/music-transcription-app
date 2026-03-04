# Bass-Only Chord Detection Implementation Plan

## Problem Statement

**Current Issue**: Chord detection analyzes the full mix, which contains:
- Bass playing root notes
- Piano/keys playing different voicings (7ths, 9ths, inversions)
- Guitar playing yet different voicings
- Result: Conflicting harmonic information → inaccurate chord detection

**Solution**: Let user choose which stem to follow for chord detection
- **Phase 1**: Start with bass-only (most accurate for root progression)
- **Phase 2**: Add piano/guitar options later
- **Phase 3**: Allow multi-stem comparison

## Why Bass First?

1. **Clearest harmonic information** - Bass typically plays root notes
2. **Least ambiguous** - No inversions or complex voicings
3. **Best for key detection** - Root progression reveals key clearly
4. **Foundation for NNS** - Nashville numbers based on bass line
5. **Easier to verify accuracy** - Simple to check if bass notes match chords

## Implementation Plan

### Step 1: Update Chord Detection to Use Bass Stem Only

**File**: `backend/functions-v2/chord-detector-ecs/app.py`

**Current Flow**:
```python
# Loads full mix
y, sr = librosa.load(audio_path, sr=22050)

# OR with stem separation (if enabled)
harmonic, sr = detector.separate_harmonic_stem_chunked(audio_path)
# harmonic = bass + other (piano, strings, etc.)
```

**New Flow**:
```python
# Separate into individual stems
stems = detector.separate_stems(audio_path)
# stems = {
#   'bass': bass_audio,
#   'drums': drums_audio,
#   'other': other_audio,  # piano, guitar, strings
#   'vocals': vocals_audio
# }

# Use ONLY bass for chord detection
bass_audio = stems['bass']
chords = detect_chords_from_audio(bass_audio, sr=22050)
```

### Step 2: Modify Demucs Separation

**Current**: Demucs separates into 4 stems but combines bass+other
**New**: Keep stems separate, use only bass

**Changes to `ChordDetector` class**:

```python
def separate_stems(self, audio_path: str) -> dict:
    """
    Separate audio into individual stems
    
    Returns:
        dict with keys: 'bass', 'drums', 'other', 'vocals'
    """
    if not self.demucs_model:
        # Fallback: use full mix for all stems
        y, sr = librosa.load(audio_path, sr=22050)
        return {
            'bass': y,
            'drums': y,
            'other': y,
            'vocals': y,
            'sample_rate': sr
        }
    
    # Load audio
    wav, sr = torchaudio.load(audio_path)
    
    # Ensure stereo
    if wav.shape[0] == 1:
        wav = wav.repeat(2, 1)
    
    # Separate stems
    with torch.no_grad():
        sources = apply_model(self.demucs_model, wav[None], device='cpu')[0]
    
    # Demucs output order: [drums, bass, other, vocals]
    drums = sources[0]
    bass = sources[1]
    other = sources[2]
    vocals = sources[3]
    
    # Convert to mono and numpy
    return {
        'bass': torch.mean(bass, dim=0).numpy(),
        'drums': torch.mean(drums, dim=0).numpy(),
        'other': torch.mean(other, dim=0).numpy(),
        'vocals': torch.mean(vocals, dim=0).numpy(),
        'sample_rate': sr
    }
```

### Step 3: Update Chord Detection Function

**File**: `backend/functions-v2/chord-detector-ecs/app.py`

**Function**: `detect_chords()`

```python
def detect_chords(audio_path, job_id, confirmed_downbeat=None, confirmed_time_signature=None):
    """
    Detect chords from audio file using BASS STEM ONLY
    """
    log("=" * 80)
    log("CHORD DETECTION - BASS STEM ANALYSIS")
    log("=" * 80)
    
    # Separate stems
    log("Step 1: Separating audio stems...")
    stems = detector.separate_stems(audio_path)
    
    # Use ONLY bass for chord detection
    log("Step 2: Analyzing BASS stem for chord detection...")
    bass_audio = stems['bass']
    sr = stems['sample_rate']
    
    # Resample if needed
    if sr != 22050:
        bass_audio = librosa.resample(bass_audio, orig_sr=sr, target_sr=22050)
        sr = 22050
    
    log(f"  Bass audio duration: {len(bass_audio) / sr:.2f}s")
    log(f"  Sample rate: {sr}Hz")
    
    # Detect chords from bass only
    chords_data = detect_chords_essentia(bass_audio, sr, job_id)
    
    # Add metadata
    chords_data['stem_used'] = 'bass'
    chords_data['stem_separation_enabled'] = True
    
    return chords_data
```

### Step 4: Update detect_chords_essentia to Accept Audio Array

**Current**: Takes `audio_path` (file path)
**New**: Takes `audio` (numpy array) + `sr` (sample rate)

```python
def detect_chords_essentia(audio, sr, job_id):
    """
    Detect chords using Essentia's HPCP-based chord detection
    
    Args:
        audio: numpy array of audio samples
        sr: sample rate (should be 22050)
        job_id: job ID for status updates
    """
    log("🎸 Using Essentia chord detection (BASS STEM)")
    
    duration = len(audio) / sr
    log(f"  Audio duration: {duration:.2f}s")
    log(f"  Sample rate: {sr}Hz")
    
    # ... rest of chord detection logic
```

### Step 5: Add Stem Selection to Job Metadata

**DynamoDB Schema Addition**:
```python
{
    'chordsData': {
        'stem_used': 'bass',  # NEW: which stem was analyzed
        'stem_separation_enabled': True,  # NEW: was separation used
        'chords': [...],
        'key': 'C',
        'mode': 'major',
        # ... rest of data
    }
}
```

### Step 6: Future - Add User Selection UI

**Phase 2 Enhancement** (not implementing now):

```typescript
// Frontend - Stem selection before processing
<select name="stemChoice">
  <option value="bass">Bass Line (Recommended)</option>
  <option value="other">Piano/Guitar/Keys</option>
  <option value="full">Full Mix</option>
</select>
```

## Expected Improvements

### Before (Full Mix Analysis):
- Chord: `Cmaj9` (detected from piano voicing)
- Actual bass note: `C` (root)
- Confusion from multiple voicings

### After (Bass-Only Analysis):
- Bass note: `C` → Chord: `C` (or `Cmaj` if other context available)
- Clear root progression: `C → F → G → C`
- Accurate Nashville numbers: `I → IV → V → I`
- Key detection: Much more accurate

## Testing Strategy

1. **Test with known song** - "That's What I Like" (you have this file)
2. **Manually verify bass line** - Listen to bass stem
3. **Compare detected chords to bass notes** - Should match closely
4. **Check key detection** - Should be accurate
5. **Verify NNS numbers** - Should make musical sense

## Implementation Order

1. ✅ Modify `separate_stems()` to return individual stems
2. ✅ Update `detect_chords()` to use bass only
3. ✅ Update `detect_chords_essentia()` to accept audio array
4. ✅ Add stem metadata to output
5. ✅ Test locally with known audio file
6. ✅ Deploy to ECS
7. ✅ Test end-to-end with upload
8. ✅ Verify accuracy improvements

## Code Changes Summary

**Files to Modify**:
1. `backend/functions-v2/chord-detector-ecs/app.py`
   - `ChordDetector.separate_stems()` - new method
   - `detect_chords()` - use bass stem only
   - `detect_chords_essentia()` - accept audio array instead of path

**Environment Variables** (optional for future):
- `CHORD_DETECTION_STEM=bass` (default)
- Can be changed to `other` or `full` later

## Next Steps

1. Implement the code changes above
2. Test locally with `public/04 That_s What I Like.m4a`
3. Verify bass stem extraction works
4. Check chord detection accuracy
5. Deploy to ECS
6. Test with full pipeline

This approach will give us clean, accurate chord progressions based on the bass line, which is exactly what lead sheets need!
