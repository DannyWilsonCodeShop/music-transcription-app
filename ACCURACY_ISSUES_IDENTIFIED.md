# Accuracy Issues Identified - 2026-02-11

## Problem Summary

Testing with "That's What I Like" by Bruno Mars revealed significant accuracy issues with the chord detection system.

---

## Test Results vs Ground Truth

### That's What I Like by Bruno Mars

**Ground Truth**:
- Key: B♭ minor (A# minor) / D♭ major (C# major relative)
- Tempo: 134-135 BPM
- Key chords: B♭m, E♭m, Fm

**System Output**:
- Key: G# major (WRONG - off by a perfect 5th)
- Tempo: 136 BPM ✓ (CORRECT)
- Chords: D#maj7, C#maj7, D#m7, Fm7, C (MOSTLY WRONG)

**Accuracy**: ❌ FAILED

---

## Root Cause Analysis

### 1. Key Detection Algorithm Issue

**Problem**: Krumhansl-Schmuckler algorithm picking wrong key

**Evidence from Diagnostic**:
```
Chroma distribution (relatively flat):
  D#: 0.106 ✓ (E♭ - correct note)
  F:  0.102 ✓ (correct note)
  G#: 0.093 ✓ (A♭ - correct note)
  A#: 0.088 ✓ (B♭ - correct note)
  C#: 0.087 ✓ (D♭ - correct note)
  D:  0.083 ✗ (not in key)

Top 5 key candidates:
  1. G# major: 0.663 ✗ WRONG
  2. D# major: 0.593 ✗ WRONG
  3. F minor:  0.574 ✗ WRONG
  4. C# major: 0.521 ✓ CORRECT (but ranked 4th!)
  5. A# major: 0.458 (close to A# minor)
```

**Analysis**:
- The correct notes ARE present in the chroma
- But the distribution is too flat (0.063-0.106 range)
- Drums and vocals are polluting the signal
- Key profiles aren't discriminating well enough

### 2. Stem Separation Not Working

**Problem**: Demucs installation issues

**Issues**:
1. SSL certificate error when downloading models
2. Large model download (~300MB) required
3. First-time setup complexity

**Impact**:
- System using full mix (drums + vocals + harmony)
- Drums add percussive noise to chroma
- Vocals add melodic content that confuses harmony detection
- Results in flat chroma distribution

### 3. Chord Detection Following Bad Key

**Problem**: Once key is wrong, chord detection is biased

**Evidence**:
- Detected D#maj7, C#maj7 (in G# major)
- Should detect A#m, D#m, Fm (in A# minor)
- Template matching is working, but in wrong key context

---

## Why "Girl from Ipanema" Worked

**That test succeeded because**:
1. Jazz standard with clear, strong harmony
2. Less percussion (more harmonic content)
3. Key of D♭ major has strong tonal center
4. Longer chord durations (easier to detect)

**Bruno Mars failed because**:
1. Heavy drums and production
2. Funk/R&B with groove emphasis over harmony
3. Shorter, more syncopated chord changes
4. Modern production with layered sounds

---

## Required Fixes

### Priority 1: Get Demucs Working ⚠️

**Why**: Clean audio is essential for accurate detection

**Actions**:
1. ✅ Install PyTorch and Demucs (DONE)
2. ✅ Fix SSL certificates (DONE)
3. ⚠️ Download Demucs model (IN PROGRESS - hitting download issues)
4. Test with stem-separated audio

**Alternative**: Pre-download model manually

### Priority 2: Improve Key Detection Algorithm

**Current Issues**:
- Krumhansl-Schmuckler profiles not discriminating well
- No weighting for bass notes (bass defines harmony)
- Flat chroma distribution confuses algorithm

**Potential Fixes**:
1. Weight bass frequencies more heavily
2. Use chord progression analysis (already implemented but needs tuning)
3. Add Essentia KeyExtractor as primary method
4. Implement confidence thresholds for user validation

### Priority 3: Tune HMM Parameters

**Current Issue**: Very long chord durations (39-81 seconds)

**Possible Causes**:
1. HMM transition probability too high (0.9 = very sticky)
2. Minimum duration too aggressive
3. Not detecting actual chord changes

**Potential Fixes**:
1. Lower HMM stay probability (try 0.7-0.8)
2. Adjust minimum duration based on genre
3. Add chord change detection sensitivity parameter

---

## Immediate Next Steps

1. **Fix Demucs model download**
   - Try manual download
   - Or use lighter model (mdx_extra)
   - Or disable for now and fix key detection first

2. **Improve key detection without Demucs**
   - Add bass weighting to chroma
   - Tune Krumhansl-Schmuckler profiles
   - Use Essentia if available

3. **Retest with fixes**
   - Test "That's What I Like" again
   - Compare with/without stem separation
   - Validate against ground truth

---

## Long-term Solutions

### 1. User Validation Flow (Week 3)
- Prompt: "Detected key: G# major. Is this correct?"
- Allow user to select correct key
- Use corrected key for chord detection

### 2. Genre-Specific Parameters
- Jazz: Longer chords, complex harmony
- Pop/R&B: Shorter chords, simpler harmony
- Adjust HMM and minimum duration accordingly

### 3. Machine Learning Key Detection
- Train on labeled dataset
- Or use pre-trained models (Essentia)
- Higher accuracy than rule-based

### 4. Confidence Scoring
- Only auto-accept high-confidence results
- Flag low-confidence for user review
- Learn from user corrections

---

## Conclusion

The system architecture is sound, but accuracy needs improvement:

✅ **Working Well**:
- Tempo detection (136 BPM vs 134-135 actual)
- Beat grid generation
- 16th-note subdivisions
- Template matching mechanics
- Processing speed (17.6x realtime)

❌ **Needs Fixing**:
- Key detection (wrong by perfect 5th)
- Chord detection (following wrong key)
- Stem separation (not working due to setup issues)
- HMM tuning (too conservative)

**Priority**: Get Demucs working OR improve key detection algorithm to work with noisy audio.

The "ask user rather than produce low-confidence output" philosophy is more important than ever - we should prompt for key confirmation before proceeding with chord detection.
