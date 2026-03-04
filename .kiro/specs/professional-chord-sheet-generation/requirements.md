# Professional Chord Sheet Generation - Requirements

**Feature Name**: professional-chord-sheet-generation  
**Created**: 2026-01-29  
**Status**: Requirements Approved  
**Timeline**: 3 weeks  
**Priority**: Chord Detection Accuracy

---

## Overview

Transform the current basic chord detection into a professional-grade music transcription system that generates publication-quality chord sheets with comprehensive musical information, accurate metadata extraction, and proper music notation formatting.

---

## Problem Statement

### Current Limitations

1. **Incomplete Chord Detection**
   - Only detecting 3-5 chords for a 5-minute song
   - Missing most chord changes throughout the song
   - Low accuracy in chord recognition

2. **Poor Visual Presentation**
   - No musical staff notation
   - Chords displayed in simple list format
   - Not professional or publication-ready
   - Missing standard music notation elements

3. **Inaccurate Metadata**
   - Just copying YouTube video title verbatim
   - No extraction of actual song name vs. video description
   - Missing song author/composer information
   - No distinction between song artist and video uploader

4. **Missing Musical Information**
   - No time signature detection
   - No tempo (BPM) detection
   - Key signature shown but not prominently
   - No chord timing/duration on staff

5. **Unprofessional Layout**
   - Not suitable for musicians to read from
   - Missing standard chord sheet formatting
   - No measure lines or bar divisions
   - Nashville numbers not aligned with chords on staff

---

## User Stories

### US-1: Accurate Song Metadata Extraction
**As a** musician  
**I want** the system to identify the actual song name, artist, and composer from the video metadata  
**So that** I have accurate attribution and can organize my chord sheets properly

**Acceptance Criteria**:
- 1.1: System extracts video title and description from YouTube
- 1.2: AI/LLM parses title to identify: song name, artist, featuring artists, version info
- 1.3: System distinguishes between song artist and video uploader
- 1.4: Composer/songwriter information extracted when available
- 1.5: Handles common title formats: "Artist - Song", "Song by Artist", "Artist: Song", etc.
- 1.6: Removes extraneous info like "(Official Video)", "[HD]", "Lyrics", etc.

### US-2: Comprehensive Chord Detection
**As a** musician  
**I want** all chord changes throughout the entire song detected accurately  
**So that** I can play along with the complete harmonic structure

**Acceptance Criteria**:
- 2.1: System detects chord changes at minimum 1-second resolution
- 2.2: Chord detection covers entire song duration (not just first minute)
- 2.3: Detects extended chords (7th, 9th, sus, add, etc.)
- 2.4: Identifies chord inversions when present
- 2.5: Minimum 80% of actual chord changes detected
- 2.6: Chord confidence scores provided for quality assessment

### US-3: Musical Analysis
**As a** musician  
**I want** complete musical analysis including tempo, time signature, and key  
**So that** I understand the song's musical structure

**Acceptance Criteria**:
- 3.1: Tempo (BPM) detected and displayed
- 3.2: Time signature detected (4/4, 3/4, 6/8, etc.)
- 3.3: Key signature prominently displayed
- 3.4: Key changes detected if present
- 3.5: Song structure identified (verse, chorus, bridge) if possible

### US-4: Professional Staff Notation
**As a** musician  
**I want** chords displayed on a musical staff with proper notation  
**So that** I can read it like standard sheet music

**Acceptance Criteria**:
- 4.1: Chords displayed on 5-line musical staff
- 4.2: Measure lines (bar lines) divide music into measures
- 4.3: Time signature shown at beginning of staff
- 4.4: Key signature shown at beginning of staff
- 4.5: Chord symbols placed above staff at correct timing
- 4.6: Nashville numbers placed below staff aligned with chords
- 4.7: Repeat signs and navigation markers included
- 4.8: Multiple staves for longer songs with proper page breaks

### US-5: Nashville Number System Integration
**As a** Nashville session musician  
**I want** Nashville numbers accurately calculated and displayed under each chord  
**So that** I can transpose easily and communicate with other musicians

**Acceptance Criteria**:
- 5.1: Nashville numbers calculated correctly for detected key
- 5.2: Numbers placed directly below corresponding chord on staff
- 5.3: Chord quality indicated (uppercase for major, lowercase for minor)
- 5.4: Extended chord qualities shown (7, maj7, sus4, etc.)
- 5.5: Slash chords notated properly (e.g., "1/3" for C/E in key of C)

### US-6: Lyrics Extraction and Alignment
**As a** musician  
**I want** song lyrics extracted and aligned with chords  
**So that** I can see which chords to play over which lyrics

**Acceptance Criteria**:
- 6.1: System extracts lyrics from audio using speech-to-text
- 6.2: Lyrics are timestamped at word or phrase level
- 6.3: Lyrics are aligned with chord changes based on timing
- 6.4: Lyrics are formatted in verse/chorus structure when possible
- 6.5: Chords are positioned above the corresponding lyrics
- 6.6: Nashville numbers appear below chords
- 6.7: Handles instrumental sections (no lyrics)
- 6.8: Accuracy minimum 85% for clear vocal tracks

### US-7: Publication-Quality Layout
**As a** musician  
**I want** a professionally formatted chord sheet  
**So that** I can use it for performances and share it with other musicians

**Acceptance Criteria**:
- 7.1: Clean, readable typography with proper font sizes
- 7.2: Song metadata in header (title, artist, key, tempo, time signature)
- 7.3: Lyrics with chords above them in traditional chord sheet format
- 7.4: Nashville numbers below chords for easy transposition
- 7.5: Proper spacing between lines and sections
- 7.6: Page numbers on multi-page sheets
- 7.7: Copyright/attribution footer
- 7.8: Consistent formatting throughout document
- 7.9: Optimized to fit most songs on 1-2 pages

---

## Technical Requirements

### TR-1: Enhanced Chord Detection Algorithm
- Use more sophisticated chord detection library or model
- Consider: Essentia, Madmom (if compatibility fixed), or ML-based approach
- Analyze entire audio file, not just samples
- Detect chord changes with sub-second precision

### TR-2: Metadata Extraction Service
- Integrate YouTube Data API v3 for video metadata
- Use LLM (Claude, GPT-4) to parse and structure song information
- Fallback to MusicBrainz or Spotify API for song data enrichment
- Cache metadata to avoid repeated API calls

### TR-3: Musical Analysis Engine
- Tempo detection using beat tracking algorithms
- Time signature detection from rhythmic patterns
- Key detection with confidence scoring
- Song structure analysis (optional, nice-to-have)

### TR-4: Lyrics Extraction System
- Use Whisper (OpenAI) for speech-to-text transcription
- Extract lyrics with word-level timestamps
- Separate vocals using Demucs (already available in pipeline)
- Handle instrumental sections gracefully
- Store lyrics data in DynamoDB with timing information

### TR-5: Lyrics-Chord Alignment Engine
- Match lyrics timestamps with chord timestamps
- Group lyrics into lines based on natural phrasing
- Position chords above corresponding lyrics
- Handle cases where chords change mid-word
- Format output for traditional chord sheet layout

### TR-6: Professional PDF Generation
- Replace basic jsPDF with lyrics-over-chords layout
- Traditional chord sheet format (chords above lyrics)
- Nashville numbers below chords in smaller font
- Support for musical symbols if needed
- High-quality rendering suitable for printing
- Optimized layout to fit on 1-2 pages

### TR-7: Data Model Updates
- Extend DynamoDB schema to store:
  - Parsed song metadata (name, artist, composer)
  - Musical analysis (tempo, time signature)
  - Detailed chord progression with timing
  - Lyrics with word-level timestamps
  - Lyrics-chord alignment data
  - Confidence scores for quality metrics

---

## Non-Functional Requirements

### Performance
- NFR-1: Chord detection completes within 2-3 minutes for 5-minute song
- NFR-2: Lyrics extraction completes within 1-2 minutes for 5-minute song
- NFR-3: Metadata extraction completes within 10 seconds
- NFR-4: PDF generation completes within 15 seconds
- NFR-5: Total end-to-end processing under 5 minutes

### Quality
- NFR-6: Chord detection accuracy minimum 85%
- NFR-7: Lyrics transcription accuracy minimum 85% for clear vocals
- NFR-8: Metadata parsing accuracy minimum 95%
- NFR-9: PDF rendering quality suitable for 300 DPI printing

### Scalability
- NFR-10: System handles songs up to 10 minutes duration
- NFR-11: Concurrent processing of multiple jobs without degradation

---

## Dependencies

### External Services
- YouTube Data API v3 (for metadata)
- LLM API (Claude/GPT-4 for parsing)
- Optional: MusicBrainz API, Spotify API

### Libraries/Tools
- Lyrics extraction: Whisper (OpenAI) - open source, highly accurate
- Vocal separation: Demucs (already in pipeline)
- Enhanced chord detection: Essentia, librosa with better models
- Lyrics-chord alignment: Custom algorithm based on timestamps
- PDF generation: jsPDF with custom chord sheet layout

---

## Success Metrics

1. **Chord Coverage**: 85%+ of actual chord changes detected
2. **Chord Accuracy**: 85%+ correct chord identification
3. **Lyrics Accuracy**: 85%+ correct transcription for clear vocals
4. **Lyrics-Chord Alignment**: 90%+ chords positioned correctly over lyrics
5. **Metadata Accuracy**: 95%+ correct song/artist identification
6. **User Satisfaction**: Professional-quality output suitable for performance use
7. **Processing Time**: Complete analysis in under 5 minutes
8. **PDF Quality**: Readable and printable chord sheet format

---

## Out of Scope (Future Enhancements)

- Melody transcription
- Rhythm notation (note durations)
- Multiple instrument parts
- Audio playback with chord highlighting
- Interactive chord sheet editor
- Transposition tool in UI
- MIDI export

---

## Stakeholder Decisions ✅

1. **Priority**: ✅ **Chord detection accuracy** (Primary focus)
2. **Budget**: ✅ **Approved** for all API costs (YouTube Data API, LLM, Music APIs)
3. **Timeline**: ✅ **3 weeks** for full implementation
4. **Quality vs. Speed**: ✅ **Slower processing (2-3 min) with 95%+ accuracy** preferred over speed
5. **Notation Style**: Traditional staff notation with Nashville numbers

---

## Next Steps

1. **Review & Approve**: Stakeholder reviews requirements
2. **Design Phase**: Create detailed technical design
3. **Prototype**: Build proof-of-concept for chord detection improvement
4. **Iterate**: Refine based on test results
5. **Implement**: Full feature development
6. **Test**: Comprehensive testing with various songs
7. **Deploy**: Gradual rollout with monitoring

---

## Notes

- Current system uses librosa with basic chromagram analysis
- Detecting only 3-5 chords suggests algorithm needs significant improvement
- Professional layout requires complete PDF generation rewrite
- Metadata extraction is new capability requiring LLM integration
- This is a major enhancement, not a quick fix
