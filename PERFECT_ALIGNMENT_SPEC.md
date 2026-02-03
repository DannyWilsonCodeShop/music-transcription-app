# Perfect Nashville Number System Alignment Specification

## Overview
This specification defines the AI-powered system for generating perfectly aligned Nashville Number System (NNS) chord charts with syllable-separated lyrics, based on the Amazing Grace template.

## Core Principles

### 1. Four-Column Alignment System
- **Default**: 4 measures per line (adjustable based on time signature)
- **Column Positions**: 
  - Column 1: x=38px (First downbeat)
  - Column 2: x=73px (Second downbeat) 
  - Column 3: x=108px (Third downbeat)
  - Column 4: x=143px (Fourth downbeat)
- **Spacing**: 35px between columns (optimal readability)

### 2. Syllable Separation Rules
- **Hyphenated syllables**: "A-maz-ing" not "Amazing"
- **3-space separation**: Between syllables within words
- **Word spacing**: Varies to maintain column alignment
- **Pickup notes**: Positioned 9px left of their target downbeat

### 3. Color Coding System
- **RED (200,0,0)**: Downbeat chord numbers (strong beats)
- **BLACK (0,0,0)**: Passing chord numbers (weak beats)
- **Font**: Helvetica Bold, 11pt for chord numbers
- **Font**: Helvetica Normal, 11pt for lyrics

## AI Analysis Requirements

### 1. Tempo Detection
```javascript
// AI must analyze audio to determine:
{
  tempo: 120,           // BPM
  timeSignature: "3/4", // Time signature
  confidence: 0.95      // Analysis confidence
}
```

### 2. Measure Boundary Detection
```javascript
// AI identifies measure boundaries in lyrics:
{
  measures: [
    {
      startTime: 0.0,
      endTime: 2.0,
      syllables: ["A-", "maz-", "ing", "Grace"],
      downbeats: [1, 2, 3, 4], // Beat positions
      pickup: "A-"              // Optional pickup note
    }
  ]
}
```

### 3. Downbeat Identification
```javascript
// AI determines which syllables fall on strong beats:
{
  downbeats: [
    { syllable: "maz-", beat: 1, measure: 1, isStrong: true },
    { syllable: "Grace", beat: 1, measure: 2, isStrong: true },
    { syllable: "sweet", beat: 1, measure: 3, isStrong: true },
    { syllable: "sound", beat: 1, measure: 4, isStrong: true }
  ]
}
```

### 4. Syllable Analysis
```javascript
// AI separates words into musical syllables:
{
  "Amazing": ["A-", "maz-", "ing"],
  "Grace": ["Grace"],
  "beautiful": ["beau-", "ti-", "ful"],
  "wonderful": ["won-", "der-", "ful"]
}
```

## Layout Algorithm

### 1. Line Processing
```javascript
function processLine(lyrics, chords, timeSignature) {
  // 1. Analyze syllable boundaries
  const syllables = separateIntoSyllables(lyrics);
  
  // 2. Identify downbeats and pickups
  const beats = identifyBeatsAndPickups(syllables, timeSignature);
  
  // 3. Map chords to syllables
  const chordMapping = mapChordsToSyllables(syllables, chords);
  
  // 4. Group into measures (default 4 per line)
  const measures = groupIntoMeasures(beats, chordMapping, 4);
  
  return measures;
}
```

### 2. Perfect Alignment Rules
```javascript
// Column alignment system:
const ALIGNMENT_RULES = {
  pickupOffset: -9,        // Pickup notes 9px left of downbeat
  syllableSpacing: 12,     // 3 spaces between syllables
  wordSpacing: 15,         // Variable word spacing for alignment
  columnSpacing: 35,       // 35px between downbeat columns
  lineSpacing: 15,         // 15px between lyric/chord pairs
  sectionSpacing: 25       // 25px between song sections
};
```

### 3. Chord Positioning
```javascript
// Chord number positioning:
function positionChords(syllables, chords, columns) {
  const positions = [];
  
  // RED downbeat chords
  for (let i = 0; i < 4; i++) {
    if (chords.downbeats[i]) {
      positions.push({
        chord: chords.downbeats[i],
        x: columns[i],
        color: "RED",
        isDownbeat: true
      });
    }
  }
  
  // BLACK passing chords
  for (const passing of chords.passing) {
    positions.push({
      chord: passing.number,
      x: calculatePassingPosition(passing.syllable),
      color: "BLACK",
      isDownbeat: false
    });
  }
  
  return positions;
}
```

## Example Output Structure

### Amazing Grace Template
```
Amazing Grace

Key: G | Tempo: 120 BPM | Meter: 3/4

Verse 1
    A-   maz- ing    Grace,how    sweet the    sound
         1           1           5            1

That     saved a    wretch like  me
         5    2     6     3      4    1

I        once  was  lost, but    now  am      found
         1          1    5       4            1

Was      blind, but now  I       see
         1    6     5            1
```

## Implementation Checklist

### Phase 1: Core Alignment
- [x] Four-column tab system (38, 73, 108, 143px)
- [x] Syllable separation with hyphens
- [x] Pickup note positioning (-9px offset)
- [x] RED/BLACK color coding for chords
- [x] Perfect vertical alignment

### Phase 2: AI Analysis
- [ ] Tempo detection from audio
- [ ] Time signature identification
- [ ] Measure boundary detection
- [ ] Downbeat identification algorithm
- [ ] Advanced syllable separation
- [ ] Chord-to-syllable mapping

### Phase 3: Adaptive Layout
- [ ] Variable measures per line (2-6 based on complexity)
- [ ] Different time signatures (3/4, 4/4, 6/8, etc.)
- [ ] Complex pickup patterns
- [ ] Multi-syllable chord changes
- [ ] Bridge and instrumental sections

### Phase 4: Quality Assurance
- [ ] Alignment validation
- [ ] Readability scoring
- [ ] Professional musician review
- [ ] A/B testing with existing charts

## Success Metrics

### Alignment Quality
- **Perfect vertical alignment**: All downbeats in clean columns
- **Consistent spacing**: 3-space syllable separation maintained
- **Readable layout**: No overlapping text or cramped spacing
- **Professional appearance**: Matches hand-written lead sheets

### Musical Accuracy
- **Correct downbeats**: Strong beats properly identified
- **Accurate pickups**: Weak beats positioned correctly
- **Proper chord timing**: Numbers align with syllable emphasis
- **Time signature compliance**: Layout matches musical meter

## Technical Requirements

### Input Processing
```javascript
// Required input format:
{
  audioFile: "song.mp3",
  lyrics: "Amazing Grace, how sweet the sound...",
  metadata: {
    title: "Amazing Grace",
    key: "G",
    artist: "Traditional"
  }
}
```

### Output Format
```javascript
// Generated PDF specifications:
{
  format: "A4",
  margins: { top: 20, bottom: 20, left: 20, right: 20 },
  fonts: {
    title: { family: "Helvetica", size: 18, weight: "bold" },
    lyrics: { family: "Helvetica", size: 11, weight: "normal" },
    chords: { family: "Helvetica", size: 11, weight: "bold" }
  },
  colors: {
    downbeats: [200, 0, 0],    // RED
    passing: [0, 0, 0],        // BLACK
    text: [0, 0, 0]            // BLACK
  }
}
```

This specification ensures every generated Nashville Number System chart matches the professional quality and perfect alignment of our Amazing Grace template.