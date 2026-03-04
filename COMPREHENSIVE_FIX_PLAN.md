# Comprehensive Fix Plan - Data Quality Issues

## Root Causes Identified

### 1. **Chord Symbol Corruption: `A !' F# !' A !' D !' E !' E`**
**Location**: Pattern analysis in `patternAnalysis` field
**Problem**: Pattern progressions store only chord roots (`A`, `F#`, `D`) instead of full chord names (`Amaj7`, `F#dim`, `Dsus4`)
**Impact**: PDF generator displays these incorrectly, adding `!'` characters

### 2. **No Lyrics**
**Location**: `chordsData.lyrics` field is `null`
**Problem**: Whisper lyrics extraction either:
- Not running in ECS container
- Failing silently
- Not being saved to DynamoDB

### 3. **No Lead Sheet**
**Location**: `chordsData.leadSheet` field is `null`
**Problem**: Lyrics-chord alignment not running because no lyrics exist

### 4. **Pattern-Only Display**
**Problem**: PDF generator falls back to showing pattern analysis when no leadSheet exists
**Impact**: Shows chord progressions instead of full song structure with lyrics

### 5. **Key Signature Inaccurate**
**Current**: Key detection from pattern analysis may be wrong
**Need**: Better key detection algorithm or manual override

### 6. **Missing NNS Numbers**
**Location**: `nashvilleProgression` exists in patterns but not displayed
**Problem**: PDF generator not rendering Nashville numbers

### 7. **Cannot Verify Downbeat**
**Problem**: Without accurate chords and structure, can't validate downbeat alignment

## Fix Priority Order

### Phase 1: Fix Lyrics Extraction (CRITICAL)
**Why First**: Lyrics are foundation for everything else
**Tasks**:
1. Verify Whisper is installed in ECS container
2. Check ECS logs for lyrics extraction errors
3. Fix any Whisper initialization issues
4. Ensure lyrics are saved to DynamoDB correctly

### Phase 2: Fix Lyrics-Chord Alignment
**Why Second**: Enables lead sheet generation
**Tasks**:
1. Verify alignment code runs when lyrics exist
2. Fix any alignment algorithm issues
3. Ensure leadSheet is saved to DynamoDB

### Phase 3: Fix Pattern Analysis Chord Names
**Why Third**: Fixes the `!'` corruption
**Tasks**:
1. Update pattern detection to store full chord names, not just roots
2. Update PDF generator to handle both formats gracefully

### Phase 4: Improve Key Detection
**Why Fourth**: Affects Nashville numbers and overall accuracy
**Tasks**:
1. Review key detection algorithm
2. Add manual key override option
3. Improve confidence scoring

### Phase 5: Add Nashville Numbers to Display
**Why Fifth**: Enhancement after core issues fixed
**Tasks**:
1. Update PDF generator to show Nashville numbers
2. Add toggle for NNS display

### Phase 6: Verify Downbeat Alignment
**Why Last**: Requires all other data to be accurate first
**Tasks**:
1. Test with known-good audio
2. Verify measure alignment
3. Check chord-to-beat mapping

## Immediate Action: Check ECS Container

Let's verify what's actually in the ECS container and why lyrics aren't working.
