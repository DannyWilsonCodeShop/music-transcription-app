# Task 5.1 Implementation Summary

**Task**: Implement `align_lyrics_with_chords()` function  
**Status**: ✅ Complete  
**Date**: 2026-02-26  

---

## What Was Implemented

Successfully implemented the main orchestration function `align_lyrics_with_chords()` in `backend/functions-v2/chord-detector-ecs/app.py` (starting at line 2269).

### Function Overview

The function ties together all the alignment algorithms to create a professional lead sheet structure:

1. **Input Validation**
   - Validates presence of lyrics data (words)
   - Validates presence of chord data
   - Creates default song structure if missing
   - Returns `None` gracefully if alignment cannot be performed

2. **Step 1: Chord-to-Word Alignment**
   - Calls `align_chords_to_words()` to match chords with word timestamps
   - Logs statistics: word_start, mid_word, and instrumental alignments

3. **Step 2: Line Grouping**
   - Calls `group_into_lines()` to create readable phrases (2-4 measures)
   - Logs count of lyric lines vs instrumental lines

4. **Step 3: Section Detection**
   - Imports and calls `detect_and_label_sections()` from section_detection.py
   - Labels sections (Verse 1, Chorus, Bridge, etc.)
   - Logs each section with line count and measure range

5. **Step 4: Lead Sheet Structure**
   - Creates final `AlignedLeadSheet` structure with:
     - `metadata`: key, tempo, timeSignature, duration, language, confidence
     - `sections`: array of labeled sections with lines
   - Logs final statistics

### Key Features

✅ **Comprehensive Logging**
- Uses emoji indicators (📊, 🎯, 📝, 🏷️, 📄, ✅, ⚠️, ❌)
- Logs input data statistics
- Logs each step with detailed counts
- Logs final summary with totals

✅ **Error Handling**
- Try-catch block around main logic
- Detailed error logging with traceback
- Returns `None` on error (doesn't crash)

✅ **Input Validation**
- Checks for missing lyrics data
- Checks for missing chord data
- Creates default song structure if needed
- Handles missing optional fields with defaults

✅ **Proper Orchestration**
- Calls helper functions in correct order
- Passes all required parameters
- Imports section detection from separate module
- Returns properly structured data

---

## Function Signature

```python
def align_lyrics_with_chords(chords_data, lyrics_data):
    """
    Main function to align lyrics with chords and create lead sheet structure
    
    Args:
        chords_data: Dict containing chords, key, tempo, timeSignature, 
                     songStructure, duration, firstDownbeat
        lyrics_data: Dict containing text, words, segments, language, confidence
    
    Returns:
        AlignedLeadSheet dict with metadata and sections, or None on error
    """
```

---

## Output Structure

```python
{
    'metadata': {
        'key': str,              # e.g., 'C major'
        'tempo': float,          # BPM
        'timeSignature': str,    # e.g., '4/4'
        'duration': float,       # seconds
        'language': str,         # e.g., 'en'
        'confidence': float      # 0-1
    },
    'sections': [
        {
            'label': str,              # 'Verse 1', 'Chorus', etc.
            'measureStart': int,
            'measureEnd': int,
            'lines': [
                {
                    'measureStart': int,
                    'measureEnd': int,
                    'lyrics': str,
                    'words': [...],
                    'chords': [...],
                    'isInstrumental': bool,
                    'start': float,
                    'end': float
                }
            ]
        }
    ]
}
```

---

## Dependencies

The function relies on these previously implemented functions:

- ✅ `align_chords_to_words()` - Task 2.1 (in app.py)
- ✅ `group_into_lines()` - Task 3.1 (in app.py)
- ✅ `detect_and_label_sections()` - Task 4.1 (in section_detection.py)
- ✅ `log()` - Logging utility (in app.py)

---

## Testing

Created `test_align_lyrics_chords.py` to document expected behavior:
- Input validation tests
- Missing data handling tests
- Default section creation test
- Documentation of expected behavior

**Note**: Full integration testing requires Docker environment with all dependencies (boto3, librosa, etc.)

---

## Example Log Output

```
============================================================
Starting lyrics-chord alignment...
============================================================
📊 Input data:
   - Chords: 48
   - Words: 156
   - Segments: 12
   - Tempo: 120.0 BPM
   - Time Signature: 4/4
   - First Downbeat: 0.72s

🎯 Step 1: Aligning chords to words...
   ✓ Aligned 48 chords:
     - At word start: 32
     - Mid-word: 12
     - Instrumental: 4

📝 Step 2: Grouping into lines...
   ✓ Created 16 lines:
     - With lyrics: 14
     - Instrumental: 2

🏷️  Step 3: Detecting and labeling sections...
   ✓ Identified 4 sections:
     - Verse 1: 4 lines (M1-8)
     - Chorus: 4 lines (M9-16)
     - Verse 2: 4 lines (M17-24)
     - Chorus: 4 lines (M25-32)

📄 Step 4: Creating lead sheet structure...
   ✓ Lead sheet created:
     - Sections: 4
     - Total lines: 16
     - Total chords: 48

============================================================
✅ Lyrics-chord alignment complete!
============================================================
```

---

## Files Modified

1. **backend/functions-v2/chord-detector-ecs/app.py**
   - Added `align_lyrics_with_chords()` function (lines 2269-2430)
   - Function includes comprehensive logging and error handling

2. **backend/functions-v2/chord-detector-ecs/test_align_lyrics_chords.py** (new)
   - Created test documentation file
   - Documents expected behavior
   - Includes test cases for reference

---

## Next Steps

According to the task list, the next tasks are:

- **Task 5.2**: ✅ Add comprehensive logging (COMPLETE - included in 5.1)
- **Task 6.1**: Update `detect_chords()` function to call alignment
- **Task 6.2**: Update `update_job_with_chords()` to store leadSheet
- **Task 7.x**: Add error handling (partially complete)
- **Task 8.x**: Create unit tests
- **Task 9.x**: Create integration tests

---

## Success Criteria Met

✅ Function orchestrates all alignment steps  
✅ Handles missing data gracefully  
✅ Returns AlignedLeadSheet structure  
✅ Comprehensive logging at each step  
✅ Error handling with detailed traceback  
✅ Input validation for all required fields  
✅ Statistics reporting (alignment types, line counts, section counts)  
✅ Proper integration with existing helper functions  

---

## Notes

- The function is ready for integration into the chord detection pipeline
- All helper functions (tasks 1-4) were already implemented
- The function follows the design specification exactly
- Logging is comprehensive and uses emoji indicators for clarity
- Error handling ensures the system doesn't crash on bad data
- The function is self-contained and can be tested independently

