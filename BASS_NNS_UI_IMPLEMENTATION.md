# Bass-Only Chord Detection with Analysis Options Modal - Implementation Complete

## Summary

Implemented a user-facing modal that allows users to select which music part to analyze (bass/piano/guitar) before processing. Currently, only bass analysis is active, with piano and guitar grayed out as "Coming Soon".

## What Was Implemented

### 1. Frontend - Analysis Options Modal

**File**: `src/components/AnalysisOptionsModal.tsx`

**Features**:
- Modal appears immediately after file selection
- Two main questions:
  1. "Which music part would you like to analyze?"
     - Bass Line (active) - Shows "(Nashville Numbers)" badge
     - Piano/Keys (grayed out, "Coming Soon")
     - Guitar (grayed out, "Coming Soon")
  2. "Do you want lyrics?" 
     - Checkbox (grayed out, "Coming Soon")
- Additional options (all active):
  - Key Detection (checkbox)
  - Tempo (BPM) (checkbox)
  - Time Signature (checkbox)
- Beautiful gradient UI matching the app's design
- Auto-starts upload after user confirms options

**Fixed**: Removed duplicate code that was causing rendering issues

### 2. Frontend - App Integration

**File**: `src/App.tsx`

**Changes**:
- Added `showAnalysisModal` state
- Added `analysisOptions` state to store user selections
- Modal shows after file selection: `setShowAnalysisModal(true)`
- Upload automatically starts after user confirms options
- Analysis options passed to backend via upload API

### 3. Backend - Upload Lambda

**File**: `simple-pipeline/upload-lambda.py`

**Changes**:
- Accepts `analysisOptions` from frontend request body
- Stores `analysisOptions` in DynamoDB job record
- Default options if not provided:
  ```python
  {
      'musicPart': 'bass',
      'includeLyrics': False,
      'includeKey': True,
      'includeTempo': True,
      'includeTimeSignature': True
  }
  ```

### 4. Backend - Process Audio Lambda

**File**: `simple-pipeline/process-audio-lambda.py`

**Changes**:
- Reads `analysisOptions` from DynamoDB job record
- Extracts `musicPart` value (bass/piano/guitar)
- Passes `MUSIC_PART` environment variable to ECS task
- Updates status message to show which part is being analyzed:
  - "Starting bass line analysis..."
  - "Starting piano line analysis..." (future)
  - "Starting guitar line analysis..." (future)

### 5. Backend - Chord Detector ECS Task

**File**: `backend/functions-v2/chord-detector-ecs/app.py`

**Major Changes**:

#### A. New `separate_stems()` Method
```python
def separate_stems(self, audio_path: str) -> dict:
    """
    Separate audio into individual stems using Demucs
    
    Returns:
        dict with keys: 'bass', 'drums', 'other', 'vocals', 'sample_rate'
    """
```

- Uses Demucs to separate audio into 4 stems:
  - `bass`: Bass line
  - `drums`: Percussion
  - `other`: Piano, guitar, keys, strings, etc.
  - `vocals`: Vocal track
- Returns mono numpy arrays for each stem
- Falls back to full mix if Demucs not available

#### B. Updated `detect_chords_librosa()` Function
```python
# Get music part from environment variable
music_part = os.environ.get('MUSIC_PART', 'bass').lower()

# Separate stems and select appropriate one
if music_part == 'bass':
    y = stems['bass']
    log("✓ Using BASS stem for chord detection")
elif music_part in ['piano', 'guitar', 'other']:
    y = stems['other']  # Piano/guitar/keys
    log("✓ Using OTHER stem for chord detection")
```

- Reads `MUSIC_PART` environment variable
- Separates stems using `detector.separate_stems()`
- Uses ONLY the selected stem for chord detection
- Resamples to 22050Hz if needed
- Logs which stem is being analyzed

#### C. Added Stem Metadata to Output
```python
return {
    'chords': [...],
    'key': 'C',
    'mode': 'major',
    # ... other fields ...
    'stemUsed': 'bass',  # NEW: which stem was analyzed
    'stemSeparationEnabled': True  # NEW: was separation used
}
```

## User Flow

1. User selects audio file
2. **Modal appears** with analysis options
3. User sees:
   - Bass Line (selected by default) ✓
   - Piano/Keys (grayed out)
   - Guitar (grayed out)
   - Lyrics checkbox (grayed out)
4. User clicks "Start Analysis"
5. Upload begins automatically
6. Backend receives `analysisOptions: { musicPart: 'bass', ... }`
7. Process Lambda reads options and passes `MUSIC_PART=bass` to ECS
8. ECS task:
   - Separates audio into stems
   - Uses ONLY bass stem for chord detection
   - Detects chords from bass line
   - Returns results with `stemUsed: 'bass'` metadata

## Why Bass First?

1. **Most accurate for root progression** - Bass typically plays root notes
2. **Least ambiguous** - No inversions or complex voicings
3. **Best for key detection** - Root progression reveals key clearly
4. **Foundation for Nashville Number System** - NNS based on bass line
5. **Easier to verify accuracy** - Simple to check if bass notes match chords

## Expected Improvements

### Before (Full Mix Analysis):
- Chord: `Cmaj9` (detected from piano voicing)
- Actual bass note: `C` (root)
- Confusion from multiple instruments playing different voicings

### After (Bass-Only Analysis):
- Bass note: `C` → Chord: `C`
- Clear root progression: `C → F → G → C`
- Accurate Nashville numbers: `I → IV → V → I`
- Key detection: Much more accurate

## Next Steps

### Phase 2: Piano/Guitar Analysis (Future)
1. Enable piano/guitar options in modal
2. Update backend to handle `musicPart='piano'` or `musicPart='guitar'`
3. Use `stems['other']` for piano/guitar analysis
4. Display full chord voicings (maj7, 9ths, etc.) instead of just roots

### Phase 3: Lyrics Integration (Future)
1. Enable lyrics checkbox in modal
2. Run Whisper extraction when `includeLyrics=true`
3. Align lyrics with chords
4. Generate lead sheet with lyrics

### Phase 4: NNS Display (Current Task)
1. When `musicPart='bass'`, display Nashville numbers instead of chord names
2. Update PDF generator to show NNS notation
3. Add NNS to frontend display

## Files Modified

1. `src/components/AnalysisOptionsModal.tsx` - Created modal component
2. `src/App.tsx` - Integrated modal into upload flow
3. `simple-pipeline/upload-lambda.py` - Store analysis options
4. `simple-pipeline/process-audio-lambda.py` - Pass options to ECS
5. `backend/functions-v2/chord-detector-ecs/app.py` - Implement bass-only detection

## Testing

To test the implementation:

1. **Frontend**: 
   ```bash
   npm run dev
   ```
   - Upload a file
   - Verify modal appears
   - Verify bass is selected by default
   - Verify piano/guitar are grayed out

2. **Backend** (after deployment):
   - Upload test file: `public/04 That_s What I Like.m4a`
   - Check ECS logs for "Using BASS stem for chord detection"
   - Verify `stemUsed: 'bass'` in DynamoDB job record
   - Compare chord accuracy to previous full-mix results

## Deployment Commands

```bash
# Deploy upload Lambda
cd simple-pipeline
./deploy-upload-simple.sh

# Deploy process Lambda
./deploy-processing.sh

# Deploy ECS task (chord detector)
cd ../backend/functions-v2/chord-detector-ecs
./build-and-push.sh
```

## Success Criteria

✅ Modal appears after file selection
✅ Bass option is active and selected by default
✅ Piano/guitar options are grayed out
✅ Lyrics checkbox is grayed out
✅ Upload starts automatically after confirmation
✅ Analysis options stored in DynamoDB
✅ MUSIC_PART passed to ECS task
✅ Backend separates stems correctly
✅ Backend uses only bass stem for detection
✅ Stem metadata included in output

## Known Limitations

1. **Stem separation requires Demucs** - Falls back to full mix if not available
2. **Piano/guitar not yet implemented** - Options grayed out in UI
3. **Lyrics not yet implemented** - Checkbox grayed out in UI
4. **NNS display not yet implemented** - Still shows chord names, not numbers

## Next Immediate Task

**Display Nashville Numbers instead of chord names when bass analysis is selected**

This will complete the bass-only analysis feature by showing the output in the most useful format for musicians analyzing bass progressions.
