# Enhanced Music Transcription System Specification

## 🎯 Objective
Upgrade the music transcription pipeline to collect and store all data needed for perfect Nashville Number System output with measure-based alignment.

## 📊 Data Collection Requirements

### 1. **Tempo Detection**
- **BPM (Beats Per Minute)**: Precise tempo measurement
- **Tempo Stability**: Track tempo changes throughout song
- **Beat Grid**: Exact timing of each beat
- **Storage**: `tempo: number, tempoChanges: [{time: number, bpm: number}]`

### 2. **Time Signature Analysis**
- **Meter Detection**: 3/4, 4/4, 6/8, etc.
- **Downbeat Identification**: Strong beats (1, 3 in 4/4 or 1 in 3/4)
- **Measure Boundaries**: Exact start/end times of each measure
- **Storage**: `timeSignature: string, measures: [{start: number, end: number, downbeat: number}]`

### 3. **Syllable-Level Lyrics**
- **Syllable Separation**: "A-maz-ing Grace" format
- **Timing Alignment**: Exact start/end time for each syllable
- **Downbeat Mapping**: Which syllables fall on strong beats
- **Verse Detection**: Automatic verse/chorus/bridge identification
- **Storage**: `syllables: [{text: string, start: number, end: number, isDownbeat: boolean, verse: string}]`

### 4. **High-Resolution Chord Detection**
- **0.2-Second Intervals**: Check for chord changes every 200ms
- **Root Chord Changes**: Focus on fundamental harmonic movement
- **Downbeat vs Passing**: Classify chords as strong-beat or passing
- **Up to 8 Passing Chords**: Between each pair of downbeats
- **Storage**: `chords: [{chord: string, start: number, end: number, isDownbeat: boolean, confidence: number}]`

### 5. **Musical Structure Analysis**
- **Song Sections**: Verse, Chorus, Bridge, Intro, Outro
- **Key Detection**: Root key and key changes
- **Nashville Numbers**: Convert chords to numbers based on key
- **Pickup Notes**: Identify anacrusis (weak beats before downbeats)

## 🗄️ Database Schema Updates

### Enhanced TranscriptionJob Model
```typescript
interface EnhancedTranscriptionJob {
  // Existing fields
  id: string;
  status: TranscriptionJobStatus;
  audioUrl?: string;
  youtubeUrl?: string;
  title?: string;
  artist?: string;
  userId?: string;
  createdAt: string;
  updatedAt: string;

  // NEW: Enhanced musical analysis
  musicalAnalysis: {
    // Tempo and timing
    tempo: {
      bpm: number;
      confidence: number;
      tempoChanges: Array<{
        time: number;
        bpm: number;
        confidence: number;
      }>;
    };

    // Time signature and measures
    timeSignature: {
      numerator: number;
      denominator: number;
      confidence: number;
      measures: Array<{
        start: number;
        end: number;
        downbeatTime: number;
        measureNumber: number;
      }>;
    };

    // Key and harmony
    key: {
      root: string;
      mode: 'major' | 'minor';
      confidence: number;
      keyChanges: Array<{
        time: number;
        key: string;
        mode: string;
        confidence: number;
      }>;
    };

    // High-resolution chord analysis
    chordAnalysis: {
      analysisInterval: number; // 0.2 seconds
      chords: Array<{
        chord: string;
        root: string;
        quality: string;
        start: number;
        end: number;
        isDownbeat: boolean;
        isPassingChord: boolean;
        nashvilleNumber: string;
        confidence: number;
        measureIndex: number;
        beatPosition: number;
      }>;
    };

    // Syllable-level lyrics with timing
    lyricsAnalysis: {
      syllables: Array<{
        text: string;
        start: number;
        end: number;
        isDownbeat: boolean;
        measureIndex: number;
        beatPosition: number;
        verse: string;
        line: number;
        wordIndex: number;
        syllableIndex: number;
      }>;
      
      verses: Array<{
        label: string; // "Verse 1", "Chorus", etc.
        start: number;
        end: number;
        syllableIndices: number[];
      }>;
    };

    // Song structure
    structure: {
      sections: Array<{
        type: 'intro' | 'verse' | 'chorus' | 'bridge' | 'outro';
        label: string;
        start: number;
        end: number;
        measureStart: number;
        measureEnd: number;
      }>;
    };
  };

  // Legacy fields (for backward compatibility)
  lyrics?: string;
  chords?: any;
}
```

## 🔧 Processing Pipeline Updates

### 1. **Audio Analysis Lambda (Enhanced)**
```typescript
// backend/functions-v2/audio-analyzer/index.js
export async function analyzeAudio(audioUrl: string) {
  const analysis = {
    tempo: await detectTempo(audioUrl),
    timeSignature: await detectTimeSignature(audioUrl),
    key: await detectKey(audioUrl),
    chords: await analyzeChords(audioUrl, { interval: 0.2 }),
    structure: await analyzeStructure(audioUrl)
  };
  
  return analysis;
}

async function analyzeChords(audioUrl: string, options: { interval: number }) {
  // Use librosa or similar for 0.2-second chord analysis
  const chords = [];
  const duration = await getAudioDuration(audioUrl);
  
  for (let time = 0; time < duration; time += options.interval) {
    const chord = await detectChordAtTime(audioUrl, time);
    if (chord) {
      chords.push({
        chord: chord.name,
        root: chord.root,
        start: time,
        end: time + options.interval,
        confidence: chord.confidence
      });
    }
  }
  
  return chords;
}
```

### 2. **Lyrics Analysis Lambda (New)**
```typescript
// backend/functions-v2/lyrics-analyzer/index.js
export async function analyzeLyrics(lyricsText: string, musicalTiming: any) {
  const syllables = await separateIntoSyllables(lyricsText);
  const timedSyllables = await alignSyllablesToBeats(syllables, musicalTiming);
  const verses = await detectVerses(timedSyllables);
  
  return {
    syllables: timedSyllables,
    verses: verses
  };
}

async function separateIntoSyllables(text: string) {
  // Advanced syllable separation using NLP
  // Handle cases like "A-maz-ing", "beau-ti-ful", etc.
}

async function alignSyllablesToBeats(syllables: any[], timing: any) {
  // Align syllables to musical beats and identify downbeats
}
```

### 3. **Musical Structure Analyzer (New)**
```typescript
// backend/functions-v2/structure-analyzer/index.js
export async function analyzeMusicalStructure(audioAnalysis: any, lyricsAnalysis: any) {
  const downbeats = identifyDownbeats(audioAnalysis.tempo, audioAnalysis.timeSignature);
  const passingChords = classifyPassingChords(audioAnalysis.chords, downbeats);
  const nashvilleNumbers = convertToNashvilleNumbers(passingChords, audioAnalysis.key);
  
  return {
    downbeats,
    passingChords,
    nashvilleNumbers,
    measureAlignment: alignChordsToMeasures(nashvilleNumbers, audioAnalysis.measures)
  };
}
```

## 🎼 Processing Workflow

### Step 1: Audio Analysis
1. **Tempo Detection** → BPM and beat grid
2. **Time Signature** → Meter and measure boundaries  
3. **Key Detection** → Root key and mode
4. **High-Res Chord Analysis** → 0.2s interval chord detection

### Step 2: Lyrics Processing
1. **Syllable Separation** → Individual syllables with hyphens
2. **Beat Alignment** → Map syllables to musical beats
3. **Downbeat Identification** → Mark strong-beat syllables
4. **Verse Detection** → Identify song sections

### Step 3: Musical Structure Analysis
1. **Downbeat Classification** → Separate strong vs weak beat chords
2. **Passing Chord Detection** → Up to 8 between downbeats
3. **Nashville Number Conversion** → Chord → number mapping
4. **Measure Alignment** → Perfect 4-measure grouping

### Step 4: Data Integration
1. **Combine All Analysis** → Merge timing, chords, lyrics
2. **Quality Validation** → Confidence scoring
3. **Database Storage** → Enhanced schema
4. **PDF Generation** → Perfect measure-based output

## 🚀 Implementation Priority

### Phase 1: Database Schema (Immediate)
- [ ] Update DynamoDB schema
- [ ] Add migration scripts
- [ ] Update GraphQL schema
- [ ] Test data storage

### Phase 2: Enhanced Audio Analysis (Week 1)
- [ ] Implement 0.2s chord detection
- [ ] Add tempo/time signature analysis
- [ ] Enhance key detection
- [ ] Add confidence scoring

### Phase 3: Lyrics Processing (Week 1)
- [ ] Advanced syllable separation
- [ ] Beat alignment algorithms
- [ ] Downbeat identification
- [ ] Verse detection

### Phase 4: Structure Analysis (Week 2)
- [ ] Passing chord classification
- [ ] Nashville number conversion
- [ ] Measure alignment
- [ ] Quality validation

### Phase 5: Integration & Testing (Week 2)
- [ ] End-to-end pipeline
- [ ] PDF generation integration
- [ ] Performance optimization
- [ ] Quality assurance

## 📈 Success Metrics

### Technical Accuracy
- **Tempo Detection**: ±2 BPM accuracy
- **Chord Detection**: 90%+ accuracy at 0.2s intervals
- **Syllable Alignment**: 95%+ correct beat placement
- **Downbeat Identification**: 98%+ accuracy

### Musical Quality
- **Nashville Numbers**: Correct key-relative numbering
- **Passing Chords**: Proper classification (max 8 per measure)
- **Measure Alignment**: Perfect 4-measure grouping
- **Professional Output**: Indistinguishable from hand-written charts

---

**This enhanced system will provide all the data needed for perfect Nashville Number System output with professional-quality measure-based alignment.**