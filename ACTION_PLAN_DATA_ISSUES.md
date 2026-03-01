# Action Plan: Fix Data Quality Issues

## Summary of Findings

### What's Working ✅
- Chord detection is running and producing chords
- Chords are stored correctly in DynamoDB with proper names (`Csus4`, `Am`, `F#dim`, etc.)
- API returns correct chord data
- Pattern analysis is detecting chord progressions
- Job completes successfully

### What's Broken ❌
1. **Lyrics extraction fails silently** - Whisper starts but produces no output
2. **No lead sheet** - Because no lyrics, alignment can't run
3. **Pattern analysis uses chord roots** - Stores `A`, `F#` instead of `Amaj7`, `F#dim`
4. **PDF shows corrupted symbols** - `A !' F# !'` because it expects full chord names
5. **No Nashville numbers displayed** - Data exists but not rendered
6. **Key detection may be inaccurate** - Hard to verify without proper output

## Root Cause Analysis

### Issue #1: Whisper Failing Silently
**Evidence**:
- Logs show "🎤 Extracting lyrics from..." but no completion message
- No error logs captured
- `chordsData.lyrics` is `null` in DynamoDB
- Job completes successfully (exception is caught)

**Likely Causes**:
1. Whisper model download failing in container (no internet access?)
2. Whisper running out of memory
3. Whisper timing out (2-3 minute audio takes too long)
4. FFmpeg/audio decoding issue

**Fix Strategy**:
1. Add more detailed error logging around Whisper
2. Check if Whisper model files are pre-downloaded in container
3. Consider using smaller Whisper model (`tiny` instead of `base`)
4. Add timeout handling
5. Test locally with same audio file

### Issue #2: Pattern Analysis Chord Simplification
**Evidence**:
- `patternAnalysis[0].progression` = `["A", "F#", "A", "D", "E", "E"]`
- Should be `["Amaj7", "F#dim", "Amaj7", "Dsus4", "Em", "Esus4"]`

**Root Cause**:
- Pattern detection code extracts only chord root, not full name
- Located in `detect_key_from_progression()` function

**Fix Strategy**:
1. Update pattern detection to store full chord names
2. Keep root extraction for key detection logic only
3. Store both `root` and `fullName` in pattern data

### Issue #3: PDF Generator Handling
**Evidence**:
- PDF shows `A !' F# !' A !' D !' E !' E`
- The `!'` suggests template rendering issue

**Root Cause**:
- PDF generator expects full chord names
- When it gets roots only, template breaks

**Fix Strategy**:
1. Update PDF generator to handle both formats
2. Fall back to chord roots if full names not available
3. Add validation before rendering

## Immediate Actions (Next 30 Minutes)

### Action 1: Add Detailed Whisper Logging
**File**: `backend/functions-v2/chord-detector-ecs/app.py`
**Changes**:
```python
# Before Whisper call
log(f"Whisper available: {WHISPER_AVAILABLE}")
log(f"Audio file size: {os.path.getsize(audio_path)} bytes")

# Wrap Whisper in try-except with detailed logging
try:
    log("Initializing Whisper model...")
    lyrics_service = LyricsExtractionService(model_size='tiny')  # Use tiny for speed
    log("Whisper model initialized, starting transcription...")
    lyrics_data = lyrics_service.extract_lyrics(audio_path, job_id)
    log(f"Whisper transcription complete: {len(lyrics_data.get('words', []))} words")
except Exception as e:
    log(f"WHISPER ERROR: {type(e).__name__}: {str(e)}", "ERROR")
    log(f"Full traceback: {traceback.format_exc()}", "ERROR")
```

### Action 2: Fix Pattern Analysis to Store Full Chord Names
**File**: `backend/functions-v2/chord-detector-ecs/app.py`
**Function**: `detect_key_from_progression()`
**Changes**:
- Store full chord name in pattern, not just root
- Keep root extraction for key detection logic

### Action 3: Test Locally
**Steps**:
1. Download the audio file that failed: `04 CUFF IT.m4a`
2. Run chord detection locally with Whisper
3. Identify exact error
4. Fix and redeploy

## Long-Term Improvements

1. **Pre-download Whisper models** in Docker image
2. **Add Whisper timeout** (max 5 minutes)
3. **Use Whisper API** instead of local (more reliable, faster)
4. **Add retry logic** for Whisper failures
5. **Improve key detection** algorithm
6. **Add manual overrides** for key, tempo, time signature
7. **Better error reporting** to user

## Success Criteria

After fixes, a successful job should have:
- ✅ `chordsData.lyrics.text` with full lyrics
- ✅ `chordsData.lyrics.words` with timestamps
- ✅ `chordsData.leadSheet.sections` with aligned lyrics and chords
- ✅ `patternAnalysis[].progression` with full chord names (e.g., `["Amaj7", "F#dim"]`)
- ✅ PDF displays proper chord symbols
- ✅ Nashville numbers visible in output
- ✅ Accurate key signature
- ✅ Verifiable downbeat alignment

## Next Steps

1. Run `./simple-diagnose.sh` on your latest upload to see current state
2. I'll add detailed Whisper logging
3. Fix pattern analysis chord names
4. Rebuild and deploy ECS container
5. Test with a new upload
6. Verify all data is correct
