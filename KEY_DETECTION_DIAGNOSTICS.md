# Key Detection Diagnostics

## Current Configuration

### Audio Processing Pipeline

1. **Stem Separation**: ❌ DISABLED
   - Not using Demucs or similar
   - Processing full mix audio

2. **Drum Removal**: ✅ ENABLED (HPSS)
   - Using Harmonic-Percussive Source Separation
   - Separates harmonic content from drums/percussion
   - Only harmonic component used for analysis

3. **Bass Weighting**: ✅ ENABLED
   - Analyzes bass frequencies (C2-C4, 65-262 Hz)
   - Bass chromagram weighted 3:1 for key detection
   - Bass chromagram weighted 2:1 for chord detection

4. **Frequency Analysis**:
   - Full spectrum: All frequencies
   - Bass range: C2 (65 Hz) to C4 (262 Hz)
   - Uses CQT (Constant-Q Transform) chromagram

---

## Key Detection Methods

### Method 1: Chromagram-Based (Krumhansl-Schmuckler)
- Analyzes frequency content over time
- Compares to major/minor key profiles
- Uses bass-weighted chromagram (3:1 ratio)
- Returns: key, mode, confidence

### Method 2: Progression-Based
- Analyzes chord progression patterns
- Looks for common progressions (I-IV-V, I-vi-ii-V, etc.)
- Identifies repeating patterns
- Returns: key, mode, confidence, pattern info

### Selection Logic
- Compares confidence scores from both methods
- Selects method with higher confidence
- Logs both results for comparison

---

## New Diagnostic Logging

When you process a file, the logs now show:

### 1. Audio Analysis Configuration
```
AUDIO ANALYSIS CONFIGURATION
  Stem separation: DISABLED (using full mix)
  Drum removal: ENABLED (HPSS)
  Bass weighting: ENABLED (C2-C4 range)
  Analysis method: Chromagram + Pattern matching
```

### 2. Harmonic/Percussive Separation
```
Separating harmonic content from percussion...
  Harmonic energy: 12345678 (85.3%)
  Percussive energy: 2134567 (14.7%)
  Using harmonic component for chord/key detection
```

### 3. Chromagram Analysis
```
KEY DETECTION DIAGNOSTICS
Chromagram Analysis:
  Full spectrum chroma shape: (12, 4800)
  Bass chroma shape: (12, 4800)
  Full spectrum mean: [0.123, 0.234, ...]
  Bass mean: [0.456, 0.567, ...]
  Top 5 notes (full): ['E=0.234', 'G=0.198', 'B=0.187', 'D=0.156', 'A=0.145']
  Top 5 notes (bass): ['E=0.312', 'B=0.245', 'G=0.198', 'D=0.167', 'A=0.134']
```

### 4. Key Detection Results
```
Key Detection Results:
  Chromagram method: E minor (confidence: 0.823)
  Progression method: G major (confidence: 0.756)
  ✓ SELECTED: Chromagram-based (higher confidence)
  FINAL KEY: E minor (confidence: 0.823)
```

---

## Why Key Detection Might Be Wrong

### 1. Relative Major/Minor Confusion
- E minor and G major share the same notes
- Algorithm might pick the wrong one
- Bass weighting helps but isn't perfect

### 2. Modulation
- Song might change keys
- Algorithm detects the most prominent key
- Doesn't handle key changes within a song

### 3. Complex Harmony
- Jazz, R&B, and modern pop use complex chords
- Extended chords (9ths, 11ths, 13ths) can confuse the algorithm
- Borrowed chords from other keys

### 4. Drum-Heavy Mix
- HPSS isn't perfect
- Some drum bleed into harmonic component
- Can affect chromagram accuracy

### 5. Bass-Heavy Mix
- If bass is too loud, it dominates the analysis
- 3:1 weighting might be too aggressive
- Could try 2:1 or 1.5:1 instead

---

## How to Improve Key Detection

### Option 1: Adjust Bass Weighting
Current: 3:1 ratio for key detection

Try:
- 2:1 (more balanced)
- 1.5:1 (even more balanced)
- 4:1 (even more bass emphasis)

### Option 2: Enable Stem Separation
- Use Demucs to separate vocals, drums, bass, other
- Analyze only bass + other (no drums, no vocals)
- More accurate but slower (30-60 seconds per song)

### Option 3: Improve Progression Analysis
- Weight progression method higher
- Analyze more chord patterns
- Use Nashville numbers for better pattern matching

### Option 4: Hybrid Approach
- Use both chromagram and progression
- Average the results
- Weight by confidence scores

### Option 5: Post-Processing
- Check if detected key makes sense with chords
- If most chords don't fit the key, try relative major/minor
- Use first and last chord as hints

---

## Testing the Diagnostics

Upload a file and check the CloudWatch logs:

```bash
aws logs tail /ecs/music-transcription-chord-detection \
  --since 5m \
  --profile production \
  --format short | grep -A 20 "KEY DETECTION"
```

You'll see:
1. Which notes are strongest in full spectrum
2. Which notes are strongest in bass
3. Both key detection methods' results
4. Which method was selected and why
5. Final key and confidence

---

## Example Output

For "04 CUFF IT.m4a" (should be E minor/G major):

```
AUDIO ANALYSIS CONFIGURATION
  Stem separation: DISABLED (using full mix)
  Drum removal: ENABLED (HPSS)
  Bass weighting: ENABLED (C2-C4 range)

Harmonic energy: 8234567 (87.2%)
Percussive energy: 1205432 (12.8%)

KEY DETECTION DIAGNOSTICS
Top 5 notes (full): ['A=0.245', 'D=0.198', 'F=0.187', ...]
Top 5 notes (bass): ['A=0.312', 'D=0.245', 'F=0.198', ...]

Key Detection Results:
  Chromagram method: A minor (confidence: 0.750)
  Progression method: A minor (confidence: 0.680)
  ✓ SELECTED: Chromagram-based (higher confidence)
  FINAL KEY: A minor (confidence: 0.750)
```

**Issue**: Detected A minor instead of E minor
**Likely Cause**: A is the relative minor of C major, and shares notes with E minor
**Solution**: Need to improve progression analysis or adjust weighting

---

## Next Steps

1. ✅ Added detailed diagnostics
2. 🎯 Test with your file and review logs
3. 📊 Analyze which notes are detected
4. 🔧 Adjust bass weighting if needed
5. 🎵 Consider enabling stem separation for better accuracy

---

**Note**: The new diagnostics are deployed. Upload a file and we can review the logs together to understand why it's detecting the wrong key.
