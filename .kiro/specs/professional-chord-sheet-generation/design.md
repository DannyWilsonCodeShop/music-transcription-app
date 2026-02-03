# Professional Chord Sheet Generation - Design Document

**Feature Name**: professional-chord-sheet-generation  
**Created**: 2026-01-29  
**Status**: Design In Progress  
**Target Accuracy**: 95%+ chord detection

---

## Overview

This design transforms the current basic chord detection system into a professional-grade music transcription pipeline. The core challenge is replacing the existing librosa chromagram approach (which detects only 3-5 chords per song) with advanced machine learning models capable of 95%+ accuracy across complete songs.

The system will process YouTube audio through four main stages:
1. **Audio Analysis**: ML-based chord detection covering entire song duration
2. **Metadata Extraction**: LLM-powered parsing of YouTube metadata
3. **Musical Analysis**: Tempo, time signature, and key detection
4. **Professional Rendering**: Staff notation with Nashville numbers in publication-quality PDF

---

## Architecture

### High-Level System Flow

```
YouTube URL → Audio Download → Audio Analysis Pipeline → Metadata Extraction → PDF Generation → S3 Storage
                                      ↓                          ↓
                                 DynamoDB Storage          YouTube API + LLM
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway / Lambda                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Service                         │
│  - Job management                                                │
│  - Progress tracking                                             │
│  - Error handling                                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌────────────────────┼────────────────────┐
        ↓                    ↓                     ↓
┌──────────────┐   ┌──────────────────┐   ┌──────────────┐
│   Audio      │   │    Metadata      │   │   Musical    │
│  Analysis    │   │   Extraction     │   │   Analysis   │
│              │   │                  │   │              │
│ - Chord      │   │ - YouTube API    │   │ - Tempo      │
│   Detection  │   │ - LLM Parsing    │   │ - Time Sig   │
│ - ML Model   │   │ - Enrichment     │   │ - Structure  │
└──────────────┘   └──────────────────┘   └──────────────┘
        │                    │                     │
        └────────────────────┼─────────────────────┘
                             ↓
                   ┌──────────────────┐
                   │  PDF Generation  │
                   │                  │
                   │ - Staff Notation │
                   │ - Nashville #s   │
                   │ - Layout Engine  │
                   └──────────────────┘
                             ↓
                   ┌──────────────────┐
                   │   S3 + DynamoDB  │
                   └──────────────────┘
```

---

## Components and Interfaces

### 1. Audio Analysis Service

**Purpose**: Detect chords throughout entire song with 95%+ accuracy

**Key Design Decision**: Replace librosa chromagram with pre-trained deep learning model

#### Chord Detection Approach

**Current Problem**: Librosa's chromagram-based approach:
- Uses basic pitch class profiles
- No temporal context modeling
- Detects only strongest harmonic content
- Results: 3-5 chords for 5-minute song (massive under-detection)

**Solution**: Deep Learning Model Pipeline

**Option A: Essentia with Pre-trained Models** (RECOMMENDED)
```python
# Essentia provides state-of-the-art chord detection
import essentia.standard as es

# Load pre-trained chord detection model
chord_detector = es.ChordsDetection(
    hopSize=2048,
    windowSize=4096,
    sampleRate=44100
)

# Process entire audio file
audio = es.MonoLoader(filename=audio_path, sampleRate=44100)()
chords, strengths = chord_detector(audio)
```

**Why Essentia**:
- Pre-trained on millions of songs
- Detects 24 chord classes (major, minor, 7th, etc.)
- Temporal smoothing built-in
- 85-90% accuracy baseline
- Can be fine-tuned for 95%+ accuracy

**Option B: CREMA (Convolutional and Recurrent Estimators for Music Analysis)**
- State-of-the-art research model
- 90%+ accuracy on benchmark datasets
- Requires more integration work

**Option C: Chordino NNLS (Librosa + Better Algorithm)**
- Improvement over basic chromagram
- 70-80% accuracy (insufficient for requirements)
- Fallback option only


**Selected Approach**: Essentia with ensemble refinement

```python
class ChordDetectionService:
    """
    Advanced chord detection using Essentia ML models
    """
    
    def __init__(self):
        self.essentia_detector = es.ChordsDetection()
        self.beat_tracker = es.BeatTrackerMultiFeature()
        self.key_detector = es.KeyExtractor()
    
    def detect_chords(self, audio_path: str) -> ChordProgression:
        """
        Detect chords throughout entire song
        
        Returns:
            ChordProgression with timing, confidence, and chord quality
        """
        # Load audio at consistent sample rate
        audio = self.load_audio(audio_path, sample_rate=44100)
        
        # Detect key first (improves chord detection accuracy)
        key, scale, strength = self.key_detector(audio)
        
        # Run chord detection with frame-by-frame analysis
        chords, strengths = self.essentia_detector(audio)
        
        # Post-process: smooth transitions, filter low-confidence
        refined_chords = self.refine_chord_sequence(
            chords, strengths, key, scale
        )
        
        # Align chords to beat grid for musical accuracy
        beat_aligned_chords = self.align_to_beats(
            refined_chords, audio
        )
        
        return ChordProgression(
            chords=beat_aligned_chords,
            key=key,
            scale=scale,
            confidence_scores=strengths
        )
    
    def refine_chord_sequence(
        self, 
        chords: List[str], 
        strengths: List[float],
        key: str,
        scale: str
    ) -> List[Chord]:
        """
        Post-processing to improve accuracy:
        1. Filter chords below confidence threshold (0.3)
        2. Smooth rapid transitions (< 0.5 seconds)
        3. Apply music theory constraints (key context)
        4. Detect extended chords (7th, 9th, sus)
        """
        refined = []
        
        for i, (chord, strength) in enumerate(zip(chords, strengths)):
            # Skip low-confidence detections
            if strength < 0.3:
                continue
            
            # Smooth rapid changes (likely detection noise)
            if i > 0 and self.time_diff(i, i-1) < 0.5:
                if strengths[i-1] > strength:
                    continue  # Keep previous chord
            
            # Enhance chord quality using key context
            enhanced_chord = self.enhance_chord_quality(
                chord, key, scale, audio_segment
            )
            
            refined.append(Chord(
                name=enhanced_chord,
                start_time=self.frame_to_time(i),
                confidence=strength
            ))
        
        return refined
    
    def enhance_chord_quality(
        self, 
        basic_chord: str, 
        key: str, 
        scale: str,
        audio_segment: np.ndarray
    ) -> str:
        """
        Detect extended chord qualities (7th, 9th, sus, add)
        using harmonic analysis of audio segment
        """
        # Analyze harmonic content
        spectrum = self.compute_harmonic_spectrum(audio_segment)
        
        # Check for 7th presence
        if self.has_seventh(spectrum, basic_chord):
            if self.is_major_seventh(spectrum):
                return f"{basic_chord}maj7"
            else:
                return f"{basic_chord}7"
        
        # Check for sus chords
        if self.has_suspended(spectrum, basic_chord):
            return f"{basic_chord}sus4"
        
        # Check for added tones
        if self.has_ninth(spectrum, basic_chord):
            return f"{basic_chord}add9"
        
        return basic_chord
```

**Interface**:
```python
@dataclass
class Chord:
    name: str              # e.g., "Cmaj7", "Am", "G7"
    start_time: float      # seconds
    duration: float        # seconds
    confidence: float      # 0.0 to 1.0
    nashville_number: str  # e.g., "1", "6m", "5/7"

@dataclass
class ChordProgression:
    chords: List[Chord]
    key: str              # e.g., "C major"
    scale: str            # "major" or "minor"
    confidence_scores: List[float]
    total_duration: float
```

---

### 2. Metadata Extraction Service

**Purpose**: Extract accurate song information from YouTube video

**Challenge**: YouTube titles are inconsistent:
- "Artist - Song Name (Official Video)"
- "Song Name by Artist [HD]"
- "Artist: Song (feat. Other Artist) | Lyrics"

**Solution**: LLM-powered structured extraction

```python
class MetadataExtractionService:
    """
    Extract structured song metadata using YouTube API + LLM
    """
    
    def __init__(self, youtube_api_key: str, llm_client):
        self.youtube = YouTubeAPI(api_key=youtube_api_key)
        self.llm = llm_client
    
    async def extract_metadata(self, video_id: str) -> SongMetadata:
        """
        Extract and parse song metadata
        """
        # Get raw metadata from YouTube
        video_info = await self.youtube.get_video_details(video_id)
        
        # Parse with LLM
        parsed = await self.parse_with_llm(
            title=video_info.title,
            description=video_info.description,
            channel_name=video_info.channel_name
        )
        
        # Enrich with music databases (optional)
        enriched = await self.enrich_metadata(parsed)
        
        return enriched
    
    async def parse_with_llm(
        self, 
        title: str, 
        description: str,
        channel_name: str
    ) -> ParsedMetadata:
        """
        Use LLM to extract structured information
        """
        prompt = f"""
        Extract song information from this YouTube video:
        
        Title: {title}
        Description: {description}
        Channel: {channel_name}
        
        Return JSON with:
        - song_name: The actual song title (clean, no extras)
        - artist: Primary artist/band
        - featured_artists: List of featured artists (if any)
        - composer: Songwriter/composer (if mentioned)
        - version: e.g., "Live", "Acoustic", "Remix" (if applicable)
        - is_official: true if official artist channel
        
        Remove: "(Official Video)", "[HD]", "Lyrics", "Audio", etc.
        """
        
        response = await self.llm.complete(
            prompt=prompt,
            response_format="json"
        )
        
        return ParsedMetadata(**response)
    
    async def enrich_metadata(
        self, 
        parsed: ParsedMetadata
    ) -> SongMetadata:
        """
        Optionally enrich with MusicBrainz or Spotify
        """
        # Try MusicBrainz for composer/songwriter info
        mb_data = await self.query_musicbrainz(
            song=parsed.song_name,
            artist=parsed.artist
        )
        
        if mb_data:
            parsed.composer = mb_data.composer or parsed.composer
            parsed.year = mb_data.year
        
        return SongMetadata(
            song_name=parsed.song_name,
            artist=parsed.artist,
            featured_artists=parsed.featured_artists,
            composer=parsed.composer,
            version=parsed.version,
            year=parsed.year,
            source_video_id=parsed.video_id
        )
```

**Interface**:
```python
@dataclass
class SongMetadata:
    song_name: str
    artist: str
    featured_artists: List[str]
    composer: Optional[str]
    version: Optional[str]  # "Live", "Acoustic", etc.
    year: Optional[int]
    source_video_id: str
    is_official: bool
```

---

### 3. Musical Analysis Service

**Purpose**: Detect tempo, time signature, and song structure

```python
class MusicalAnalysisService:
    """
    Analyze musical characteristics of audio
    """
    
    def __init__(self):
        self.tempo_detector = es.RhythmExtractor2013()
        self.beat_tracker = es.BeatTrackerMultiFeature()
    
    def analyze(self, audio_path: str) -> MusicalAnalysis:
        """
        Perform complete musical analysis
        """
        audio = self.load_audio(audio_path)
        
        # Tempo detection
        bpm, beats, confidence, _, beat_intervals = self.tempo_detector(audio)
        
        # Time signature detection
        time_signature = self.detect_time_signature(beat_intervals)
        
        # Song structure (optional, best-effort)
        structure = self.detect_structure(audio, beats)
        
        return MusicalAnalysis(
            tempo_bpm=round(bpm, 1),
            time_signature=time_signature,
            beats=beats,
            structure=structure
        )
    
    def detect_time_signature(
        self, 
        beat_intervals: np.ndarray
    ) -> TimeSignature:
        """
        Infer time signature from beat patterns
        """
        # Analyze beat interval patterns
        # Common patterns: 4/4 (most common), 3/4 (waltz), 6/8
        
        # Use autocorrelation to find strong beat pattern
        strong_beat_pattern = self.find_strong_beat_pattern(beat_intervals)
        
        if strong_beat_pattern == 4:
            return TimeSignature(numerator=4, denominator=4)
        elif strong_beat_pattern == 3:
            return TimeSignature(numerator=3, denominator=4)
        elif strong_beat_pattern == 6:
            return TimeSignature(numerator=6, denominator=8)
        else:
            return TimeSignature(numerator=4, denominator=4)  # default
    
    def detect_structure(
        self, 
        audio: np.ndarray, 
        beats: np.ndarray
    ) -> Optional[SongStructure]:
        """
        Detect verse/chorus/bridge sections (best-effort)
        Uses self-similarity matrix analysis
        """
        # This is optional and may not be 100% accurate
        # Use for layout optimization, not critical path
        try:
            segments = self.segment_audio(audio, beats)
            labeled_segments = self.label_segments(segments)
            return SongStructure(sections=labeled_segments)
        except:
            return None  # Graceful degradation
```

**Interface**:
```python
@dataclass
class TimeSignature:
    numerator: int    # e.g., 4 in 4/4
    denominator: int  # e.g., 4 in 4/4

@dataclass
class MusicalAnalysis:
    tempo_bpm: float
    time_signature: TimeSignature
    beats: np.ndarray  # Beat timestamps
    structure: Optional[SongStructure]

@dataclass
class SongStructure:
    sections: List[Section]  # Verse, Chorus, Bridge, etc.
```

---

### 4. Nashville Number Service

**Purpose**: Convert chords to Nashville number system

```python
class NashvilleNumberService:
    """
    Convert chords to Nashville numbers based on key
    """
    
    # Scale degree mappings
    MAJOR_SCALE = ['1', '2', '3', '4', '5', '6', '7']
    MINOR_SCALE = ['1', '2', 'b3', '4', '5', 'b6', 'b7']
    
    def __init__(self):
        self.note_to_number = self.build_note_mappings()
    
    def convert_chord(
        self, 
        chord: Chord, 
        key: str, 
        scale: str
    ) -> str:
        """
        Convert chord to Nashville number
        
        Examples:
        - C in key of C major → "1"
        - Am in key of C major → "6m"
        - Gmaj7 in key of C major → "5maj7"
        - C/E in key of C major → "1/3"
        """
        # Parse chord components
        root, quality, extensions, bass = self.parse_chord(chord.name)
        
        # Get scale degree for root
        degree = self.get_scale_degree(root, key, scale)
        
        # Format number with quality
        number = self.format_number(degree, quality, extensions)
        
        # Handle slash chords
        if bass and bass != root:
            bass_degree = self.get_scale_degree(bass, key, scale)
            number = f"{number}/{bass_degree}"
        
        return number
    
    def get_scale_degree(
        self, 
        note: str, 
        key: str, 
        scale: str
    ) -> str:
        """
        Calculate scale degree of note in given key
        """
        # Convert note and key to semitone numbers
        note_num = self.note_to_semitone(note)
        key_num = self.note_to_semitone(key)
        
        # Calculate interval
        interval = (note_num - key_num) % 12
        
        # Map to scale degree
        scale_degrees = self.MAJOR_SCALE if scale == 'major' else self.MINOR_SCALE
        return scale_degrees[interval]
    
    def format_number(
        self, 
        degree: str, 
        quality: str, 
        extensions: str
    ) -> str:
        """
        Format Nashville number with quality indicators
        
        Conventions:
        - Uppercase = major (1, 4, 5)
        - Lowercase = minor (2m, 3m, 6m)
        - Extensions preserved (7, maj7, sus4, add9)
        """
        if quality == 'minor':
            return f"{degree}m{extensions}"
        elif quality == 'diminished':
            return f"{degree}°{extensions}"
        elif quality == 'augmented':
            return f"{degree}+{extensions}"
        else:
            return f"{degree}{extensions}"
```

---

### 5. PDF Generation Service

**Purpose**: Generate professional staff notation with chords and Nashville numbers

**Key Requirements**:
- Musical staff with 5 lines
- Measure bars based on time signature
- Chord symbols above staff
- Nashville numbers below staff
- Key and time signature at start
- Multi-page support with headers

**Technology Choice**: VexFlow + PDF rendering

```python
class PDFGenerationService:
    """
    Generate professional chord sheet PDF with staff notation
    """
    
    def __init__(self):
        self.vexflow_renderer = VexFlowRenderer()
        self.layout_engine = LayoutEngine()
    
    def generate_chord_sheet(
        self,
        metadata: SongMetadata,
        chords: ChordProgression,
        analysis: MusicalAnalysis
    ) -> bytes:
        """
        Generate complete chord sheet PDF
        """
        # Calculate layout
        layout = self.layout_engine.calculate_layout(
            chords=chords,
            time_signature=analysis.time_signature,
            measures_per_line=4
        )
        
        # Create document
        doc = PDFDocument(size='letter')
        
        # Add header
        self.add_header(doc, metadata, chords.key, analysis)
        
        # Render staves
        for page_num, page_layout in enumerate(layout.pages):
            if page_num > 0:
                doc.add_page()
            
            self.render_staves(
                doc, 
                page_layout, 
                chords, 
                analysis.time_signature
            )
        
        # Add footer
        self.add_footer(doc, metadata)
        
        return doc.to_bytes()
    
    def render_staves(
        self,
        doc: PDFDocument,
        page_layout: PageLayout,
        chords: ChordProgression,
        time_signature: TimeSignature
    ):
        """
        Render musical staves with chords and Nashville numbers
        """
        for staff_num, staff_layout in enumerate(page_layout.staves):
            y_position = 100 + (staff_num * 120)  # pixels
            
            # Draw staff lines (5 lines)
            self.draw_staff_lines(doc, y_position)
            
            # Add clef, key signature, time signature (first staff only)
            if staff_num == 0:
                self.draw_key_signature(doc, y_position, chords.key)
                self.draw_time_signature(doc, y_position, time_signature)
            
            # Draw measure bars
            for measure in staff_layout.measures:
                self.draw_measure_bar(doc, measure.x_position, y_position)
                
                # Add chords above staff
                for chord in measure.chords:
                    self.draw_chord_symbol(
                        doc, 
                        chord.name, 
                        chord.x_position, 
                        y_position - 30
                    )
                    
                    # Add Nashville number below staff
                    self.draw_nashville_number(
                        doc,
                        chord.nashville_number,
                        chord.x_position,
                        y_position + 70
                    )
```


    
    def draw_staff_lines(self, doc: PDFDocument, y: int):
        """Draw 5 horizontal staff lines"""
        for i in range(5):
            line_y = y + (i * 10)
            doc.draw_line(50, line_y, 550, line_y, width=1)
    
    def draw_chord_symbol(
        self, 
        doc: PDFDocument, 
        chord: str, 
        x: int, 
        y: int
    ):
        """Draw chord symbol above staff"""
        doc.draw_text(
            chord, 
            x, 
            y, 
            font='Arial-Bold', 
            size=14
        )
    
    def draw_nashville_number(
        self, 
        doc: PDFDocument, 
        number: str, 
        x: int, 
        y: int
    ):
        """Draw Nashville number below staff"""
        doc.draw_text(
            number, 
            x, 
            y, 
            font='Arial', 
            size=12,
            color='#666666'
        )
```

**Layout Engine**:
```python
class LayoutEngine:
    """
    Calculate optimal layout for chord sheet
    """
    
    def calculate_layout(
        self,
        chords: ChordProgression,
        time_signature: TimeSignature,
        measures_per_line: int = 4
    ) -> DocumentLayout:
        """
        Organize chords into measures, lines, and pages
        """
        # Group chords into measures based on time signature
        measures = self.group_into_measures(
            chords, 
            time_signature
        )
        
        # Organize measures into lines
        lines = self.organize_into_lines(
            measures, 
            measures_per_line
        )
        
        # Paginate (4-5 staves per page)
        pages = self.paginate(lines, staves_per_page=5)
        
        return DocumentLayout(pages=pages)
    
    def group_into_measures(
        self,
        chords: ChordProgression,
        time_signature: TimeSignature
    ) -> List[Measure]:
        """
        Group chords into measures based on time signature
        """
        measure_duration = self.calculate_measure_duration(time_signature)
        measures = []
        current_measure = Measure(number=1, chords=[])
        current_time = 0.0
        
        for chord in chords.chords:
            # Check if chord fits in current measure
            if current_time + chord.duration > measure_duration:
                # Start new measure
                measures.append(current_measure)
                current_measure = Measure(
                    number=len(measures) + 1, 
                    chords=[]
                )
                current_time = 0.0
            
            current_measure.chords.append(chord)
            current_time += chord.duration
        
        # Add final measure
        if current_measure.chords:
            measures.append(current_measure)
        
        return measures
```

---

## Data Models

### DynamoDB Schema Updates

**Table**: `chord-sheets`

```python
{
    "PK": "SHEET#<sheet_id>",
    "SK": "METADATA",
    
    # Existing fields
    "videoId": str,
    "status": str,  # "processing", "completed", "failed"
    "createdAt": str,
    "pdfUrl": str,
    
    # NEW: Enhanced metadata
    "songName": str,
    "artist": str,
    "featuredArtists": List[str],
    "composer": Optional[str],
    "version": Optional[str],
    "year": Optional[int],
    "isOfficial": bool,
    
    # NEW: Musical analysis
    "key": str,              # "C major"
    "scale": str,            # "major" or "minor"
    "tempoBpm": float,
    "timeSignature": {
        "numerator": int,
        "denominator": int
    },
    
    # NEW: Quality metrics
    "chordCount": int,
    "averageConfidence": float,
    "processingTimeSeconds": float,
    
    # NEW: Detailed chord progression
    "chords": [
        {
            "name": str,           # "Cmaj7"
            "startTime": float,    # seconds
            "duration": float,
            "confidence": float,
            "nashvilleNumber": str # "1maj7"
        }
    ],
    
    # Optional structure
    "structure": Optional[{
        "sections": [
            {
                "type": str,      # "verse", "chorus", "bridge"
                "startTime": float,
                "endTime": float
            }
        ]
    }]
}
```

### Internal Data Models

```python
from dataclasses import dataclass
from typing import List, Optional
import numpy as np

@dataclass
class Chord:
    """Single chord with timing and confidence"""
    name: str
    start_time: float
    duration: float
    confidence: float
    nashville_number: str

@dataclass
class ChordProgression:
    """Complete chord progression for a song"""
    chords: List[Chord]
    key: str
    scale: str
    confidence_scores: List[float]
    total_duration: float
    
    @property
    def average_confidence(self) -> float:
        return np.mean(self.confidence_scores)

@dataclass
class SongMetadata:
    """Parsed song information"""
    song_name: str
    artist: str
    featured_artists: List[str]
    composer: Optional[str]
    version: Optional[str]
    year: Optional[int]
    source_video_id: str
    is_official: bool

@dataclass
class TimeSignature:
    """Musical time signature"""
    numerator: int
    denominator: int
    
    def __str__(self) -> str:
        return f"{self.numerator}/{self.denominator}"

@dataclass
class MusicalAnalysis:
    """Complete musical analysis"""
    tempo_bpm: float
    time_signature: TimeSignature
    beats: np.ndarray
    structure: Optional['SongStructure']

@dataclass
class Section:
    """Song section (verse, chorus, etc.)"""
    type: str  # "verse", "chorus", "bridge", "intro", "outro"
    start_time: float
    end_time: float
    measure_start: int
    measure_end: int

@dataclass
class SongStructure:
    """Song structure with labeled sections"""
    sections: List[Section]

@dataclass
class Measure:
    """Musical measure containing chords"""
    number: int
    chords: List[Chord]
    x_position: int  # For layout

@dataclass
class StaffLayout:
    """Layout for one staff line"""
    measures: List[Measure]
    y_position: int

@dataclass
class PageLayout:
    """Layout for one page"""
    staves: List[StaffLayout]
    page_number: int

@dataclass
class DocumentLayout:
    """Complete document layout"""
    pages: List[PageLayout]
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Before defining the correctness properties, I need to analyze each acceptance criterion to determine which are testable as properties, examples, or edge cases.



### Property Reflection

Reviewing the prework analysis to identify redundant or overlapping properties:

**Redundancies Identified**:
1. Properties 4.6 and 5.2 are identical (Nashville numbers aligned with chords) - will combine into single property
2. Properties 1.2, 1.5, and 1.6 all test LLM parsing of titles - can combine into comprehensive parsing property
3. Properties 4.3 and 4.4 are both simple examples of "required elements present" - can combine

**Consolidations**:
- Metadata parsing (1.2, 1.5, 1.6) → Single property: "LLM parsing extracts clean, structured data"
- Staff notation elements (4.3, 4.4, 6.6) → Single example: "Required PDF elements present"
- Nashville alignment (4.6, 5.2) → Single property: "Nashville numbers aligned with chords"

This reduces 30+ potential properties to ~20 unique, non-redundant properties.

---

### Correctness Properties

#### Metadata Extraction Properties

**Property 1: YouTube API data retrieval**
*For any* valid YouTube video ID, calling the metadata extraction service should return non-empty title and description fields.
**Validates: Requirements 1.1**

**Property 2: LLM parsing produces clean structured data**
*For any* YouTube title containing song information (with or without noise like "(Official Video)", "[HD]", "Lyrics"), the LLM parser should extract a song name that does not contain these noise markers and should identify artist, featured artists, and version information when present in standard formats ("Artist - Song", "Song by Artist", "Artist: Song").
**Validates: Requirements 1.2, 1.5, 1.6**

**Property 3: Artist vs uploader distinction**
*For any* video where the channel name differs from the artist name mentioned in the title, the parsed metadata should correctly identify the artist from the title, not the channel name.
**Validates: Requirements 1.3**

**Property 4: Composer extraction when available**
*For any* video description containing composer/songwriter information (keywords: "written by", "composed by", "songwriter"), the metadata extraction should populate the composer field.
**Validates: Requirements 1.4**

#### Chord Detection Properties

**Property 5: Complete temporal coverage**
*For any* audio file, the sum of all detected chord durations should equal the total audio duration (within 1 second tolerance), ensuring no gaps in chord coverage.
**Validates: Requirements 2.2**

**Property 6: Minimum temporal resolution**
*For any* detected chord sequence, consecutive chords should have durations of at least 0.5 seconds (preventing over-segmentation noise).
**Validates: Requirements 2.1**

**Property 7: Extended chord detection**
*For any* chord progression, at least one chord type beyond basic major/minor should be detected (7th, maj7, sus, add, dim, aug) when the audio contains harmonic complexity.
**Validates: Requirements 2.3**

**Property 8: Slash chord notation**
*For any* detected chord with a bass note different from the root, the chord name should be formatted as a slash chord (e.g., "C/E", "G/B").
**Validates: Requirements 2.4**

**Property 9: Confidence scores present**
*For any* detected chord, a confidence score between 0.0 and 1.0 must be provided.
**Validates: Requirements 2.6**

#### Musical Analysis Properties

**Property 10: Valid tempo range**
*For any* audio input, the detected tempo should be between 40 and 240 BPM (reasonable musical range).
**Validates: Requirements 3.1**

**Property 11: Valid time signature format**
*For any* audio input, the detected time signature should have a numerator between 2 and 12 and a denominator that is a power of 2 (2, 4, 8, 16).
**Validates: Requirements 3.2**

**Property 12: Non-overlapping song sections**
*For any* detected song structure, all sections should have non-overlapping time ranges and should collectively cover the song duration.
**Validates: Requirements 3.5**

#### Nashville Number Properties

**Property 13: Nashville number correctness**
*For any* chord and key combination, the Nashville number should correctly represent the scale degree of the chord root relative to the key (e.g., C in key of C = "1", Am in key of C = "6m", G in key of C = "5").
**Validates: Requirements 5.1**

**Property 14: Nashville case conventions**
*For any* Nashville number, major chords should use uppercase numbers and minor chords should use lowercase "m" suffix (e.g., "1" for major, "6m" for minor).
**Validates: Requirements 5.3**

**Property 15: Nashville extension preservation**
*For any* extended chord (7th, maj7, sus4, add9, etc.), the Nashville number should preserve the extension notation (e.g., "1maj7", "5sus4").
**Validates: Requirements 5.4**

**Property 16: Nashville slash chord notation**
*For any* slash chord, the Nashville notation should show both the chord and bass note as scale degrees separated by "/" (e.g., "1/3" for C/E in key of C).
**Validates: Requirements 5.5**

#### PDF Layout Properties

**Property 17: Measure calculation accuracy**
*For any* chord progression with known time signature and tempo, the number of measures should equal the total duration divided by measure duration (within rounding tolerance).
**Validates: Requirements 4.2**

**Property 18: Chord positioning correspondence**
*For any* chord in the progression, its position in the PDF should correspond to its timestamp relative to the song duration (proportional spacing).
**Validates: Requirements 4.5**

**Property 19: Nashville-chord alignment**
*For any* chord symbol in the PDF, there should be a Nashville number directly below it at the same horizontal position (within 5 pixels).
**Validates: Requirements 4.6, 5.2**

**Property 20: Multi-page pagination**
*For any* song with more than 5 staves worth of content, multiple pages should be generated, and each page after the first should contain a page number.
**Validates: Requirements 4.8, 6.5**

**Property 21: Measures per line constraint**
*For any* staff line in the layout, the number of measures should be between 4 and 8 (optimal readability range).
**Validates: Requirements 6.3**

**Property 22: Required metadata in header**
*For any* generated PDF, the header should contain all of: song name, artist, key, tempo (BPM), and time signature.
**Validates: Requirements 6.2**

---

## Error Handling

### Error Categories

#### 1. Audio Processing Errors

**Invalid Audio Format**
```python
class InvalidAudioFormatError(Exception):
    """Raised when audio file cannot be decoded"""
    pass

def handle_audio_error(audio_path: str) -> ErrorResponse:
    try:
        audio = load_audio(audio_path)
    except Exception as e:
        logger.error(f"Failed to load audio: {e}")
        return ErrorResponse(
            code="INVALID_AUDIO",
            message="Audio file format not supported or corrupted",
            retry=False
        )
```

**Chord Detection Failure**
```python
def handle_chord_detection_failure(
    chords: List[Chord], 
    audio_duration: float
) -> Optional[ErrorResponse]:
    """
    Validate chord detection results
    """
    # Check for catastrophic failure (no chords detected)
    if len(chords) == 0:
        return ErrorResponse(
            code="NO_CHORDS_DETECTED",
            message="Chord detection failed to identify any chords",
            retry=True
        )
    
    # Check for insufficient coverage
    total_coverage = sum(c.duration for c in chords)
    coverage_ratio = total_coverage / audio_duration
    
    if coverage_ratio < 0.8:
        logger.warning(
            f"Low chord coverage: {coverage_ratio:.1%} of song duration"
        )
        # Continue but flag quality issue
        return None
    
    # Check for low confidence
    avg_confidence = np.mean([c.confidence for c in chords])
    if avg_confidence < 0.4:
        logger.warning(f"Low average confidence: {avg_confidence:.2f}")
        # Continue but flag quality issue
    
    return None
```

#### 2. Metadata Extraction Errors

**YouTube API Errors**
```python
def handle_youtube_api_error(video_id: str, error: Exception) -> ErrorResponse:
    """
    Handle YouTube API failures with retry logic
    """
    if isinstance(error, QuotaExceededError):
        return ErrorResponse(
            code="YOUTUBE_QUOTA_EXCEEDED",
            message="YouTube API quota exceeded, try again later",
            retry=True,
            retry_after=3600  # 1 hour
        )
    elif isinstance(error, VideoNotFoundError):
        return ErrorResponse(
            code="VIDEO_NOT_FOUND",
            message=f"YouTube video {video_id} not found or private",
            retry=False
        )
    else:
        return ErrorResponse(
            code="YOUTUBE_API_ERROR",
            message="Failed to fetch video metadata",
            retry=True
        )
```

**LLM Parsing Errors**
```python
def handle_llm_parsing_error(
    title: str, 
    error: Exception
) -> SongMetadata:
    """
    Fallback to rule-based parsing if LLM fails
    """
    logger.warning(f"LLM parsing failed, using fallback: {error}")
    
    # Simple rule-based parsing
    parsed = simple_title_parser(title)
    
    return SongMetadata(
        song_name=parsed.song or title,
        artist=parsed.artist or "Unknown Artist",
        featured_artists=[],
        composer=None,
        version=None,
        year=None,
        source_video_id=video_id,
        is_official=False
    )
```

#### 3. PDF Generation Errors

**Layout Calculation Errors**
```python
def handle_layout_error(
    chords: ChordProgression,
    error: Exception
) -> ErrorResponse:
    """
    Handle PDF layout calculation failures
    """
    logger.error(f"Layout calculation failed: {error}")
    
    # Try simplified layout
    try:
        simplified_layout = create_simple_layout(chords)
        return None  # Success with fallback
    except Exception as e:
        return ErrorResponse(
            code="LAYOUT_FAILED",
            message="Failed to generate PDF layout",
            retry=False
        )
```

**Rendering Errors**
```python
def handle_rendering_error(error: Exception) -> ErrorResponse:
    """
    Handle PDF rendering failures
    """
    logger.error(f"PDF rendering failed: {error}")
    return ErrorResponse(
        code="PDF_GENERATION_FAILED",
        message="Failed to generate PDF document",
        retry=True
    )
```

### Error Response Model

```python
@dataclass
class ErrorResponse:
    code: str
    message: str
    retry: bool
    retry_after: Optional[int] = None  # seconds
    details: Optional[Dict] = None
```

### Graceful Degradation Strategy

**Priority Levels**:
1. **Critical**: Chord detection, basic metadata
2. **Important**: Musical analysis (tempo, time signature)
3. **Nice-to-have**: Song structure, extended chord qualities

**Degradation Rules**:
- If tempo detection fails → use default 120 BPM
- If time signature detection fails → use default 4/4
- If structure detection fails → omit structure, continue
- If LLM parsing fails → use rule-based fallback
- If extended chord detection fails → use basic major/minor only

---

## Testing Strategy

### Dual Testing Approach

This system requires both **unit tests** for specific scenarios and **property-based tests** for comprehensive validation across diverse inputs.

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- Specific song examples with known ground truth
- Edge cases (very short songs, unusual time signatures)
- Error conditions (invalid audio, API failures)
- Integration between components

**Property Tests**: Verify universal properties across all inputs
- Run minimum 100 iterations per property
- Generate random but valid test data
- Verify properties hold for all generated inputs
- Catch edge cases through randomization

### Property-Based Testing Configuration

**Library**: Use `hypothesis` (Python) for property-based testing

**Test Structure**:
```python
from hypothesis import given, strategies as st
import pytest

@given(
    video_id=st.text(min_size=11, max_size=11, alphabet=st.characters()),
    title=st.text(min_size=10, max_size=200)
)
def test_metadata_extraction_completeness(video_id, title):
    """
    Feature: professional-chord-sheet-generation
    Property 1: YouTube API data retrieval
    
    For any valid YouTube video ID, metadata extraction 
    should return non-empty title and description.
    """
    # Mock YouTube API response
    mock_response = YouTubeVideo(
        id=video_id,
        title=title,
        description="Test description"
    )
    
    # Extract metadata
    metadata = metadata_service.extract(mock_response)
    
    # Verify property
    assert metadata.song_name is not None
    assert len(metadata.song_name) > 0
    assert metadata.artist is not None
```

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with property number and text
- Seed randomization for reproducibility
- Timeout: 60 seconds per property test

### Unit Test Examples

```python
def test_chord_detection_complete_song():
    """
    Test chord detection on known song
    """
    audio_path = "test_data/wonderwall.mp3"
    
    chords = chord_service.detect_chords(audio_path)
    
    # Verify coverage
    assert len(chords.chords) >= 20  # Known to have many chords
    assert chords.key == "F# minor"
    
    # Verify specific chords present
    chord_names = [c.name for c in chords.chords]
    assert "F#m" in chord_names
    assert "A" in chord_names
    assert "E" in chord_names

def test_nashville_conversion_edge_cases():
    """
    Test Nashville number conversion for edge cases
    """
    service = NashvilleNumberService()
    
    # Test slash chord
    assert service.convert_chord(
        Chord(name="C/E", ...), 
        key="C", 
        scale="major"
    ) == "1/3"
    
    # Test extended chord
    assert service.convert_chord(
        Chord(name="Gmaj7", ...), 
        key="C", 
        scale="major"
    ) == "5maj7"
    
    # Test minor chord
    assert service.convert_chord(
        Chord(name="Am", ...), 
        key="C", 
        scale="major"
    ) == "6m"

def test_pdf_generation_multi_page():
    """
    Test PDF generation for long song requiring multiple pages
    """
    # Create long chord progression (100 chords)
    chords = create_test_progression(num_chords=100)
    metadata = create_test_metadata()
    analysis = create_test_analysis()
    
    pdf_bytes = pdf_service.generate_chord_sheet(
        metadata, chords, analysis
    )
    
    # Verify multi-page
    pdf = parse_pdf(pdf_bytes)
    assert pdf.page_count >= 2
    assert pdf.pages[1].has_page_number()
```

### Integration Testing

```python
@pytest.mark.integration
def test_end_to_end_processing():
    """
    Test complete pipeline from YouTube URL to PDF
    """
    video_id = "test_video_id"
    
    # Run complete pipeline
    result = orchestrator.process_video(video_id)
    
    # Verify all components executed
    assert result.status == "completed"
    assert result.metadata is not None
    assert result.chords is not None
    assert result.analysis is not None
    assert result.pdf_url is not None
    
    # Verify quality metrics
    assert result.chord_count >= 20
    assert result.average_confidence >= 0.5
    assert result.processing_time_seconds < 210  # 3.5 minutes
```

### Performance Testing

```python
@pytest.mark.performance
def test_processing_time_requirement():
    """
    Verify processing completes within 3.5 minutes for 5-minute song
    """
    audio_path = "test_data/5_minute_song.mp3"
    
    start_time = time.time()
    result = orchestrator.process_audio(audio_path)
    elapsed = time.time() - start_time
    
    assert elapsed < 210  # 3.5 minutes = 210 seconds
    assert result.status == "completed"
```

### Test Data Requirements

**Test Audio Files**:
- Short song (2 minutes) - fast iteration
- Medium song (5 minutes) - standard case
- Long song (8 minutes) - stress test
- Various genres (rock, jazz, classical) - diversity
- Various keys and time signatures - edge cases

**Ground Truth Data**:
- Manually verified chord progressions for accuracy testing
- Known metadata for parsing validation
- Reference PDFs for layout comparison

---

## Implementation Notes

### Technology Stack

**Backend**:
- Python 3.11+ (for audio processing)
- Essentia (chord detection)
- librosa (audio utilities)
- boto3 (AWS services)
- httpx (async HTTP client)

**APIs**:
- YouTube Data API v3
- Claude/GPT-4 API (metadata parsing)
- Optional: MusicBrainz API

**PDF Generation**:
- ReportLab (PDF creation)
- VexFlow (music notation rendering via Node.js subprocess)
- Or: abcjs with SVG-to-PDF conversion

**Infrastructure**:
- AWS Lambda (orchestration)
- AWS ECS Fargate (heavy audio processing)
- DynamoDB (data storage)
- S3 (PDF storage)
- SQS (job queue)

### Performance Optimization

**Parallel Processing**:
```python
async def process_video_parallel(video_id: str):
    """
    Run independent tasks in parallel
    """
    # Start all tasks concurrently
    metadata_task = asyncio.create_task(
        metadata_service.extract(video_id)
    )
    audio_task = asyncio.create_task(
        download_audio(video_id)
    )
    
    # Wait for audio download
    audio_path = await audio_task
    
    # Start audio analysis (CPU-intensive)
    analysis_task = asyncio.create_task(
        run_in_executor(audio_service.analyze, audio_path)
    )
    
    # Wait for both
    metadata, analysis_result = await asyncio.gather(
        metadata_task,
        analysis_task
    )
    
    return metadata, analysis_result
```

**Caching Strategy**:
- Cache YouTube metadata (24 hours)
- Cache audio files temporarily (1 hour)
- Cache generated PDFs permanently
- Cache LLM parsing results (permanent)

### Deployment Strategy

**Phase 1: Core Functionality** (Week 1)
- Essentia chord detection integration
- Basic metadata extraction
- Simple PDF generation

**Phase 2: Enhancement** (Week 2)
- LLM metadata parsing
- Nashville number system
- Professional PDF layout

**Phase 3: Polish** (Week 3)
- Song structure detection
- Extended chord qualities
- Performance optimization
- Comprehensive testing

### Monitoring and Metrics

**Key Metrics**:
- Chord detection accuracy (target: 95%)
- Processing time (target: < 3.5 minutes)
- API success rate (target: 99%)
- Average confidence score (target: > 0.6)
- User satisfaction (qualitative feedback)

**Logging**:
```python
logger.info("Chord detection started", extra={
    "video_id": video_id,
    "audio_duration": duration
})

logger.info("Chord detection completed", extra={
    "video_id": video_id,
    "chord_count": len(chords),
    "average_confidence": avg_confidence,
    "processing_time": elapsed
})
```

---

## Open Questions

1. **Essentia Installation**: Essentia has complex dependencies - may need Docker container
2. **VexFlow Integration**: VexFlow is JavaScript - need Node.js subprocess or alternative
3. **LLM Choice**: Claude vs GPT-4 for metadata parsing (cost vs accuracy tradeoff)
4. **Ground Truth Data**: Need labeled dataset for accuracy validation
5. **Chord Detection Model**: May need to fine-tune Essentia model on specific genres

---

## Future Enhancements (Out of Scope)

- Lyrics extraction and alignment with chords
- Melody transcription
- Multiple instrument parts
- Interactive chord sheet editor
- Real-time transposition
- MIDI export
- Mobile app integration
- Collaborative editing

