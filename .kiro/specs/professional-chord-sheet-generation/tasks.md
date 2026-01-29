# Implementation Plan: Professional Chord Sheet Generation

## Overview

This implementation plan transforms the basic chord detection system into a professional-grade music transcription pipeline. The focus is on achieving 95%+ chord detection accuracy through ML-based models, extracting accurate metadata via LLM parsing, and generating publication-quality PDFs with staff notation and Nashville numbers.

The implementation is organized into discrete phases: audio analysis infrastructure, metadata extraction, musical analysis, Nashville number system, PDF generation, and integration.

---

## Tasks

- [x] 1. Set up enhanced audio analysis infrastructure
  - Install and configure Essentia library with pre-trained chord detection models
  - Create ChordDetectionService class with Essentia integration
  - Implement audio loading and preprocessing utilities
  - Set up test framework with hypothesis for property-based testing
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_

- [ ] 2. Implement core chord detection with ML models
  - [x] 2.1 Implement basic Essentia chord detection pipeline
    - Create detect_chords method that processes entire audio file
    - Integrate key detection to improve chord accuracy
    - Return ChordProgression with timing and confidence scores
    - _Requirements: 2.1, 2.2, 2.6_
  
  - [x] 2.2 Write property test for complete temporal coverage
    - **Property 5: Complete temporal coverage**
    - **Validates: Requirements 2.2**
  
  - [x] 2.3 Write property test for minimum temporal resolution
    - **Property 6: Minimum temporal resolution**
    - **Validates: Requirements 2.1**
  
  - [x] 2.4 Implement chord sequence refinement
    - Filter low-confidence detections (< 0.3 threshold)
    - Smooth rapid transitions (< 0.5 seconds)
    - Apply music theory constraints using key context
    - _Requirements: 2.1, 2.6_
  
  - [x] 2.5 Write property test for confidence scores
    - **Property 9: Confidence scores present**
    - **Validates: Requirements 2.6**

- [ ] 3. Implement extended chord quality detection
  - [ ] 3.1 Create enhance_chord_quality method
    - Analyze harmonic spectrum of audio segments
    - Detect 7th chords (major 7th vs dominant 7th)
    - Detect suspended chords (sus2, sus4)
    - Detect added tone chords (add9, add11)
    - Detect slash chords / inversions
    - _Requirements: 2.3, 2.4_
  
  - [ ] 3.2 Write property test for extended chord detection
    - **Property 7: Extended chord detection**
    - **Validates: Requirements 2.3**
  
  - [ ] 3.3 Write property test for slash chord notation
    - **Property 8: Slash chord notation**
    - **Validates: Requirements 2.4**

- [ ] 4. Checkpoint - Verify chord detection accuracy
  - Test chord detection on sample songs
  - Verify 95%+ accuracy target is achievable
  - Ensure all tests pass, ask the user if questions arise

- [ ] 5. Implement metadata extraction service
  - [ ] 5.1 Create YouTube API integration
    - Set up YouTube Data API v3 client
    - Implement get_video_details method to fetch title, description, channel
    - Add error handling for quota limits and video not found
    - _Requirements: 1.1_
  
  - [ ] 5.2 Write property test for YouTube API data retrieval
    - **Property 1: YouTube API data retrieval**
    - **Validates: Requirements 1.1**
  
  - [ ] 5.3 Implement LLM-powered metadata parsing
    - Create parse_with_llm method using Claude/GPT-4 API
    - Design prompt to extract song name, artist, featured artists, composer, version
    - Parse JSON response into ParsedMetadata structure
    - Implement fallback rule-based parser for LLM failures
    - _Requirements: 1.2, 1.5, 1.6_
  
  - [ ] 5.4 Write property test for LLM parsing clean output
    - **Property 2: LLM parsing produces clean structured data**
    - **Validates: Requirements 1.2, 1.5, 1.6**
  
  - [ ] 5.5 Implement artist vs uploader distinction logic
    - Compare channel name with artist extracted from title
    - Set is_official flag when channel matches artist
    - _Requirements: 1.3_
  
  - [ ] 5.6 Write property test for artist distinction
    - **Property 3: Artist vs uploader distinction**
    - **Validates: Requirements 1.3**
  
  - [ ] 5.7 Implement composer extraction from description
    - Parse description for keywords: "written by", "composed by", "songwriter"
    - Extract composer name when present
    - _Requirements: 1.4_
  
  - [ ] 5.8 Write property test for composer extraction
    - **Property 4: Composer extraction when available**
    - **Validates: Requirements 1.4**

- [ ] 6. Implement musical analysis service
  - [ ] 6.1 Create tempo and beat detection
    - Integrate Essentia RhythmExtractor2013 for BPM detection
    - Extract beat timestamps for alignment
    - _Requirements: 3.1_
  
  - [ ] 6.2 Write property test for valid tempo range
    - **Property 10: Valid tempo range**
    - **Validates: Requirements 3.1**
  
  - [ ] 6.3 Implement time signature detection
    - Analyze beat interval patterns using autocorrelation
    - Detect common time signatures (4/4, 3/4, 6/8)
    - Default to 4/4 if detection uncertain
    - _Requirements: 3.2_
  
  - [ ] 6.4 Write property test for valid time signature format
    - **Property 11: Valid time signature format**
    - **Validates: Requirements 3.2**
  
  - [ ] 6.5 Implement song structure detection (optional)
    - Use self-similarity matrix analysis to segment audio
    - Label segments as verse, chorus, bridge (best-effort)
    - Gracefully degrade if detection fails
    - _Requirements: 3.5_
  
  - [ ] 6.6 Write property test for non-overlapping sections
    - **Property 12: Non-overlapping song sections**
    - **Validates: Requirements 3.5**

- [ ] 7. Implement Nashville number system
  - [ ] 7.1 Create NashvilleNumberService class
    - Build note-to-semitone mappings
    - Define major and minor scale degree arrays
    - _Requirements: 5.1_
  
  - [ ] 7.2 Implement convert_chord method
    - Parse chord into root, quality, extensions, bass components
    - Calculate scale degree of root relative to key
    - Format number with quality indicators (uppercase/lowercase)
    - Handle slash chords with bass note scale degree
    - _Requirements: 5.1, 5.3, 5.4, 5.5_
  
  - [ ] 7.3 Write property test for Nashville number correctness
    - **Property 13: Nashville number correctness**
    - **Validates: Requirements 5.1**
  
  - [ ] 7.4 Write property test for Nashville case conventions
    - **Property 14: Nashville case conventions**
    - **Validates: Requirements 5.3**
  
  - [ ] 7.5 Write property test for extension preservation
    - **Property 15: Nashville extension preservation**
    - **Validates: Requirements 5.4**
  
  - [ ] 7.6 Write property test for slash chord notation
    - **Property 16: Nashville slash chord notation**
    - **Validates: Requirements 5.5**

- [ ] 8. Checkpoint - Verify data processing pipeline
  - Test end-to-end data flow from audio to structured data
  - Verify all Nashville numbers calculate correctly
  - Ensure all tests pass, ask the user if questions arise

- [ ] 9. Implement PDF layout engine
  - [ ] 9.1 Create LayoutEngine class
    - Implement calculate_layout method
    - Define measures_per_line configuration (4-8 measures)
    - Define staves_per_page configuration (5 staves)
    - _Requirements: 4.2, 6.3_
  
  - [ ] 9.2 Implement measure grouping logic
    - Calculate measure duration from time signature and tempo
    - Group chords into measures based on timing
    - Handle partial measures at song end
    - _Requirements: 4.2_
  
  - [ ] 9.3 Write property test for measure calculation accuracy
    - **Property 17: Measure calculation accuracy**
    - **Validates: Requirements 4.2**
  
  - [ ] 9.4 Write property test for measures per line constraint
    - **Property 21: Measures per line constraint**
    - **Validates: Requirements 6.3**
  
  - [ ] 9.5 Implement pagination logic
    - Organize measures into staff lines
    - Group staff lines into pages
    - Calculate page breaks
    - _Requirements: 4.8, 6.5_
  
  - [ ] 9.6 Write property test for multi-page pagination
    - **Property 20: Multi-page pagination**
    - **Validates: Requirements 4.8, 6.5**

- [ ] 10. Implement PDF generation service
  - [ ] 10.1 Set up PDF rendering infrastructure
    - Choose and integrate PDF library (ReportLab or similar)
    - Set up VexFlow for music notation (or alternative)
    - Create PDFDocument wrapper class
    - _Requirements: 4.1, 4.3, 4.4_
  
  - [ ] 10.2 Implement header rendering
    - Add song metadata (title, artist, composer)
    - Add musical information (key, tempo, time signature)
    - Format header with proper typography
    - _Requirements: 6.2_
  
  - [ ] 10.3 Write property test for required metadata in header
    - **Property 22: Required metadata in header**
    - **Validates: Requirements 6.2**
  
  - [ ] 10.4 Implement staff rendering
    - Draw 5-line musical staff
    - Add key signature at beginning
    - Add time signature at beginning
    - Draw measure bar lines
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [ ] 10.5 Implement chord symbol rendering
    - Place chord symbols above staff at correct x-position
    - Calculate x-position based on chord timestamp
    - Use proper font and sizing
    - _Requirements: 4.5_
  
  - [ ] 10.6 Write property test for chord positioning correspondence
    - **Property 18: Chord positioning correspondence**
    - **Validates: Requirements 4.5**
  
  - [ ] 10.7 Implement Nashville number rendering
    - Place Nashville numbers below staff
    - Align horizontally with corresponding chord symbols
    - Use distinct styling (lighter color, smaller font)
    - _Requirements: 4.6, 5.2_
  
  - [ ] 10.8 Write property test for Nashville-chord alignment
    - **Property 19: Nashville-chord alignment**
    - **Validates: Requirements 4.6, 5.2**
  
  - [ ] 10.9 Implement footer rendering
    - Add copyright/attribution text
    - Add page numbers on multi-page documents
    - _Requirements: 6.6, 6.5_

- [ ] 11. Implement orchestration service
  - [ ] 11.1 Create main orchestration workflow
    - Coordinate all services (audio, metadata, analysis, PDF)
    - Implement parallel processing where possible (metadata + audio download)
    - Add progress tracking and status updates
    - _Requirements: All_
  
  - [ ] 11.2 Implement error handling and graceful degradation
    - Handle YouTube API errors with retry logic
    - Handle LLM failures with rule-based fallback
    - Handle optional feature failures (structure detection)
    - Implement ErrorResponse model
    - _Requirements: All_
  
  - [ ] 11.3 Add DynamoDB integration
    - Update schema to store enhanced metadata
    - Store detailed chord progression with timing
    - Store musical analysis results
    - Store quality metrics (confidence, processing time)
    - _Requirements: All_
  
  - [ ] 11.4 Write integration test for end-to-end processing
    - Test complete pipeline from video ID to PDF
    - Verify all components execute successfully
    - Verify quality metrics meet requirements

- [ ] 12. Implement caching and performance optimization
  - [ ] 12.1 Add caching layer
    - Cache YouTube metadata (24 hours TTL)
    - Cache LLM parsing results (permanent)
    - Cache generated PDFs (permanent)
    - Use DynamoDB for cache storage
    - _Requirements: NFR-2, NFR-3_
  
  - [ ] 12.2 Optimize audio processing
    - Implement parallel processing for independent tasks
    - Use asyncio for I/O-bound operations
    - Optimize Essentia parameters for speed vs accuracy tradeoff
    - _Requirements: NFR-1_
  
  - [ ] 12.3 Write performance test for processing time
    - Verify 5-minute song processes in under 3.5 minutes
    - Test with various song lengths

- [ ] 13. Final checkpoint and integration testing
  - [ ] 13.1 Run comprehensive test suite
    - Execute all property-based tests (100+ iterations each)
    - Execute all unit tests
    - Execute integration tests
    - Verify 95%+ chord detection accuracy on test dataset
  
  - [ ] 13.2 Test with diverse song samples
    - Test various genres (rock, jazz, classical, pop)
    - Test various keys and time signatures
    - Test edge cases (very short songs, unusual structures)
    - Verify PDF quality and readability
  
  - [ ] 13.3 Verify all requirements met
    - Review requirements document
    - Confirm all acceptance criteria satisfied
    - Document any known limitations
    - Ensure all tests pass, ask the user if questions arise

---

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples and edge cases
- Focus on achieving 95%+ chord detection accuracy as primary success metric
- Processing time target: < 3.5 minutes for 5-minute song (acceptable for quality)

