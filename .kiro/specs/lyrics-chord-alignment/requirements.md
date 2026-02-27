# Lyrics-Chord Alignment Requirements

**Feature**: Align lyrics with chords to create professional lead sheets  
**Priority**: High  
**Status**: Ready for Implementation  
**Estimated Effort**: 2-3 days  

---

## Overview

Now that we have both lyrics (with word-level timestamps from Whisper) and chords (with measure-aligned timestamps), we need to align them together to create a professional lead sheet where chord symbols appear above the exact words where chord changes occur.

---

## User Stories

### 1. As a musician, I want to see chord symbols positioned above the exact lyrics where chord changes occur
**Acceptance Criteria:**
- Chord symbols appear directly above the syllable/word where the chord change happens
- Alignment is accurate to within 0.1 seconds
- Multiple chords within a single word are handled gracefully
- Instrumental sections show chords without lyrics

### 2. As a musician, I want the lead sheet to follow standard notation conventions
**Acceptance Criteria:**
- Lyrics are grouped into phrases/lines (typically 2-4 measures per line)
- Chord symbols are positioned above the staff
- Measure numbers are shown at the start of each line
- Section labels (Verse, Chorus, Bridge) are clearly marked
- Repeated sections use repeat signs or "2x" notation

### 3. As a musician, I want to see the song structure clearly
**Acceptance Criteria:**
- Sections are labeled (Intro, Verse 1, Chorus, Verse 2, etc.)
- Repeated sections are identified and can be shown once with repeat notation
- Bridge, solo, and instrumental sections are clearly marked
- Section boundaries align with musical phrases

### 4. As a musician, I want accurate timing even when lyrics are sparse
**Acceptance Criteria:**
- Instrumental intros show chords with measure numbers
- Instrumental breaks maintain chord progression display
- Sustained notes/words show chord changes that occur during them
- Rests and pauses are represented appropriately

---

## Technical Requirements

### 1. Lyrics-Chord Timestamp Alignment
**Input:**
- Lyrics data with word-level timestamps from Whisper
- Chord data with measure-aligned timestamps
- Song structure data (sections)

**Output:**
- Aligned data structure mapping chords to lyrics positions

**Algorithm:**
```
For each chord change:
  1. Find the word that is being sung at that timestamp
  2. If word starts within 0.2s of chord change, align to word start
  3. If chord change is mid-word, align to that word
  4. If no word (instrumental), mark as instrumental section
  5. Store chord position relative to word/phrase
```

### 2. Line Breaking and Phrase Grouping
**Requirements:**
- Group lyrics into lines based on musical phrases
- Typically 2-4 measures per line
- Break at natural phrase boundaries (punctuation, breath marks)
- Maintain consistent line length for readability
- Consider page width constraints

**Algorithm:**
```
For each section:
  1. Identify phrase boundaries (silence > 0.5s, punctuation)
  2. Group phrases into lines (target: 2-4 measures)
  3. Ensure chords fit above lyrics without overlap
  4. Break long lines at natural word boundaries
  5. Align measure numbers to line starts
```

### 3. Chord Symbol Positioning
**Requirements:**
- Position chord symbols directly above the syllable where change occurs
- Handle multiple chords per word
- Handle chords in instrumental sections
- Maintain minimum spacing between chord symbols
- Use standard notation conventions

**Spacing Rules:**
- Minimum 1 character space between chord symbols
- Chord symbols don't overlap with lyrics
- Long chord names (e.g., "Cmaj7#11") get adequate space
- Slash chords (e.g., "C/G") are formatted correctly

### 4. Section Labeling
**Requirements:**
- Detect section boundaries from song structure analysis
- Label sections with standard names (Verse, Chorus, Bridge, etc.)
- Number repeated sections (Verse 1, Verse 2, etc.)
- Identify instrumental sections (Intro, Solo, Outro)
- Use repeat notation for identical sections

**Section Detection:**
- Use existing song structure data from chord detection
- Correlate with lyrics phrase boundaries
- Identify repeated chord progressions
- Match with common song structures (ABABCB, AABA, etc.)

---

## Data Structures

### Input: Lyrics Data (from Whisper)
```json
{
  "text": "Full lyrics text",
  "language": "en",
  "segments": [
    {
      "start": 0.5,
      "end": 3.2,
      "text": "We're no strangers to love"
    }
  ],
  "words": [
    {"word": "We're", "start": 0.5, "end": 0.8},
    {"word": "no", "start": 0.9, "end": 1.1},
    {"word": "strangers", "start": 1.2, "end": 1.6},
    {"word": "to", "start": 1.7, "end": 1.8},
    {"word": "love", "start": 1.9, "end": 3.2}
  ]
}
```

### Input: Chord Data (from chord detection)
```json
{
  "chords": [
    {
      "chord": "Fmaj7",
      "start": 0.72,
      "end": 2.16,
      "measure": 1,
      "beat": 1
    },
    {
      "chord": "G7",
      "start": 2.16,
      "end": 3.60,
      "measure": 2,
      "beat": 1
    }
  ],
  "songStructure": [
    {
      "label": "Verse",
      "start": 0.0,
      "end": 16.0,
      "measureStart": 1,
      "measureEnd": 8
    }
  ]
}
```

### Output: Aligned Lead Sheet Data
```json
{
  "sections": [
    {
      "label": "Verse 1",
      "measureStart": 1,
      "measureEnd": 8,
      "lines": [
        {
          "measureStart": 1,
          "measureEnd": 2,
          "lyrics": "We're no strangers to love",
          "chords": [
            {
              "chord": "Fmaj7",
              "position": 0,
              "wordIndex": 0,
              "word": "We're"
            },
            {
              "chord": "G7",
              "position": 15,
              "wordIndex": 3,
              "word": "to"
            }
          ]
        },
        {
          "measureStart": 3,
          "measureEnd": 4,
          "lyrics": "You know the rules and so do I",
          "chords": [
            {
              "chord": "Am7",
              "position": 0,
              "wordIndex": 0,
              "word": "You"
            }
          ]
        }
      ]
    },
    {
      "label": "Chorus",
      "measureStart": 9,
      "measureEnd": 16,
      "lines": [...]
    }
  ]
}
```

---

## Edge Cases to Handle

### 1. Multiple Chords Per Word
**Example:** Long sustained note with chord changes
```
"Loooooove"
 C    Dm  Em
```
**Solution:** Stack chords or show with timing markers

### 2. Rapid Chord Changes
**Example:** Jazz progression with chord per beat
```
"I love you"
 Cmaj7 Dm7 G7 Cmaj7
```
**Solution:** Ensure minimum spacing, may need to abbreviate

### 3. Instrumental Sections
**Example:** Guitar solo with no lyrics
```
[Guitar Solo]
Measure 17: Am7 | Dm7 | G7 | Cmaj7 |
Measure 21: Fmaj7 | Bm7b5 | E7 | Am7 |
```
**Solution:** Show chord progression with measure numbers

### 4. Syncopated Lyrics
**Example:** Lyrics that don't align with downbeats
```
Measure 1:    2:
"...and I    love you"
    Dm7      G7
```
**Solution:** Position chords at actual timing, not forced to downbeat

### 5. Repeated Sections
**Example:** Chorus appears 3 times with same lyrics/chords
```
Chorus (3x):
Measure 9: "Never gonna give you up"
           Cmaj7        Dm7
```
**Solution:** Show once with repeat notation

---

## Non-Functional Requirements

### Performance
- Alignment algorithm completes in < 1 second for typical song
- No blocking operations on main thread
- Efficient data structures for large songs (500+ words)

### Accuracy
- Chord-to-word alignment accurate within 0.1 seconds
- 95%+ of chords positioned at correct word
- Section boundaries detected with 90%+ accuracy

### Usability
- Lead sheet is readable and follows standard conventions
- Chord symbols are clearly visible and not overlapping
- Section labels are intuitive and helpful
- Output works well for both screen display and PDF printing

---

## Success Metrics

1. **Alignment Accuracy**: 95% of chords positioned at correct word (manual verification on 20 test songs)
2. **Readability**: Musicians can sight-read the lead sheet without confusion
3. **Standard Compliance**: Follows standard lead sheet notation conventions
4. **Performance**: Alignment completes in < 1 second per song
5. **User Satisfaction**: Positive feedback from beta testers

---

## Dependencies

- ✅ Lyrics extraction with word-level timestamps (Phase 1 - Complete)
- ✅ Chord detection with measure alignment (Complete)
- ✅ Song structure detection (Complete)
- ⚠️ Downbeat detection and user confirmation (In Progress)

---

## Out of Scope (Future Phases)

- Manual editing of chord positions
- Custom section labeling by user
- Transposition to different keys
- Multiple vocal parts / harmonies
- Guitar tablature generation
- MIDI playback

---

## Questions for Clarification

1. Should we show Nashville Number System alongside absolute chord names?
2. How should we handle songs with multiple languages?
3. Should instrumental sections show full chord grids or just symbols?
4. Do we need to support custom section names (e.g., "Pre-Chorus", "Post-Chorus")?
5. Should we detect and mark key changes within a song?

---

## Next Steps

Once requirements are approved:
1. Create design document with detailed algorithm specifications
2. Define data transformation pipeline
3. Create task breakdown for implementation
4. Identify test cases and validation criteria
