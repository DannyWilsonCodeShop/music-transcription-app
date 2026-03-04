# Lyrics-Chord Alignment Implementation Tasks

**Feature**: Align lyrics with chords to create professional lead sheets  
**Status**: Ready for Implementation  
**Estimated Duration**: 2-3 days  

---

## Task Breakdown

### Phase 1: Backend Core Algorithms (Day 1)

- [x] 1. Implement helper functions
  - [x] 1.1 Create `find_word_at_timestamp()` function
    - Input: words list, timestamp, tolerance
    - Output: word index or None
    - Handle edge cases: before word, between words, after all words
  - [x] 1.2 Create `calculate_measure_number()` function
    - Convert timestamp to measure number based on tempo and time signature
  - [x] 1.3 Create `get_words_in_segment()` function
    - Filter words by time range
  - [x] 1.4 Create `get_chords_in_segment()` function
    - Filter chords by time range

- [x] 2. Implement chord-to-word alignment
  - [x] 2.1 Create `align_chords_to_words()` function
    - For each chord, find word at that timestamp
    - Determine position type (word_start, mid_word, between_words, instrumental)
    - Return aligned chords with word associations
  - [x] 2.2 Handle edge case: multiple chords per word
    - Create `handle_multiple_chords_per_word()` function
    - Distribute chords evenly across word length
  - [x] 2.3 Handle edge case: rapid chord changes
    - Create `ensure_chord_spacing()` function
    - Implement `abbreviate_chord()` for long chord names

- [x] 3. Implement phrase/line grouping
  - [x] 3.1 Create `group_into_lines()` function
    - Use Whisper segments as phrase boundaries
    - Target 2-4 measures per line
    - Break at natural boundaries (punctuation, silence)
  - [x] 3.2 Create `finalize_line()` function
    - Calculate measure numbers
    - Build lyrics string
    - Map chords to character positions
  - [x] 3.3 Create `ends_with_punctuation()` helper
    - Check if segment ends with punctuation marks

- [x] 4. Implement section detection and labeling
  - [x] 4.1 Create `detect_and_label_sections()` function
    - Use existing song_structure from chord detection
    - Correlate with lyric line boundaries
    - Assign standard labels (Verse 1, Chorus, Bridge, etc.)
  - [x] 4.2 Create `create_chord_fingerprint()` function
    - Generate pattern signature for chord progression
  - [x] 4.3 Create section classification helpers
    - `is_verse_like()` - heuristic for verse detection
    - `is_chorus_like()` - heuristic for chorus detection
    - `is_bridge_like()` - heuristic for bridge detection
  - [x] 4.4 Handle instrumental sections
    - Create `format_instrumental_section()` function
    - Display chords in grid format with measure numbers

- [x] 5. Create main alignment function
  - [x] 5.1 Implement `align_lyrics_with_chords()` function
    - Orchestrate all alignment steps
    - Handle missing data gracefully
    - Return AlignedLeadSheet structure
  - [x] 5.2 Add comprehensive logging
    - Log each alignment step
    - Log statistics (chords aligned, lines created, sections identified)

---

### Phase 2: Backend Integration (Day 1-2)

- [x] 6. Integrate with chord detection pipeline
  - [x] 6.1 Update `detect_chords()` function in app.py
    - Check if lyrics data exists in job
    - Call `align_lyrics_with_chords()` after chord detection
    - Add leadSheet to chords_data output
  - [x] 6.2 Update `update_job_with_chords()` function
    - Include leadSheet in DynamoDB update
    - Handle Decimal conversion for nested structures

- [x] 7. Add error handling
  - [x] 7.1 Validate input data
    - Check for missing lyrics data
    - Check for missing chord data
    - Log warnings for incomplete data
  - [x] 7.2 Handle timestamp mismatches
    - Implement adaptive tolerance in word finding
    - Log misalignment issues
  - [x] 7.3 Handle empty sections
    - Create placeholder instrumental sections
    - Log warnings for sections without lines

---

### Phase 3: Backend Testing (Day 2)

- [x] 8. Create unit tests
  - [x] 8.1 Create `test_lyrics_alignment.py`
  - [x] 8.2 Test `find_word_at_timestamp()`
    - Test exact match
    - Test anticipation (before word)
    - Test between words
    - Test after all words
  - [x] 8.3 Test `align_chords_to_words()`
    - Test basic alignment
    - Test multiple chords per word
    - Test instrumental sections
  - [x] 8.4 Test `group_into_lines()`
    - Test phrase grouping
    - Test measure calculation
    - Test line breaking
  - [x] 8.5 Test `detect_and_label_sections()`
    - Test section labeling
    - Test verse numbering
    - Test repeated sections
  - [x] 8.6 Test edge cases
    - Multiple chords per word
    - Rapid chord changes
    - Instrumental sections
    - Syncopated lyrics

- [x] 9. Create integration tests
  - [x] 9.1 Test with sample song data
    - Load test chords and lyrics
    - Run full alignment pipeline
    - Verify output structure
  - [x] 9.2 Test with various genres
    - Pop song (simple structure)
    - Jazz song (complex chords)
    - Rock song (instrumental sections)

- [x] 10. Local testing
  - [x] 10.1 Test with "That's What I Like" audio file
    - Verify alignment accuracy
    - Check section detection
    - Validate line grouping
  - [x] 10.2 Test with "Plastic Off The Sofa" audio file
    - Test with different tempo/style
    - Verify edge case handling

---

### Phase 4: Frontend Display (Day 2)

- [x] 11. Create LeadSheetDisplay component
  - [x] 11.1 Create `src/components/LeadSheetDisplay.tsx`
    - Define TypeScript interfaces
    - Implement component structure
    - Add metadata header display
  - [x] 11.2 Create LyricsLine component
    - Position chord symbols above lyrics
    - Display measure numbers
    - Handle instrumental sections
  - [x] 11.3 Create SectionLabel component
    - Display section headers
    - Style section boundaries

- [x] 12. Add CSS styling
  - [x] 12.1 Create lead sheet styles
    - Monospace font for alignment
    - Chord symbol positioning
    - Line spacing and margins
  - [x] 12.2 Style section labels
    - Bold headers
    - Border separators
  - [x] 12.3 Style measure numbers
    - Left margin positioning
    - Subtle color
  - [x] 12.4 Add responsive design
    - Handle different screen sizes
    - Adjust font sizes for mobile

- [x] 13. Integrate with App.tsx
  - [x] 13.1 Import LeadSheetDisplay component
  - [x] 13.2 Add conditional rendering
    - Show lead sheet if leadSheet data exists
    - Fall back to chord-only display if no lyrics
  - [x] 13.3 Add toggle for debug mode
    - Show/hide timestamps
    - Show/hide measure numbers

- [x] 14. Update TypeScript types
  - [x] 14.1 Update `src/services/transcriptionService.ts`
    - Add AlignedLeadSheet interface
    - Add AlignedLine interface
    - Add AlignedChord interface
  - [x] 14.2 Update TranscriptionJob type
    - Add leadSheet field to chordsData

---

### Phase 5: PDF Generation (Day 2-3)

- [x] 15. Update PDF generator
  - [x] 15.1 Update `backend/functions-v2/pdf-generator/index.js`
    - Check if leadSheet data exists
    - Use aligned data instead of raw chords
  - [x] 15.2 Implement `generateLeadSheetPDF()` function
    - Render metadata header
    - Render sections with labels
    - Render lines with chords and lyrics
  - [x] 15.3 Implement `renderLineWithChords()` function
    - Position chord symbols above lyrics
    - Add measure numbers in margin
    - Handle instrumental sections
  - [x] 15.4 Handle page breaks
    - Don't break sections across pages
    - Add section headers after page breaks

- [x] 16. Test PDF output
  - [x] 16.1 Generate test PDFs
    - Test with various songs
    - Verify chord positioning
    - Check page layout
  - [x] 16.2 Verify readability
    - Check font sizes
    - Verify spacing
    - Test print quality

---

### Phase 6: Testing & Refinement (Day 3)

- [x] 17. End-to-end testing
  - [x] 17.1 Test complete pipeline
    - Upload audio file
    - Verify lyrics extraction
    - Verify chord detection
    - Verify alignment
    - Check frontend display
    - Download and verify PDF
  - [x] 17.2 Test with diverse songs
    - Pop: "That's What I Like"
    - Rock: "Plastic Off The Sofa"
    - Jazz: Complex chord progressions
    - Instrumental: Sections without lyrics

- [x] 18. Performance testing
  - [x] 18.1 Measure alignment time
    - Should complete in < 1 second
    - Profile slow operations
  - [x] 18.2 Test with long songs
    - 10+ minute songs
    - 500+ words
    - 200+ chords

- [x] 19. Accuracy validation
  - [x] 19.1 Manual verification
    - Check 20 test songs
    - Verify chord-to-word alignment (target: 95% accuracy)
    - Verify section detection (target: 90% accuracy)
  - [x] 19.2 Fix alignment issues
    - Adjust tolerance values
    - Refine heuristics
    - Handle edge cases

- [x] 20. Bug fixes and refinement
  - [x] 20.1 Fix any discovered bugs
  - [x] 20.2 Refine alignment heuristics
  - [x] 20.3 Improve section detection
  - [x] 20.4 Optimize performance

---

### Phase 7: Deployment (Day 3)

- [x] 21. Backend deployment
  - [x] 21.1 Commit code changes
    - Commit alignment functions
    - Commit integration code
    - Commit tests
  - [x] 21.2 Rebuild Docker image
    - Run build-and-push.sh
    - Verify image includes new code
  - [x] 21.3 Test on dev environment
    - Upload test file
    - Verify alignment works
    - Check CloudWatch logs

- [x] 22. Frontend deployment
  - [x] 22.1 Commit frontend changes
    - Commit LeadSheetDisplay component
    - Commit CSS styles
    - Commit type updates
  - [x] 22.2 Deploy to Amplify
    - Push to dev branch
    - Monitor deployment
    - Verify deployment success
  - [x] 22.3 Test deployed frontend
    - Upload file on dev site
    - Verify lead sheet display
    - Test PDF download

- [x] 23. PDF generator deployment
  - [x] 23.1 Deploy updated Lambda
    - Package and deploy
    - Verify deployment
  - [x] 23.2 Test PDF generation
    - Trigger PDF generation
    - Download and verify PDF
    - Check formatting

- [x] 24. Final verification
  - [x] 24.1 Complete end-to-end test on dev
    - Upload multiple test files
    - Verify all features work
    - Check error handling
  - [x] 24.2 Monitor logs
    - Check for errors
    - Verify performance
    - Check alignment statistics

---

## Success Criteria

✅ All unit tests passing  
✅ Integration tests passing  
✅ Chord-to-word alignment 95%+ accurate  
✅ Section detection 90%+ accurate  
✅ Alignment completes in < 1 second  
✅ Frontend displays lead sheet correctly  
✅ PDF output matches frontend display  
✅ Works with diverse song types  
✅ Deployed to dev environment  
✅ No critical bugs  

---

## Notes

- Focus on getting core alignment working first (Phase 1-2)
- Test thoroughly before moving to frontend (Phase 3)
- Frontend and PDF can be developed in parallel (Phase 4-5)
- Leave time for refinement and bug fixes (Phase 6)
- Deploy incrementally and test at each stage (Phase 7)

---

## Dependencies

- ✅ Lyrics extraction with word timestamps (Complete)
- ✅ Chord detection with measure alignment (Complete)
- ✅ Song structure detection (Complete)
- ⚠️ Downbeat detection (In Progress - not blocking)

---

## Estimated Time

- Phase 1: Backend Core - 4-6 hours
- Phase 2: Integration - 2-3 hours
- Phase 3: Testing - 3-4 hours
- Phase 4: Frontend - 4-5 hours
- Phase 5: PDF - 3-4 hours
- Phase 6: Refinement - 4-6 hours
- Phase 7: Deployment - 2-3 hours

**Total**: 22-31 hours (2.75-3.9 days)
