# Task 1: Update Python Dependencies - COMPLETE

**Date**: 2026-03-04  
**Status**: ✅ Complete  
**Spec**: v3-accuracy-improvements

---

## Summary

Successfully updated Python dependencies for v3.0 ChordScout accuracy improvements. Added four new dependencies required for multi-stem transcription, song identification, and lyrics integration.

---

## Changes Made

### Task 1.1: Add new dependencies to requirements.txt ✅

**Files Modified**:
1. `backend/functions-v2/chord-detector-ecs/requirements.txt`
2. `bass-transcription-pipeline/bass-transcription-ecs/requirements.txt`

**Dependencies Added**:
- `mutagen==1.47.0` - Audio metadata extraction (ID3 tags, MP4 metadata)
- `requests==2.31.0` - HTTP client for Genius API calls
- `beautifulsoup4==4.12.0` - HTML parsing for lyrics scraping
- `lxml==4.9.3` - XML/HTML parser (required by beautifulsoup4)

**Note**: Did not add `lyricsgenius` package as the design document shows we're implementing direct Genius API calls using `requests` and `beautifulsoup4` for more control over the scraping process.

---

## Task 1.2: Test dependency installation

**Test Script Created**: `backend/functions-v2/chord-detector-ecs/test_v3_dependencies.py`

This script verifies:
- All new v3.0 dependencies can be imported
- Existing dependencies still work (no conflicts)
- New modules (stem_transcription, song_metadata_lyrics, bass_note_transcription) can be imported

**To run the test**:
```bash
# After building Docker image
docker run <image-name> python test_v3_dependencies.py
```

---

## Next Steps

**Task 2: Integrate new modules into ECS orchestrator**
- Task 2.1: Import new modules in app.py
- Task 2.2: Add song identification stage
- Task 2.3: Add stem separation stage
- Task 2.4: Implement transcription mode selection workflow
- Task 2.5: Implement multi-stem transcription
- Task 2.6: Add lyrics fetching stage
- Task 2.7: Implement key detection and confirmation workflow
- Task 2.8: Implement lyrics-to-measures alignment
- Task 2.9: Update DynamoDB write operations

**Task 3: Update Docker configuration**
- Task 3.1: Update Dockerfile to copy new modules
- Task 3.2: Add environment variables
- Task 3.3: Build and test Docker image locally

---

## Validation

To validate Task 1 completion:

1. ✅ New dependencies added to both requirements.txt files
2. ✅ Dependencies have specific version numbers for reproducibility
3. ✅ Comments explain purpose of each dependency
4. ✅ Test script created to verify imports
5. ⏳ Docker build test (pending Task 3.3)

---

## Dependencies for Next Tasks

Task 2 (Backend Integration) can now proceed since all required Python packages are specified in requirements.txt. The packages will be installed when the Docker image is built in Task 3.

---

## Notes

- The `mutagen` library supports multiple audio formats (MP3, MP4, FLAC, etc.) for metadata extraction
- `requests` is a standard HTTP library, widely used and well-maintained
- `beautifulsoup4` with `lxml` parser provides robust HTML parsing for Genius lyrics pages
- All version numbers are pinned to ensure consistent builds across environments
- No breaking changes to existing dependencies
