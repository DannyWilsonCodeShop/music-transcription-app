# Lyrics-Chord Alignment Design

**Feature**: Align lyrics with chords to create professional lead sheets  
**Status**: Design Phase  
**Last Updated**: 2026-02-26  

---

## Overview

This document details the technical design for aligning lyrics (with word-level timestamps from Whisper) with chords (with measure-aligned timestamps) to generate professional lead sheets. The system will position chord symbols above the exact words where chord changes occur, group lyrics into readable phrases, and label song sections.

---

## Architecture

### High-Level Flow

```
Input Data (from DynamoDB)
├── Lyrics Data (Whisper output with word timestamps)
├── Chord Data (measure-aligned chord progression)
└── Song Structure (detected sections)
         ↓
Alignment Pipeline
├── 1. Preprocess Data
├── 2. Align Chords to Words
├── 3. Group into Phrases/Lines
├── 4. Label Sections
└── 5. Format for Display
         ↓
Output: Aligned Lead Sheet Data
├── Backend: Store in DynamoDB
└── Frontend: Render in UI and PDF
```

### Component Architecture

```
Backend (Python - app.py)
├── align_lyrics_chords()          # Main alignment function
├── find_word_at_timestamp()       # Find word for chord
├── group_into_lines()             # Create phrase lines
├── detect_section_boundaries()    # Identify sections
└── format_lead_sheet()            # Create output structure

Frontend (TypeScript - App.tsx)
├── LeadSheetDisplay component     # Render aligned sheet
├── ChordSymbol component          # Position chord above word
├── LyricsLine component           # Display phrase with chords
└── SectionLabel component         # Show section headers
```

---

## Data Models

### Input: Lyrics Data Structure

```python
LyricsData = {
    'text': str,              # Full lyrics as plain text
    'language': str,          # Detected language (e.g., 'en')
    'segments': [             # Phrase-level segments
        {
            'start': float,   # Segment start time (seconds)
            'end': float,     # Segment end time (seconds)
            'text': str       # Segment text
        }
    ],
    'words': [                # Word-level timestamps
        {
            'word': str,      # Individual word
            'start': float,   # Word start time (seconds)
            'end': float      # Word end time (seconds)
        }
    ],
    'confidence': float       # Overall transcription confidence (0-1)
}
```

### Input: Chord Data Structure

```python
ChordData = {
    'chords': [
        {
            'chord': str,         # Chord name (e.g., 'Cmaj7')
            'start': float,       # Chord start time (seconds)
            'end': float,         # Chord end time (seconds)
            'measure': int,       # Measure number
            'beat': float,        # Beat within measure
            'confidence': float   # Detection confidence (0-1)
        }
    ],
    'key': str,                   # Detected key (e.g., 'C major')
    'tempo': float,               # BPM
    'timeSignature': str,         # e.g., '4/4'
    'songStructure': [            # Detected sections
        {
            'label': str,         # Section name (e.g., 'Verse')
            'start': float,       # Section start time
            'end': float,         # Section end time
            'measureStart': int,  # First measure
            'measureEnd': int     # Last measure
        }
    ]
}
```

### Output: Aligned Lead Sheet Structure


```python
AlignedLeadSheet = {
    'metadata': {
        'key': str,
        'tempo': float,
        'timeSignature': str,
        'duration': float
    },
    'sections': [
        {
            'label': str,              # 'Verse 1', 'Chorus', etc.
            'measureStart': int,
            'measureEnd': int,
            'lines': [                 # Grouped lyric lines
                {
                    'measureStart': int,
                    'measureEnd': int,
                    'lyrics': str,     # Full line text
                    'words': [         # Individual words with positions
                        {
                            'word': str,
                            'start': float,
                            'end': float,
                            'charPosition': int  # Position in lyrics string
                        }
                    ],
                    'chords': [        # Chords for this line
                        {
                            'chord': str,
                            'timestamp': float,
                            'wordIndex': int,      # Which word (0-based)
                            'charPosition': int,   # Character position in lyrics
                            'measure': int,
                            'beat': float
                        }
                    ],
                    'isInstrumental': bool  # True if no lyrics
                }
            ]
        }
    ]
}
```

---

## Core Algorithms

### Algorithm 1: Chord-to-Word Alignment

**Purpose**: Find which word is being sung when each chord change occurs

**Input**: 
- `chords`: List of chord objects with timestamps
- `words`: List of word objects with timestamps

**Output**: List of chords with associated word indices

**Algorithm**:


```python
def align_chords_to_words(chords, words):
    """
    Align each chord change to the word being sung at that moment
    
    Strategy:
    1. For each chord, find the word that overlaps with chord start time
    2. If chord starts within 0.2s before word, snap to word start
    3. If chord is mid-word, associate with that word
    4. If no word found (instrumental), mark as instrumental
    """
    aligned_chords = []
    
    for chord in chords:
        chord_time = chord['start']
        
        # Find word at this timestamp
        word_index = find_word_at_timestamp(words, chord_time)
        
        if word_index is not None:
            word = words[word_index]
            
            # Check if chord is close to word start (within 0.2s before)
            time_before_word = word['start'] - chord_time
            if 0 <= time_before_word <= 0.2:
                # Snap to word start for cleaner alignment
                position_type = 'word_start'
            elif word['start'] <= chord_time <= word['end']:
                # Chord change during word
                position_type = 'mid_word'
            else:
                position_type = 'between_words'
            
            aligned_chords.append({
                **chord,
                'wordIndex': word_index,
                'word': word['word'],
                'positionType': position_type
            })
        else:
            # No word found - instrumental section
            aligned_chords.append({
                **chord,
                'wordIndex': None,
                'word': None,
                'positionType': 'instrumental'
            })
    
    return aligned_chords

def find_word_at_timestamp(words, timestamp, tolerance=0.1):
    """
    Find the word being sung at a given timestamp
    
    Returns word index or None if no word found
    """
    for i, word in enumerate(words):
        # Check if timestamp falls within word duration
        if word['start'] - tolerance <= timestamp <= word['end'] + tolerance:
            return i
    
    # Check if timestamp is just before a word (anticipation)
    for i, word in enumerate(words):
        if word['start'] - 0.2 <= timestamp < word['start']:
            return i
    
    return None  # Instrumental section
```

**Edge Cases**:
- Multiple chords per word: Keep all, position sequentially
- Rapid chord changes: Ensure minimum spacing (handled in formatting)
- Instrumental sections: Group chords by measure
- Syncopated timing: Use actual timestamps, don't force to beat

---

### Algorithm 2: Phrase/Line Grouping

**Purpose**: Group words and chords into readable lines (typically 2-4 measures)

**Input**:
- `aligned_chords`: Chords with word associations
- `words`: All words with timestamps
- `segments`: Whisper's phrase-level segments
- `measures_per_line`: Target measures per line (default: 2-4)

**Output**: List of line objects with lyrics and chords

**Algorithm**:


```python
def group_into_lines(aligned_chords, words, segments, tempo, time_signature):
    """
    Group words and chords into readable lines
    
    Strategy:
    1. Use Whisper segments as initial phrase boundaries
    2. Ensure each line is 2-4 measures (adjustable)
    3. Break at natural boundaries (punctuation, silence)
    4. Keep lines roughly equal length for readability
    """
    lines = []
    beats_per_measure = int(time_signature.split('/')[0])
    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * beats_per_measure
    
    # Target: 2-4 measures per line
    target_line_duration = measure_duration * 3  # 3 measures average
    min_line_duration = measure_duration * 2
    max_line_duration = measure_duration * 4
    
    current_line = {
        'words': [],
        'chords': [],
        'start': None,
        'end': None
    }
    
    for segment in segments:
        segment_words = get_words_in_segment(words, segment['start'], segment['end'])
        segment_chords = get_chords_in_segment(aligned_chords, segment['start'], segment['end'])
        
        # Check if adding this segment would exceed max line duration
        if current_line['start'] is not None:
            potential_duration = segment['end'] - current_line['start']
            
            if potential_duration > max_line_duration:
                # Finish current line and start new one
                lines.append(finalize_line(current_line))
                current_line = {
                    'words': segment_words,
                    'chords': segment_chords,
                    'start': segment['start'],
                    'end': segment['end']
                }
            else:
                # Add to current line
                current_line['words'].extend(segment_words)
                current_line['chords'].extend(segment_chords)
                current_line['end'] = segment['end']
        else:
            # First segment
            current_line = {
                'words': segment_words,
                'chords': segment_chords,
                'start': segment['start'],
                'end': segment['end']
            }
        
        # Check if current line meets minimum duration
        if current_line['start'] is not None:
            duration = current_line['end'] - current_line['start']
            
            # If line is long enough and segment ends with punctuation, break
            if duration >= min_line_duration and ends_with_punctuation(segment['text']):
                lines.append(finalize_line(current_line))
                current_line = {'words': [], 'chords': [], 'start': None, 'end': None}
    
    # Add final line
    if current_line['words']:
        lines.append(finalize_line(current_line))
    
    return lines

def finalize_line(line_data):
    """Convert line data to final format with measure numbers"""
    # Calculate measure numbers
    measure_start = calculate_measure_number(line_data['start'])
    measure_end = calculate_measure_number(line_data['end'])
    
    # Build lyrics string
    lyrics_text = ' '.join(word['word'] for word in line_data['words'])
    
    # Calculate character positions for each word
    char_pos = 0
    for word in line_data['words']:
        word['charPosition'] = char_pos
        char_pos += len(word['word']) + 1  # +1 for space
    
    # Map chords to character positions
    for chord in line_data['chords']:
        if chord['wordIndex'] is not None:
            word = line_data['words'][chord['wordIndex']]
            chord['charPosition'] = word['charPosition']
        else:
            chord['charPosition'] = 0  # Instrumental
    
    return {
        'measureStart': measure_start,
        'measureEnd': measure_end,
        'lyrics': lyrics_text,
        'words': line_data['words'],
        'chords': line_data['chords'],
        'isInstrumental': len(line_data['words']) == 0
    }
```

---

### Algorithm 3: Section Detection and Labeling

**Purpose**: Identify and label song sections (Verse, Chorus, Bridge, etc.)

**Input**:
- `song_structure`: Detected sections from chord analysis
- `lines`: Grouped lyric lines
- `chords`: Chord progression

**Output**: Sections with labels and line groupings

**Algorithm**:


```python
def detect_and_label_sections(song_structure, lines, chords):
    """
    Identify song sections and assign appropriate labels
    
    Strategy:
    1. Use existing song_structure from chord detection
    2. Correlate with lyric line boundaries
    3. Detect repeated sections (same chords + similar lyrics)
    4. Assign standard labels (Verse 1, Chorus, Bridge, etc.)
    5. Handle instrumental sections (Intro, Solo, Outro)
    """
    sections = []
    verse_count = 0
    chorus_count = 0
    bridge_count = 0
    
    # Track repeated sections for numbering
    section_fingerprints = {}  # chord pattern -> section type
    
    for struct_section in song_structure:
        # Get lines that fall within this section
        section_lines = get_lines_in_range(
            lines, 
            struct_section['start'], 
            struct_section['end']
        )
        
        # Get chord progression for this section
        section_chords = get_chords_in_range(
            chords,
            struct_section['start'],
            struct_section['end']
        )
        
        # Create fingerprint (chord progression pattern)
        fingerprint = create_chord_fingerprint(section_chords)
        
        # Determine section type
        has_lyrics = any(not line['isInstrumental'] for line in section_lines)
        
        if not has_lyrics:
            # Instrumental section
            if struct_section['start'] < 5.0:
                label = 'Intro'
            elif struct_section['end'] > get_song_duration() - 10.0:
                label = 'Outro'
            else:
                label = 'Instrumental'
        else:
            # Section with lyrics - use existing label or detect
            base_label = struct_section.get('label', 'Section')
            
            # Check if this is a repeated section
            if fingerprint in section_fingerprints:
                # Repeated section - increment counter
                section_type = section_fingerprints[fingerprint]
                if section_type == 'Verse':
                    verse_count += 1
                    label = f'Verse {verse_count}'
                elif section_type == 'Chorus':
                    chorus_count += 1
                    label = 'Chorus' if chorus_count == 1 else f'Chorus {chorus_count}'
                else:
                    label = section_type
            else:
                # New section - classify
                if base_label == 'Verse' or is_verse_like(section_chords, section_lines):
                    verse_count += 1
                    label = f'Verse {verse_count}'
                    section_fingerprints[fingerprint] = 'Verse'
                elif base_label == 'Chorus' or is_chorus_like(section_chords, section_lines):
                    chorus_count += 1
                    label = 'Chorus'
                    section_fingerprints[fingerprint] = 'Chorus'
                elif base_label == 'Bridge' or is_bridge_like(section_chords, section_lines):
                    bridge_count += 1
                    label = 'Bridge'
                    section_fingerprints[fingerprint] = 'Bridge'
                else:
                    label = base_label
        
        sections.append({
            'label': label,
            'measureStart': struct_section['measureStart'],
            'measureEnd': struct_section['measureEnd'],
            'lines': section_lines
        })
    
    return sections

def create_chord_fingerprint(chords):
    """Create a pattern signature for chord progression"""
    # Use chord roots and qualities, ignoring exact timing
    return tuple((c['chord'], c['measure'] % 4) for c in chords)

def is_verse_like(chords, lines):
    """Heuristic: verses typically have more lyrics, simpler chords"""
    avg_words_per_line = sum(len(l['words']) for l in lines) / max(len(lines), 1)
    return avg_words_per_line > 8  # Verses tend to be wordy

def is_chorus_like(chords, lines):
    """Heuristic: choruses have repetitive lyrics, stronger progressions"""
    # Check for repeated phrases
    texts = [l['lyrics'] for l in lines]
    has_repetition = len(texts) != len(set(texts))
    return has_repetition

def is_bridge_like(chords, lines):
    """Heuristic: bridges have different chord progressions"""
    # This would compare against verse/chorus patterns
    # Simplified: assume bridge if not verse or chorus
    return False
```

---

## Implementation Details

### Backend Implementation (Python)

**File**: `backend/functions-v2/chord-detector-ecs/app.py`

**New Function**: `align_lyrics_with_chords()`


```python
def align_lyrics_with_chords(chords_data, lyrics_data):
    """
    Main function to align lyrics with chords
    
    Args:
        chords_data: Dict with chords, key, tempo, timeSignature, songStructure
        lyrics_data: Dict with text, segments, words, confidence
    
    Returns:
        AlignedLeadSheet structure
    """
    log("Starting lyrics-chord alignment...")
    
    # Step 1: Align chords to words
    aligned_chords = align_chords_to_words(
        chords_data['chords'],
        lyrics_data['words']
    )
    log(f"  Aligned {len(aligned_chords)} chords to words")
    
    # Step 2: Group into lines
    lines = group_into_lines(
        aligned_chords,
        lyrics_data['words'],
        lyrics_data['segments'],
        chords_data['tempo'],
        chords_data['timeSignature']
    )
    log(f"  Grouped into {len(lines)} lines")
    
    # Step 3: Detect and label sections
    sections = detect_and_label_sections(
        chords_data['songStructure'],
        lines,
        chords_data['chords']
    )
    log(f"  Identified {len(sections)} sections")
    
    # Step 4: Create final structure
    lead_sheet = {
        'metadata': {
            'key': chords_data['key'],
            'tempo': chords_data['tempo'],
            'timeSignature': chords_data['timeSignature'],
            'duration': chords_data['duration']
        },
        'sections': sections
    }
    
    log("✓ Lyrics-chord alignment complete")
    return lead_sheet
```

**Integration Point**: Call after chord detection completes

```python
def detect_chords(audio_path, job_id, confirmed_downbeat=None, confirmed_time_signature=None):
    # ... existing chord detection code ...
    
    # After chord detection, check if lyrics exist
    job_data = get_job_from_dynamodb(job_id)
    
    if job_data.get('lyricsData'):
        log("Lyrics found, performing alignment...")
        lead_sheet = align_lyrics_with_chords(chords_data, job_data['lyricsData'])
        chords_data['leadSheet'] = lead_sheet
    else:
        log("No lyrics found, skipping alignment")
    
    return chords_data
```

---

### Frontend Implementation (TypeScript/React)

**File**: `src/App.tsx`

**New Component**: `LeadSheetDisplay`


```typescript
interface LeadSheetProps {
  leadSheet: AlignedLeadSheet;
  showMeasureNumbers?: boolean;
  showTimestamps?: boolean;  // Debug mode
}

function LeadSheetDisplay({ leadSheet, showMeasureNumbers = true, showTimestamps = false }: LeadSheetProps) {
  return (
    <div className="lead-sheet">
      {/* Metadata header */}
      <div className="lead-sheet-header">
        <div>Key: {leadSheet.metadata.key}</div>
        <div>Tempo: {leadSheet.metadata.tempo} BPM</div>
        <div>Time: {leadSheet.metadata.timeSignature}</div>
      </div>
      
      {/* Sections */}
      {leadSheet.sections.map((section, sectionIdx) => (
        <div key={sectionIdx} className="lead-sheet-section">
          {/* Section label */}
          <h3 className="section-label">{section.label}</h3>
          
          {/* Lines within section */}
          {section.lines.map((line, lineIdx) => (
            <LyricsLine
              key={lineIdx}
              line={line}
              showMeasureNumbers={showMeasureNumbers}
              showTimestamps={showTimestamps}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

interface LyricsLineProps {
  line: AlignedLine;
  showMeasureNumbers: boolean;
  showTimestamps: boolean;
}

function LyricsLine({ line, showMeasureNumbers, showTimestamps }: LyricsLineProps) {
  // Build chord positioning map
  const chordPositions = line.chords.map(chord => ({
    chord: chord.chord,
    position: chord.charPosition,
    timestamp: chord.timestamp
  }));
  
  return (
    <div className="lyrics-line">
      {/* Measure numbers */}
      {showMeasureNumbers && (
        <div className="measure-numbers">
          {line.measureStart === line.measureEnd 
            ? `M${line.measureStart}`
            : `M${line.measureStart}-${line.measureEnd}`
          }
        </div>
      )}
      
      {/* Chord symbols positioned above lyrics */}
      <div className="chord-line">
        {chordPositions.map((cp, idx) => (
          <span
            key={idx}
            className="chord-symbol"
            style={{ 
              position: 'absolute',
              left: `${cp.position * 0.6}ch`  // Approximate character width
            }}
          >
            {cp.chord}
            {showTimestamps && <span className="timestamp">({cp.timestamp.toFixed(2)}s)</span>}
          </span>
        ))}
      </div>
      
      {/* Lyrics text */}
      <div className="lyrics-text">
        {line.isInstrumental ? (
          <span className="instrumental-marker">[Instrumental]</span>
        ) : (
          line.lyrics
        )}
      </div>
    </div>
  );
}
```

**CSS Styling**:

```css
.lead-sheet {
  font-family: 'Courier New', monospace;
  padding: 20px;
  background: white;
  color: black;
}

.lead-sheet-section {
  margin-bottom: 30px;
}

.section-label {
  font-weight: bold;
  font-size: 18px;
  margin-bottom: 10px;
  border-bottom: 2px solid #333;
}

.lyrics-line {
  position: relative;
  margin-bottom: 20px;
  padding-left: 60px;  /* Space for measure numbers */
}

.measure-numbers {
  position: absolute;
  left: 0;
  top: 20px;
  font-size: 12px;
  color: #666;
  width: 50px;
}

.chord-line {
  position: relative;
  height: 20px;
  font-weight: bold;
  color: #0066cc;
}

.chord-symbol {
  white-space: nowrap;
}

.lyrics-text {
  font-size: 14px;
  line-height: 1.6;
}

.instrumental-marker {
  font-style: italic;
  color: #999;
}

.timestamp {
  font-size: 10px;
  color: #999;
  margin-left: 4px;
}
```

---

## PDF Generation Updates

**File**: `backend/functions-v2/pdf-generator/index.js`

Update PDF generator to use aligned lead sheet data:


```javascript
function generateLeadSheetPDF(jobData) {
  const doc = new PDFDocument({ size: 'LETTER', margin: 50 });
  
  // Header with metadata
  doc.fontSize(20).text(jobData.title || 'Untitled', { align: 'center' });
  doc.moveDown();
  doc.fontSize(12).text(
    `Key: ${jobData.chordsData.key}  |  Tempo: ${jobData.chordsData.tempo} BPM  |  Time: ${jobData.chordsData.timeSignature}`,
    { align: 'center' }
  );
  doc.moveDown(2);
  
  // Render each section
  const leadSheet = jobData.chordsData.leadSheet;
  
  for (const section of leadSheet.sections) {
    // Section label
    doc.fontSize(14).font('Helvetica-Bold').text(section.label);
    doc.moveDown(0.5);
    
    // Render lines
    for (const line of section.lines) {
      renderLineWithChords(doc, line);
      doc.moveDown(1);
    }
    
    doc.moveDown(1);
  }
  
  return doc;
}

function renderLineWithChords(doc, line) {
  const startX = doc.x;
  const startY = doc.y;
  
  // Measure numbers (left margin)
  doc.fontSize(10).font('Helvetica').fillColor('#666666');
  doc.text(
    line.measureStart === line.measureEnd 
      ? `${line.measureStart}`
      : `${line.measureStart}-${line.measureEnd}`,
    startX - 40,
    startY + 10,
    { width: 35, align: 'right' }
  );
  
  // Chord symbols (above lyrics)
  doc.fillColor('#0066cc').font('Helvetica-Bold').fontSize(11);
  for (const chord of line.chords) {
    const xPos = startX + (chord.charPosition * 6);  // Approximate char width
    doc.text(chord.chord, xPos, startY);
  }
  
  // Lyrics text (below chords)
  doc.fillColor('#000000').font('Helvetica').fontSize(12);
  doc.text(
    line.isInstrumental ? '[Instrumental]' : line.lyrics,
    startX,
    startY + 15
  );
}
```

---

## Edge Case Handling

### 1. Multiple Chords Per Word

**Problem**: Long sustained note with multiple chord changes

**Example**:
```
"Loooooove"
 C  Dm  Em
```

**Solution**:


```python
def handle_multiple_chords_per_word(word, chords_for_word):
    """
    When multiple chords occur during a single word,
    space them evenly across the word length
    """
    word_length = len(word['word'])
    num_chords = len(chords_for_word)
    
    for i, chord in enumerate(chords_for_word):
        # Distribute chords across word
        offset = (word_length / num_chords) * i
        chord['charPosition'] = word['charPosition'] + int(offset)
    
    return chords_for_word
```

### 2. Rapid Chord Changes

**Problem**: Jazz/complex progressions with chord per beat

**Example**:
```
"I    love    you"
 Cmaj7 Dm7 G7 Cmaj7
```

**Solution**: Ensure minimum spacing, abbreviate if needed

```python
def ensure_chord_spacing(chords, min_spacing=3):
    """
    Ensure chords don't overlap by enforcing minimum spacing
    """
    for i in range(1, len(chords)):
        prev_chord = chords[i-1]
        curr_chord = chords[i]
        
        # Calculate space between chords
        space = curr_chord['charPosition'] - (prev_chord['charPosition'] + len(prev_chord['chord']))
        
        if space < min_spacing:
            # Abbreviate chord names if needed
            if len(prev_chord['chord']) > 4:
                prev_chord['chord'] = abbreviate_chord(prev_chord['chord'])
            if len(curr_chord['chord']) > 4:
                curr_chord['chord'] = abbreviate_chord(curr_chord['chord'])
    
    return chords

def abbreviate_chord(chord_name):
    """Shorten chord names: Cmaj7 -> CM7, Dm7b5 -> Dm7♭5"""
    chord_name = chord_name.replace('maj', 'M')
    chord_name = chord_name.replace('min', 'm')
    chord_name = chord_name.replace('dim', '°')
    chord_name = chord_name.replace('aug', '+')
    return chord_name
```

### 3. Instrumental Sections

**Problem**: No lyrics, just chord progression

**Solution**: Display chords with measure numbers in grid format

```python
def format_instrumental_section(chords, measures):
    """
    Format instrumental section as chord grid
    
    Example output:
    [Guitar Solo]
    M17: Am7  | Dm7  | G7   | Cmaj7 |
    M21: Fmaj7| Bm7♭5| E7   | Am7   |
    """
    lines = []
    chords_per_measure = 1  # Adjust based on time signature
    
    for i in range(0, len(chords), 4):  # 4 measures per line
        measure_chords = chords[i:i+4]
        measure_start = measure_chords[0]['measure']
        
        chord_str = ' | '.join(f"{c['chord']:6s}" for c in measure_chords)
        lines.append({
            'measureStart': measure_start,
            'measureEnd': measure_start + 3,
            'lyrics': f"M{measure_start}: {chord_str} |",
            'chords': [],
            'isInstrumental': True
        })
    
    return lines
```

### 4. Syncopated Lyrics

**Problem**: Lyrics don't align with downbeats

**Solution**: Use actual timestamps, don't force alignment

```python
# Already handled by using actual word timestamps
# No artificial snapping to beat grid
```

### 5. Repeated Sections

**Problem**: Same lyrics/chords appear multiple times

**Solution**: Show once with repeat notation or number each occurrence

```python
def detect_repeated_sections(sections):
    """
    Identify repeated sections and add repeat notation
    """
    section_patterns = {}
    
    for section in sections:
        # Create fingerprint
        fingerprint = (
            tuple(line['lyrics'] for line in section['lines']),
            tuple(chord['chord'] for chord in get_all_chords(section))
        )
        
        if fingerprint in section_patterns:
            # Mark as repeat
            section['isRepeat'] = True
            section['repeatOf'] = section_patterns[fingerprint]
        else:
            section_patterns[fingerprint] = section['label']
            section['isRepeat'] = False
    
    return sections
```

---

## Testing Strategy

### Unit Tests

**Test File**: `test_lyrics_alignment.py`


```python
import pytest
from lyrics_alignment import (
    align_chords_to_words,
    find_word_at_timestamp,
    group_into_lines,
    detect_and_label_sections
)

def test_find_word_at_timestamp():
    """Test finding word at specific timestamp"""
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 0.9, 'end': 1.2}
    ]
    
    # Exact match
    assert find_word_at_timestamp(words, 0.6) == 0
    assert find_word_at_timestamp(words, 1.0) == 1
    
    # Before word (anticipation)
    assert find_word_at_timestamp(words, 0.4) == 0
    
    # Between words
    assert find_word_at_timestamp(words, 0.85) is None
    
    # After all words
    assert find_word_at_timestamp(words, 2.0) is None

def test_align_chords_to_words():
    """Test chord-to-word alignment"""
    words = [
        {'word': 'I', 'start': 0.5, 'end': 0.7},
        {'word': 'love', 'start': 0.8, 'end': 1.2},
        {'word': 'you', 'start': 1.3, 'end': 1.6}
    ]
    
    chords = [
        {'chord': 'C', 'start': 0.5, 'measure': 1},
        {'chord': 'G', 'start': 1.0, 'measure': 2},
        {'chord': 'Am', 'start': 1.4, 'measure': 3}
    ]
    
    aligned = align_chords_to_words(chords, words)
    
    assert aligned[0]['wordIndex'] == 0  # C at "I"
    assert aligned[1]['wordIndex'] == 1  # G at "love"
    assert aligned[2]['wordIndex'] == 2  # Am at "you"

def test_group_into_lines():
    """Test phrase grouping"""
    # Mock data
    words = create_mock_words(20)  # 20 words
    chords = create_mock_chords(8)  # 8 chords
    segments = create_mock_segments(4)  # 4 phrases
    
    lines = group_into_lines(words, chords, segments, tempo=120, time_signature='4/4')
    
    # Should create 2-4 lines
    assert 2 <= len(lines) <= 4
    
    # Each line should have words and chords
    for line in lines:
        assert len(line['words']) > 0
        assert 'lyrics' in line
        assert 'measureStart' in line

def test_section_detection():
    """Test section labeling"""
    # Mock song structure
    song_structure = [
        {'label': 'Verse', 'start': 0, 'end': 16, 'measureStart': 1, 'measureEnd': 8},
        {'label': 'Chorus', 'start': 16, 'end': 32, 'measureStart': 9, 'measureEnd': 16},
        {'label': 'Verse', 'start': 32, 'end': 48, 'measureStart': 17, 'measureEnd': 24}
    ]
    
    lines = create_mock_lines(12)
    chords = create_mock_chords(24)
    
    sections = detect_and_label_sections(song_structure, lines, chords)
    
    # Should have 3 sections
    assert len(sections) == 3
    
    # Verses should be numbered
    assert sections[0]['label'] == 'Verse 1'
    assert sections[2]['label'] == 'Verse 2'
    
    # Chorus should not be numbered (first occurrence)
    assert sections[1]['label'] == 'Chorus'

def test_multiple_chords_per_word():
    """Test handling multiple chords during one word"""
    word = {'word': 'Loooove', 'start': 1.0, 'end': 3.0, 'charPosition': 0}
    chords = [
        {'chord': 'C', 'start': 1.0},
        {'chord': 'Dm', 'start': 1.5},
        {'chord': 'Em', 'start': 2.0}
    ]
    
    result = handle_multiple_chords_per_word(word, chords)
    
    # Chords should be spaced across word
    assert result[0]['charPosition'] == 0
    assert result[1]['charPosition'] > 0
    assert result[2]['charPosition'] > result[1]['charPosition']

def test_instrumental_section():
    """Test instrumental section formatting"""
    chords = [
        {'chord': 'Am7', 'measure': 17},
        {'chord': 'Dm7', 'measure': 18},
        {'chord': 'G7', 'measure': 19},
        {'chord': 'Cmaj7', 'measure': 20}
    ]
    
    lines = format_instrumental_section(chords, measures=[17, 18, 19, 20])
    
    assert len(lines) == 1
    assert lines[0]['isInstrumental'] == True
    assert 'M17:' in lines[0]['lyrics']
```

### Integration Tests

Test with real song data:

```python
def test_full_alignment_pipeline():
    """Test complete alignment with real data"""
    # Load test data
    chords_data = load_test_chords('test_song.json')
    lyrics_data = load_test_lyrics('test_song_lyrics.json')
    
    # Run alignment
    lead_sheet = align_lyrics_with_chords(chords_data, lyrics_data)
    
    # Verify structure
    assert 'metadata' in lead_sheet
    assert 'sections' in lead_sheet
    assert len(lead_sheet['sections']) > 0
    
    # Verify each section has lines
    for section in lead_sheet['sections']:
        assert 'label' in section
        assert 'lines' in section
        assert len(section['lines']) > 0
        
        # Verify each line has chords and lyrics
        for line in section['lines']:
            if not line['isInstrumental']:
                assert len(line['lyrics']) > 0
            assert 'chords' in line
```

---

## Performance Considerations

### Time Complexity

- `find_word_at_timestamp()`: O(n) where n = number of words
- `align_chords_to_words()`: O(m * n) where m = chords, n = words
- `group_into_lines()`: O(n) where n = number of segments
- `detect_and_label_sections()`: O(s * l) where s = sections, l = lines

**Overall**: O(m * n) dominated by chord-word alignment

**Optimization**: Use binary search for word lookup → O(m * log n)

### Space Complexity

- Input data: O(m + n) for chords and words
- Output data: O(m + n) for aligned structure
- Temporary structures: O(n) for line grouping

**Total**: O(m + n) - linear in input size

### Expected Performance

For typical song (3-4 minutes):
- ~200 words
- ~100 chords
- ~20 lines
- ~5 sections

**Estimated time**: < 100ms for alignment

---

## Error Handling

### Missing Data

```python
def align_lyrics_with_chords(chords_data, lyrics_data):
    # Validate inputs
    if not lyrics_data or not lyrics_data.get('words'):
        log("No lyrics data available", "WARNING")
        return None
    
    if not chords_data or not chords_data.get('chords'):
        log("No chord data available", "ERROR")
        raise ValueError("Chord data required for alignment")
    
    # Continue with alignment...
```

### Timestamp Mismatches

```python
def find_word_at_timestamp(words, timestamp, tolerance=0.1):
    # Increase tolerance if no match found
    if result is None and tolerance < 0.5:
        return find_word_at_timestamp(words, timestamp, tolerance * 2)
    return result
```

### Empty Sections

```python
def detect_and_label_sections(song_structure, lines, chords):
    sections = []
    
    for struct_section in song_structure:
        section_lines = get_lines_in_range(...)
        
        if not section_lines:
            log(f"No lines found for section {struct_section['label']}", "WARNING")
            # Create placeholder instrumental section
            section_lines = create_instrumental_placeholder(struct_section)
        
        sections.append({...})
    
    return sections
```

---

## Deployment Plan

### Phase 1: Backend Implementation (Day 1)
1. Implement core alignment algorithms in `app.py`
2. Add unit tests
3. Test with sample data locally

### Phase 2: Integration (Day 2)
1. Integrate with chord detection pipeline
2. Update DynamoDB schema to store `leadSheet` data
3. Test end-to-end with real songs

### Phase 3: Frontend Display (Day 2-3)
1. Create `LeadSheetDisplay` component
2. Add CSS styling
3. Test rendering with various songs

### Phase 4: PDF Generation (Day 3)
1. Update PDF generator to use aligned data
2. Test PDF output quality
3. Handle edge cases (long lines, many chords)

### Phase 5: Testing & Refinement (Day 3)
1. Test with diverse song types (pop, jazz, rock)
2. Refine alignment heuristics
3. Fix edge cases
4. Performance optimization

---

## Success Criteria

✅ **Functional Requirements**:
- Chords positioned above correct words (95% accuracy)
- Lines grouped into readable phrases (2-4 measures)
- Sections properly labeled and numbered
- Instrumental sections handled gracefully
- PDF output matches frontend display

✅ **Performance Requirements**:
- Alignment completes in < 1 second
- No blocking on main thread
- Handles songs up to 10 minutes

✅ **Quality Requirements**:
- Follows standard lead sheet conventions
- Readable and professional appearance
- Works across different genres and styles

---

## Future Enhancements

### Phase 3 (Future):
- Manual chord position editing
- Custom section labeling
- Nashville Number System display
- Transposition to different keys
- Multiple vocal parts support
- Export to MusicXML format

---

## References

- [Lead Sheet Notation Standards](https://en.wikipedia.org/wiki/Lead_sheet)
- [Whisper Word Timestamps](https://github.com/openai/whisper)
- [Music Notation Best Practices](https://www.musicnotation.org/)
