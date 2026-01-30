# Measure-Based Nashville Number System Layout Specification

## 🎯 Overview
This document specifies the exact implementation of the measure-based Nashville Number System layout with RED downbeats and BLACK passing chords, supporting up to 8 passing chords per measure.

## 📐 Layout Specifications

### Column Positions
- **Measure 1**: 38px (one-tab indent from margin)
- **Measure 2**: 73px (35px spacing)
- **Measure 3**: 108px (35px spacing)
- **Measure 4**: 143px (35px spacing)

### Typography
- **Title**: 18pt Helvetica Bold, normal case
- **Metadata**: 12pt Helvetica Bold (Key: G | Tempo: 120 BPM | Meter: 3/4)
- **Section Labels**: 12pt Helvetica Bold (Verse 1, Chorus, etc.)
- **Lyrics**: 11pt Helvetica Normal
- **Chord Numbers**: 11pt Helvetica Bold

### Color Coding
- **RED (200, 0, 0)**: Downbeat chord numbers (strong beats)
- **BLACK (0, 0, 0)**: Passing chord numbers (weak beats)

### Spacing
- **Title Gap**: 10px after title
- **Metadata Gap**: 13px after metadata
- **Section Gap**: 8px after section labels
- **Line Gap**: 6px between lyrics and chord numbers
- **Measure Gap**: 15px between measure lines

## 🎵 Measure Structure

### Each Measure Contains:
1. **Pickup Notes** (optional)
   - Positioned LEFT of downbeat (-9px, -21px, -33px, etc.)
   - Weak beats that lead into the downbeat
   - BLACK chord numbers if they have chord changes

2. **Downbeat Syllable** (required)
   - Positioned at exact column position (38px, 73px, 108px, 143px)
   - Strong beat of the measure
   - RED chord number underneath

3. **Additional Syllables** (optional)
   - Positioned RIGHT of downbeat (+12px, +24px, +36px, etc.)
   - Continuing syllables within the measure
   - May have BLACK chord numbers for passing chords

4. **Passing Chords** (up to 8 per measure)
   - BLACK chord numbers positioned under appropriate syllables
   - Can be pickup chords, downbeat chords, or after-beat chords

## 🔧 Implementation Structure

### Measure Data Format
```javascript
const measureData = {
  measures: [
    {
      pickup: { syllable: 'A-', position: 29 }, // Optional pickup
      downbeat: { syllable: 'maz-', chordNumber: '1' }, // Required
      additional: [
        { syllable: 'ing', offset: 12 }
      ], // Optional additional syllables
      passingChords: [
        { number: '4', position: 56 }
      ] // Optional passing chords (max 8)
    },
    // ... up to 4 measures per line
  ]
};
```

### Function Structure
```javascript
function generateMeasureLine(doc, measures, tabPositions, yPos) {
  // 1. Draw syllables (pickup, downbeat, additional)
  // 2. Draw RED downbeat chord numbers
  // 3. Draw BLACK passing chord numbers
  // 4. Return updated yPos
}
```

## 🎼 Musical Rules

### Downbeat Identification
- **3/4 Time**: Beats 1 of each measure (every 3 beats)
- **4/4 Time**: Beats 1 of each measure (every 4 beats)
- **6/8 Time**: Beats 1 and 4 of each measure (every 3 beats)

### Pickup Note Handling
- Positioned to the LEFT of their target downbeat
- Multiple pickups stack leftward (-9px, -21px, -33px)
- Maintain proper syllable spacing

### Passing Chord Limits
- Maximum 8 passing chords per measure
- Positioned based on syllable alignment
- Always BLACK color coding
- Can appear before, on, or after any beat

## 📊 Example Output

```
Amazing Grace
Key: G | Tempo: 120 BPM | Meter: 3/4

Verse 1
    A-   maz- ing    Grace,how    sweet the    sound
         1           1           5     4       1

That     saved a    wretch like  me
         5    2     6     3      4    1

I        once  was  lost, but    now  am      found
         1          1    5       4            1

Was      blind, but now  I       see
         1    6     5            1
```

## 🚀 Production Features

### Automatic Analysis
- **Syllable Separation**: AI-powered syllable boundary detection
- **Downbeat Detection**: Musical phrase analysis for strong beats
- **Pickup Identification**: Anacrusis detection and positioning
- **Chord Mapping**: Intelligent chord-to-syllable alignment

### Scalability
- **Variable Measures**: 1-4 measures per line (AI-adjustable)
- **Multiple Verses**: Consistent alignment across all sections
- **Different Time Signatures**: 3/4, 4/4, 6/8, etc.
- **Complex Rhythms**: Syncopation and irregular patterns

### Quality Assurance
- **Perfect Alignment**: Vertical column consistency
- **No Overlap**: Intelligent spacing prevents text collision
- **Professional Typography**: Industry-standard formatting
- **Color Consistency**: Reliable RED/BLACK coding

## 🎯 Success Metrics

### Technical Excellence
- ✅ Perfect 4-column alignment (38px, 73px, 108px, 143px)
- ✅ RED downbeat chord numbers
- ✅ BLACK passing chord numbers (up to 8 per measure)
- ✅ Proper pickup note positioning
- ✅ Syllable separation with hyphens

### Musical Accuracy
- ✅ Correct downbeat identification
- ✅ Proper pickup note handling
- ✅ Accurate chord-to-syllable mapping
- ✅ Time signature compliance

### Professional Quality
- ✅ Indistinguishable from hand-written lead sheets
- ✅ Musician-ready for live performance
- ✅ Educational quality for music instruction
- ✅ Industry-standard Nashville Number System

---

**This specification ensures consistent, professional-quality Nashville Number System chord charts with perfect measure-based alignment.**