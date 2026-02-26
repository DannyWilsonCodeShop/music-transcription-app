# Updated MVP Vision - Professional Chord & Lyrics Sheet Generator

**Last Updated**: 2026-02-11  
**Status**: Vision Alignment Document

---

## Core MVP Goal

**Transform uploaded audio files into publication-quality chord and lyrics sheets that musicians can actually use for live performances.**

---

## Complete Processing Pipeline

### Phase 1: Tempo & Beat Foundation
```
1. Detect tempo (BPM)
2. Detect beats (full beat grid)
3. Align chroma frames to beats or subdivisions
4. Average chroma within each beat or 16th note window
```

**Purpose**: Establish precise timing grid for all subsequent analysis

---

### Phase 2: Clean Audio Analysis
```
5. Separate stems using Demucs or similar
   - Remove drums (percussion pollutes harmonic analysis)
   - Remove vocals (lyrics handled separately)
   - Keep: bass, guitar, piano, strings, synths
6. Run chord detection on harmonic content only
```

**Purpose**: Isolate harmonic content for accurate chord detection

---

### Phase 3: High-Precision Chord Detection

**Base Configuration**:
- CQT chroma (Constant-Q Transform)
- 4096 window size
- 20ms hop length (10ms for ultra-fast changes like gospel/jazz)
- Beat detection
- Average chroma per 16th note

**Processing**:
- Template matching or Hidden Markov Model (HMM)
- Enforce minimum chord duration: 1/8 note
- Handles syncopated changes cleanly (8th/16th note positions)
- No noise from passing tones

**Purpose**: Detect ALL chord changes with 16th-note precision, handling highly syncopated music

---

### Phase 4: User Validation & Correction (NEW!)

**Interactive Workflow**:
1. **Key Confirmation**
   - System: "I think the key is C major, is that correct?"
   - User: Confirms or corrects
   
2. **Song Start Point**
   - System: "Does the main portion start here?" (skip intro)
   - User: Confirms or adjusts timestamp
   
3. **Chord Review** (optional)
   - User can review and correct detected chords
   - Especially important for low-confidence sections

**Philosophy**: "Ask the user rather than produce low-confidence output"

**Purpose**: Ensure accuracy through human-in-the-loop validation

---

### Phase 5: Lyrics Extraction

**Implementation**:
- Use Whisper (OpenAI) or similar speech-to-text
- Extract from vocal stem (separated in Phase 2)
- Timestamp each lyric line
- Align lyrics with chord changes

**Purpose**: Complete the chord + lyrics sheet

---

### Phase 6: Professional PDF Creation

**Layout Requirements**:
- **Song Metadata**: Title, artist, key, tempo, time signature
- **Section Labels**: Verse, Chorus, Bridge, Intro, Outro, etc.
- **Lyrics**: Aligned with timing
- **Chords**: Nashville Number System (NNS) by measure
- **Format**: Clean, readable, performance-ready

**Display Options**:
1. **In-App View**: Scrollable, follow-along with audio
2. **Playlist View**: Multiple songs in sequence
3. **PDF Download**: Print-ready for live performance

**Key Feature**: "Follow the song along the sheet without missing anything"

**Purpose**: Professional output suitable for live performance use

---

## Current State Assessment

### What's Working ✅
- Basic infrastructure (upload, ECS, DynamoDB)
- File processing pipeline
- Frontend displays results

### What Needs Complete Rewrite ❌
1. **Chord Detection Algorithm**
   - Current: Downbeat-only sampling (misses syncopation)
   - Needed: Beat-aligned 16th-note resolution
   
2. **Key Detection**
   - Current: Frequency-based (too simplistic)
   - Needed: ML-based (Essentia) + user validation
   
3. **Audio Processing**
   - Current: Full mix with HPSS drum removal
   - Needed: Full stem separation (remove drums AND vocals)

### What's Missing Entirely ❌
1. **Lyrics Extraction** - Not implemented
2. **User Validation Flow** - Not implemented
3. **Professional PDF Generation** - Not implemented
4. **Section Identification** - Basic pattern detection exists, needs refinement
5. **In-App Scrollable View** - Not implemented

---

## Technical Specifications

### Chord Detection Parameters

```python
# Base Configuration
WINDOW_SIZE = 4096
HOP_LENGTH_MS = 20  # or 10ms for ultra-fast changes
CHROMA_TYPE = 'cqt'  # Constant-Q Transform
MIN_CHORD_DURATION = 0.125  # 1/8 note in seconds (adjusted by tempo)
RESOLUTION = '16th_note'  # Analyze at 16th note subdivisions

# Stem Separation
REMOVE_STEMS = ['drums', 'vocals']
KEEP_STEMS = ['bass', 'other']  # other = guitar, piano, strings, synths

# Beat Alignment
ALIGN_TO = 'beats_and_subdivisions'
SUBDIVISION_LEVEL = 4  # 16th notes (4 subdivisions per beat)
```

### Processing Flow

```python
def process_audio(audio_path):
    # Phase 1: Tempo & Beats
    tempo = detect_tempo(audio_path)
    beats = detect_beats(audio_path)
    subdivisions = generate_subdivisions(beats, level=4)  # 16th notes
    
    # Phase 2: Stem Separation
    stems = separate_stems(audio_path)
    harmonic_audio = stems['bass'] + stems['other']  # No drums, no vocals
    
    # Phase 3: Chord Detection
    chroma = compute_cqt_chroma(
        harmonic_audio,
        window_size=4096,
        hop_length_ms=20
    )
    
    # Align chroma to 16th note grid
    aligned_chroma = align_to_subdivisions(chroma, subdivisions)
    
    # Average chroma per 16th note window
    averaged_chroma = average_per_window(aligned_chroma, subdivisions)
    
    # Template matching with minimum duration constraint
    chords = detect_chords_with_hmm(
        averaged_chroma,
        min_duration=calculate_eighth_note_duration(tempo)
    )
    
    # Phase 4: User Validation
    key = detect_key(chords, chroma)
    key_confirmed = prompt_user_key_confirmation(key)
    
    start_point = detect_song_start(audio_path)
    start_confirmed = prompt_user_start_confirmation(start_point)
    
    # Phase 5: Lyrics
    vocal_stem = stems['vocals']
    lyrics = extract_lyrics_with_whisper(vocal_stem)
    lyrics_aligned = align_lyrics_to_chords(lyrics, chords)
    
    # Phase 6: PDF Generation
    sections = detect_sections(chords, lyrics_aligned)
    pdf = generate_professional_pdf(
        chords=chords,
        lyrics=lyrics_aligned,
        sections=sections,
        key=key_confirmed,
        tempo=tempo,
        metadata=song_metadata
    )
    
    return pdf
```

---

## Success Criteria

### Chord Detection
- ✅ Detects ALL chord changes (not just downbeats)
- ✅ Handles syncopated changes (8th/16th note positions)
- ✅ Minimum 1/8 note duration enforcement
- ✅ Clean signal (no drum/vocal interference)

### Key Detection
- ✅ ML-based initial detection
- ✅ User confirmation/correction
- ✅ High confidence before proceeding

### Lyrics
- ✅ Accurate transcription
- ✅ Aligned with chord changes
- ✅ Timestamped for follow-along

### PDF Output
- ✅ Professional layout
- ✅ Section labels (Verse, Chorus, etc.)
- ✅ Nashville numbers by measure
- ✅ Lyrics aligned with chords
- ✅ Readable for live performance
- ✅ Downloadable and printable

### User Experience
- ✅ Interactive validation (not batch processing)
- ✅ In-app scrollable view
- ✅ Follow-along with audio
- ✅ Playlist support
- ✅ "Never miss anything" - complete coverage

---

## Implementation Priority

### Phase 1: Foundation (Weeks 1-2)
1. Rewrite chord detection algorithm (beat-aligned, 16th-note resolution)
2. Implement full stem separation (remove drums + vocals)
3. Add ML-based key detection (Essentia)

### Phase 2: User Validation (Week 3)
4. Add user confirmation prompts (key, start point)
5. Build interactive frontend for validation
6. Add chord correction interface

### Phase 3: Lyrics & Sections (Week 4)
7. Integrate Whisper for lyrics extraction
8. Improve section detection
9. Align lyrics with chords

### Phase 4: Professional Output (Week 5)
10. Build professional PDF generator
11. Create in-app scrollable view
12. Add playlist support
13. Implement follow-along feature

---

## Key Differences from Previous Approach

| Aspect | Old Approach | New Approach |
|--------|-------------|--------------|
| **Timing Resolution** | Downbeat-only (4 beats) | 16th-note subdivisions |
| **Audio Source** | Full mix with HPSS | Separated stems (no drums/vocals) |
| **Key Detection** | Frequency counting | ML + user validation |
| **User Interaction** | Batch processing | Interactive validation |
| **Output** | Basic chord list | Professional PDF + in-app view |
| **Lyrics** | None | Whisper extraction + alignment |
| **Philosophy** | "Process and hope" | "Ask user, ensure quality" |

---

## Next Steps

1. **Validate this vision** - Does this match your goals?
2. **Prioritize features** - What's most critical first?
3. **Start implementation** - Begin with chord detection rewrite?

This is a significant pivot from the current implementation. The good news: the infrastructure (upload, ECS, storage) is solid. The work ahead: rewrite the core analysis algorithms and add user interaction.

Ready to proceed?
