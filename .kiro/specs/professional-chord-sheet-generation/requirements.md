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

### US-6: Publication-Quality Layout
**As a** musician  
**I want** a professionally formatted chord sheet  
**So that** I can use it for performances and share it with other musicians

**Acceptance Criteria**:
- 6.1: Clean, readable typography with proper font sizes
- 6.2: Song metadata in header (title, artist, key, tempo, time signature)
- 6.3: Measures per line optimized for readability (typically 4-8)
- 6.4: Proper spacing between staves
- 6.5: Page numbers on multi-page sheets
- 6.6: Copyright/attribution footer
- 6.7: Consistent formatting throughout document

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

### TR-4: Professional PDF Generation
- Replace basic jsPDF with music notation library
- Consider: VexFlow, abcjs, or custom SVG-to-PDF pipeline
- Support for musical symbols and notation
- High-quality rendering suitable for printing

### TR-5: Data Model Updates
- Extend DynamoDB schema to store:
  - Parsed song metadata (name, artist, composer)
  - Musical analysis (tempo, time signature)
  - Detailed chord progression with timing
  - Confidence scores for quality metrics

---

## Non-Functional Requirements

### Performance
- NFR-1: Chord detection completes within 2-3 minutes for 5-minute song (accuracy prioritized over speed)
- NFR-2: Metadata extraction completes within 10 seconds
- NFR-3: PDF generation completes within 15 seconds
- NFR-4: Total end-to-end processing under 3.5 minutes (acceptable for high accuracy)

### Quality
- NFR-5: Chord detection accuracy minimum 95% (prioritized)
- NFR-6: Metadata parsing accuracy minimum 95%
- NFR-7: PDF rendering quality suitable for 300 DPI printing

### Scalability
- NFR-8: System handles songs up to 10 minutes duration
- NFR-9: Concurrent processing of multiple jobs without degradation

---

## Dependencies

### External Services
- YouTube Data API v3 (for metadata)
- LLM API (Claude/GPT-4 for parsing)
- Optional: MusicBrainz API, Spotify API

### Libraries/Tools
- Enhanced chord detection: Essentia, librosa with better models
- Music notation: VexFlow, abcjs, or similar
- Beat tracking: librosa, madmom
- PDF generation: Advanced library supporting music notation

---

## Success Metrics

1. **Chord Coverage**: 95%+ of actual chord changes detected (PRIMARY METRIC)
2. **Chord Accuracy**: 95%+ correct chord identification
3. **Metadata Accuracy**: 95%+ correct song/artist identification
4. **User Satisfaction**: Professional-quality output suitable for performance use
5. **Processing Time**: Complete analysis in under 3.5 minutes (acceptable for quality)
6. **PDF Quality**: Readable at standard sheet music size (8.5x11")

---

## Out of Scope (Future Enhancements)

- Melody transcription
- Rhythm notation (note durations)
- Lyrics with chord placement above words
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
