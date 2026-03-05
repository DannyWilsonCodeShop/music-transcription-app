# v3.0 ChordScout Accuracy Improvements - Design Document

**Feature Name**: v3-accuracy-improvements  
**Created**: 2026-03-01  
**Status**: Design Phase  
**Target**: Enhanced transcription accuracy with multi-stem support

---

## Overview

ChordScout v3.0 transforms the bass-only transcription pipeline into a comprehensive multi-instrument analysis system. The core improvements address quantization granularity (8th notes vs 16th notes), add harmonic context through piano and guitar stem transcription, integrate song metadata and lyrics, and implement user confirmation workflows for transcription mode and key selection.

This design maintains full backward compatibility with v2.0 while adding significant new capabilities. The system architecture extends the existing ECS-based processing pipeline with new modules for stem transcription, song identification, and lyrics fetching.

**Key Design Principles**:
- Additive changes only (no breaking changes to v2.0 API)
- User control through confirmation workflows
- Graceful degradation when optional features fail
- Performance optimization through parallel processing
- Clear state management for async user interactions

---

## Architecture

### High-Level System Flow

```
Audio Upload → S3 Storage → ECS Task Trigger → Multi-Stage Processing → PDF Generation
                                    ↓
                            ┌───────┴────────┐
                            │  ECS Container │
                            └───────┬────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ↓                           ↓                           ↓
   Tempo/Downbeat          Stem Separation         Song Identification
   Detection (v2.0)        (NEW - Demucs)          (NEW - Fingerprint)
        │                       │                           │
        ↓                       ↓                           ↓
   User Confirms          Transcription Mode          Lyrics Fetch
   Downbeat (v2.0)        Selection (NEW)             (NEW - Genius API)
        │                       │                           │
        └───────────────────────┼───────────────────────────┘
                                ↓
                        Multi-Stem Transcription
                        (Bass + Piano + Guitar)
                                ↓
                        Key Detection & Confirmation
                                ↓
                        Nashville Number Generation
                                ↓
                        PDF Generation with Lyrics
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     API Gateway + Lambda                         │
│  - Upload handler (v2.0)                                         │
│  - Job status endpoint (v2.0)                                    │
│  - User confirmation endpoints (NEW)                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        DynamoDB                                  │
│  - Job records with extended schema                              │
│  - Status: PENDING_MODE_SELECTION, PENDING_KEY_CONFIRMATION      │
│  - New fields: transcriptionMode, detectedKey, confirmedKey,     │
│    songMetadata, lyrics, stemData                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ECS Task (bass-transcription-ecs)             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Stage 1: Audio Analysis (v2.0 + enhancements)             │ │
│  │  - Load audio from S3                                      │ │
│  │  - Tempo detection (librosa)                               │ │
│  │  - Downbeat detection (existing module)                    │ │
│  │  - Time signature detection                                │ │
│  │  → Status: PENDING_DOWNBEAT_CONFIRMATION                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Stage 2: Song Identification (NEW)                        │ │
│  │  - Audio fingerprinting (mutagen)                          │ │
│  │  - Metadata extraction (title, artist, album)              │ │
│  │  - Fallback: "Unknown Song" if identification fails        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Stage 3: Stem Separation (NEW)                            │ │
│  │  - Demucs mdx_extra model                                  │ │
│  │  - Output: bass.wav, piano.wav, guitar.wav, drums.wav,     │ │
│  │    vocals.wav                                               │ │
│  │  - Store stems in S3: audio/{jobId}/stems/                 │ │
│  │  → Status: PROCESSING_STEMS                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Stage 4: Transcription Mode Selection (NEW)               │ │
│  │  - Present options: bass-only, bass+piano, bass+guitar,    │ │
│  │    all                                                      │ │
│  │  - Wait for user selection (5 min timeout)                 │ │
│  │  - Default: bass-only                                       │ │
│  │  → Status: PENDING_MODE_SELECTION                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Stage 5: Multi-Stem Transcription (NEW)                  │ │
│  │  - Bass: 8th note quantization (UPDATED from 16th)        │ │
│  │  - Piano: 8th note quantization (if selected)             │ │
│  │  - Guitar: 8th note quantization (if selected)            │ │
│  │  - Basic Pitch for note transcription                     │ │
│  │  → Status: TRANSCRIBING_STEMS                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Stage 6: Lyrics Integration (NEW)                        │ │
│  │  - Fetch lyrics from Genius API                            │ │
│  │  - Parse into lines and sections                           │ │
│  │  - Align with measure boundaries                           │ │
│  │  - Fallback: Continue without lyrics if unavailable        │ │
│  │  → Status: FETCHING_LYRICS                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Stage 7: Key Detection & Confirmation (NEW)              │ │
│  │  - Analyze transcribed notes for key                       │ │
│  │  - Present detected key to user                            │ │
│  │  - Allow correction (all 24 keys available)                │ │
│  │  - Wait for confirmation (5 min timeout)                   │ │
│  │  - Default: Use detected key                               │ │
│  │  → Status: PENDING_KEY_CONFIRMATION                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Stage 8: Nashville Number Generation (v2.0)               │ │
│  │  - Convert notes to NNS based on confirmed key             │ │
│  │  - Group by measures                                        │ │
│  │  - Store in DynamoDB                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Lambda (PDF Generator)                          │
│  - Generate PDF with NNS chart                                   │
│  - Include song metadata                                         │
│  - Include lyrics overlay (if available)                         │
│  - Upload to S3                                                  │
│  → Status: COMPLETED                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## State Machine

### Job Processing States

```
PENDING (initial)
    ↓
PROCESSING (audio analysis)
    ↓
PENDING_DOWNBEAT_CONFIRMATION (v2.0 existing)
    ↓ (user confirms or timeout)
PROCESSING_STEMS (stem separation)
    ↓
PENDING_MODE_SELECTION (NEW - user selects transcription mode)
    ↓ (user selects or timeout → bass-only)
TRANSCRIBING_STEMS (multi-stem transcription)
    ↓
FETCHING_LYRICS (optional, non-blocking)
    ↓
PENDING_KEY_CONFIRMATION (NEW - user confirms key)
    ↓ (user confirms or timeout → use detected)
PROCESSING (NNS generation)
    ↓
GENERATING_PDF
    ↓
COMPLETED
```

### State Transitions

| From State | Event | To State | Notes |
|------------|-------|----------|-------|
| PENDING | ECS task starts | PROCESSING | Initial audio analysis |
| PROCESSING | Tempo detected | PENDING_DOWNBEAT_CONFIRMATION | v2.0 existing |
| PENDING_DOWNBEAT_CONFIRMATION | User confirms | PROCESSING_STEMS | Continue to stem separation |
| PENDING_DOWNBEAT_CONFIRMATION | Timeout (5 min) | PROCESSING_STEMS | Use detected downbeat |
| PROCESSING_STEMS | Stems separated | PENDING_MODE_SELECTION | Present mode options |
| PENDING_MODE_SELECTION | User selects mode | TRANSCRIBING_STEMS | Begin transcription |
| PENDING_MODE_SELECTION | Timeout (5 min) | TRANSCRIBING_STEMS | Default to bass-only |
| TRANSCRIBING_STEMS | Transcription complete | FETCHING_LYRICS | Parallel with key detection |
| FETCHING_LYRICS | Lyrics fetched/failed | PENDING_KEY_CONFIRMATION | Non-blocking |
| TRANSCRIBING_STEMS | Key detected | PENDING_KEY_CONFIRMATION | Present detected key |
| PENDING_KEY_CONFIRMATION | User confirms | PROCESSING | Generate NNS |
| PENDING_KEY_CONFIRMATION | Timeout (5 min) | PROCESSING | Use detected key |
| PROCESSING | NNS generated | GENERATING_PDF | Trigger PDF Lambda |
| GENERATING_PDF | PDF uploaded | COMPLETED | Job complete |
| ANY | Error | FAILED | With error message |

---

## Data Models

### DynamoDB Schema Extensions

**Table**: `ChordScout-Jobs-V2-dev`

**Existing Fields** (v2.0):
```json
{
  "jobId": "string (PK)",
  "status": "string",
  "progress": "number",
  "filename": "string",
  "audioKey": "string",
  "createdAt": "string (ISO 8601)",
  "updatedAt": "string (ISO 8601)",
  "tempo": "number",
  "timeSignature": "string",
  "firstDownbeat": "number",
  "bassData": {
    "notes": "array",
    "key": "string",
    "mode": "string",
    "relativeMajor": "string",
    "measures": "array"
  },
  "pdfUrl": "string"
}
```

**NEW Fields** (v3.0):
```json
{
  "transcriptionMode": "string",  // "bass-only" | "bass+piano" | "bass+guitar" | "all"
  "detectedKey": "string",        // e.g., "C major", "A minor"
  "confirmedKey": "string",       // User-confirmed or timeout-defaulted key
  "keyConfidence": "number",      // 0.0 to 1.0
  
  "songMetadata": {
    "title": "string",
    "artist": "string",
    "album": "string",
    "year": "number",
    "identificationMethod": "string"  // "fingerprint" | "manual" | "unknown"
  },
  
  "lyrics": {
    "available": "boolean",
    "source": "string",           // "genius" | null
    "sections": [
      {
        "type": "string",         // "verse" | "chorus" | "bridge" | "intro" | "outro"
        "lines": ["string"],
        "startMeasure": "number",
        "endMeasure": "number"
      }
    ]
  },
  
  "stemData": {
    "piano": {
      "s3Key": "string",          // S3 path to piano.wav
      "notes": [
        {
          "pitch": "number",
          "start": "number",
          "end": "number",
          "velocity": "number",
          "nns": "string",
          "measure": "number"
        }
      ],
      "totalNotes": "number"
    },
    "guitar": {
      "s3Key": "string",
      "notes": "array",           // Same structure as piano
      "totalNotes": "number"
    }
  },
  
  "processingMetrics": {
    "stemSeparationTime": "number",     // seconds
    "transcriptionTime": "number",
    "lyricsFetchTime": "number",
    "totalProcessingTime": "number"
  }
}
```

### S3 Structure

**Existing** (v2.0):
```
audio/
  {jobId}/
    original.m4a          # Uploaded audio file
```

**NEW** (v3.0):
```
audio/
  {jobId}/
    original.m4a          # Uploaded audio file
    stems/                # NEW directory
      bass.wav
      piano.wav
      guitar.wav
      drums.wav
      vocals.wav
```

**PDFs** (unchanged):
```
pdfs/
  {jobId}.pdf
```

---

## Component Interfaces

### 1. Stem Transcription Module

**File**: `backend/functions-v2/chord-detector-ecs/stem_transcription.py`

**Purpose**: Transcribe piano and guitar stems using Basic Pitch


**Interface**:
```python
def transcribe_stem(
    stem_audio: np.ndarray,
    sr: int,
    stem_type: str,  # "piano" | "guitar"
    tempo: float,
    time_signature: str,
    first_downbeat: float
) -> Dict:
    """
    Transcribe a single stem to MIDI notes with 8th note quantization
    
    Args:
        stem_audio: Audio data (numpy array)
        sr: Sample rate (22050 Hz)
        stem_type: Type of stem being transcribed
        tempo: BPM
        time_signature: e.g., "4/4"
        first_downbeat: Time of first downbeat in seconds
    
    Returns:
        {
            'notes': [
                {
                    'pitch': int,           # MIDI note number (0-127)
                    'start': float,         # Original start time (seconds)
                    'end': float,           # Original end time (seconds)
                    'quantized_start': float,  # Quantized to 8th note grid
                    'velocity': float,      # 0.0 to 1.0
                    'note_name': str,       # e.g., "C4", "F#3"
                    'measure': int,
                    'beat': float,
                    'subdivision': int      # 1=downbeat, 2=upbeat
                }
            ],
            'totalNotes': int,
            'duration': float,
            'quantizationResolution': '8th'
        }
    """
```

**Key Implementation Details**:
- Uses Basic Pitch with 8th note minimum length (not 16th)
- Frequency range constraints:
  - Piano: 27.5 Hz (A0) to 4186 Hz (C8)
  - Guitar: 82 Hz (E2) to 1318 Hz (E6)
- Polyphonic transcription (multiple simultaneous notes)
- Quantization to 8th note grid (same as bass in v3.0)

---

### 2. Song Metadata and Lyrics Module

**File**: `backend/functions-v2/chord-detector-ecs/song_metadata_lyrics.py`

**Purpose**: Identify songs and fetch lyrics from Genius API

**Interface**:
```python
def identify_song(audio_path: str) -> Dict:
    """
    Identify song from audio file using metadata tags
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        {
            'title': str,
            'artist': str,
            'album': str,
            'year': int,
            'identificationMethod': 'fingerprint' | 'metadata' | 'unknown'
        }
    """

def fetch_lyrics(song_title: str, artist: str, genius_token: str) -> Dict:
    """
    Fetch lyrics from Genius API
    
    Args:
        song_title: Song title
        artist: Artist name
        genius_token: Genius API access token
    
    Returns:
        {
            'available': bool,
            'source': 'genius' | null,
            'rawLyrics': str,
            'sections': [
                {
                    'type': 'verse' | 'chorus' | 'bridge' | 'intro' | 'outro',
                    'lines': [str]
                }
            ]
        }
    """
```


def align_lyrics_to_measures(
    lyrics_sections: List[Dict],
    total_measures: int,
    song_structure: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    Align lyrics sections to measure boundaries
    
    Args:
        lyrics_sections: Parsed lyrics sections
        total_measures: Total number of measures in song
        song_structure: Optional structural analysis (verse/chorus detection)
    
    Returns:
        [
            {
                'type': str,
                'lines': [str],
                'startMeasure': int,
                'endMeasure': int
            }
        ]
    """
```

**Implementation Notes**:
- Uses `mutagen` library for audio metadata extraction
- Genius API requires `GENIUS_ACCESS_TOKEN` environment variable
- Lyrics parsing uses regex to detect section markers: [Verse], [Chorus], etc.
- Fallback: If identification fails, use filename or "Unknown Song"
- Timeout: 30 seconds for song identification, 10 seconds for lyrics fetch

---

### 3. Bass Note Transcription Module (UPDATED)

**File**: `backend/functions-v2/chord-detector-ecs/bass_note_transcription.py`

**Changes from v2.0**:
- Quantization resolution changed from 16th notes to 8th notes
- Update `quantize_notes()` function to use 8th note grid
- Update `quantizationResolution` field in output

**Updated Function**:
```python
def quantize_notes(notes: List[Dict], tempo: float, time_signature: str, 
                   first_downbeat: float) -> List[Dict]:
    """
    Quantize note start times to 8th note grid (UPDATED from 16th)
    
    Args:
        notes: List of detected notes
        tempo: BPM
        time_signature: e.g., "4/4"
        first_downbeat: Time of first downbeat
    
    Returns:
        List of notes with quantized timing and measure/beat info
    """
    beats_per_measure = int(time_signature.split('/')[0])
    beat_duration = 60.0 / tempo
    eighth_duration = beat_duration / 2  # CHANGED from /4 (16th)
    
    quantized = []
    for note in notes:
        time_from_downbeat = note['start'] - first_downbeat
        
        # Quantize to nearest 8th note (CHANGED from 16th)
        eighth_index = round(time_from_downbeat / eighth_duration)
        quantized_time = first_downbeat + (eighth_index * eighth_duration)
        
        # Calculate measure and beat
        beats_from_downbeat = eighth_index / 2
        measure = int(beats_from_downbeat / beats_per_measure) + 1
        beat_in_measure = (beats_from_downbeat % beats_per_measure) + 1
        subdivision = (eighth_index % 2) + 1
        
        quantized.append({
            **note,
            'quantized_start': quantized_time,
            'measure': measure,
            'beat': beat_in_measure,
            'subdivision': subdivision,
            'eighth_index': eighth_index,
            'quantization_resolution': '8th'  # CHANGED from '16th'
        })
    
    return quantized
```

---

### 4. ECS Task Orchestrator (MAJOR UPDATE)

**File**: `bass-transcription-pipeline/bass-transcription-ecs/app.py`

**Purpose**: Main orchestration logic for multi-stage processing


**Updated Main Flow**:
```python
def main():
    """Main entry point for v3.0 bass transcription ECS task"""
    job_id = os.environ.get('JOB_ID')
    bucket = os.environ.get('AUDIO_BUCKET')
    key = os.environ.get('AUDIO_KEY')
    
    try:
        # Stage 1: Download and analyze audio (v2.0 existing)
        update_job_status(job_id, 'PROCESSING', 20, "Analyzing audio...")
        audio_path = download_audio(bucket, key, job_id)
        tempo, time_signature, beats = detect_tempo_and_beats(audio_path)
        
        # Stage 2: Downbeat detection and confirmation (v2.0 existing)
        update_job_status(job_id, 'PROCESSING', 30, "Detecting downbeat...")
        first_downbeat = detect_downbeat(audio_path, tempo, beats)
        
        # Wait for downbeat confirmation (v2.0 existing)
        update_job_status(job_id, 'PENDING_DOWNBEAT_CONFIRMATION', 30)
        first_downbeat = wait_for_downbeat_confirmation(job_id, first_downbeat, timeout=300)
        
        # Stage 3: Song identification (NEW)
        update_job_status(job_id, 'PROCESSING', 35, "Identifying song...")
        song_metadata = identify_song(audio_path)
        update_job_with_metadata(job_id, song_metadata)
        
        # Stage 4: Stem separation (NEW)
        update_job_status(job_id, 'PROCESSING_STEMS', 40, "Separating audio stems...")
        stems = separate_stems(audio_path, job_id, bucket)
        upload_stems_to_s3(stems, job_id, bucket)
        
        # Stage 5: Transcription mode selection (NEW)
        update_job_status(job_id, 'PENDING_MODE_SELECTION', 45)
        transcription_mode = wait_for_mode_selection(job_id, timeout=300)
        
        # Stage 6: Multi-stem transcription (NEW)
        update_job_status(job_id, 'TRANSCRIBING_STEMS', 50, "Transcribing stems...")
        transcription_data = transcribe_stems(
            stems, 
            transcription_mode, 
            tempo, 
            time_signature, 
            first_downbeat
        )
        
        # Stage 7: Lyrics fetching (NEW, parallel with key detection)
        update_job_status(job_id, 'FETCHING_LYRICS', 70, "Fetching lyrics...")
        lyrics = fetch_lyrics_async(song_metadata['title'], song_metadata['artist'])
        
        # Stage 8: Key detection and confirmation (NEW)
        update_job_status(job_id, 'PROCESSING', 75, "Detecting key...")
        detected_key = detect_key_from_transcription(transcription_data)
        update_job_status(job_id, 'PENDING_KEY_CONFIRMATION', 75)
        confirmed_key = wait_for_key_confirmation(job_id, detected_key, timeout=300)
        
        # Stage 9: Nashville number generation (v2.0 existing, enhanced)
        update_job_status(job_id, 'PROCESSING', 85, "Generating Nashville numbers...")
        nns_data = generate_nashville_numbers(transcription_data, confirmed_key)
        
        # Stage 10: Align lyrics to measures (NEW)
        if lyrics['available']:
            lyrics_aligned = align_lyrics_to_measures(
                lyrics['sections'], 
                nns_data['totalMeasures']
            )
            update_job_with_lyrics(job_id, lyrics_aligned)
        
        # Stage 11: Update job with all data
        update_job_with_transcription_data(job_id, nns_data, transcription_data)
        
        # Stage 12: Trigger PDF generation (v2.0 existing)
        update_job_status(job_id, 'GENERATING_PDF', 90, "Generating PDF...")
        trigger_pdf_generation(job_id)
        
    except Exception as e:
        log_error(e)
        update_job_status(job_id, 'FAILED', 0, str(e))
        raise
```


**New Helper Functions**:
```python
def wait_for_mode_selection(job_id: str, timeout: int = 300) -> str:
    """
    Wait for user to select transcription mode
    
    Args:
        job_id: Job identifier
        timeout: Timeout in seconds (default 5 minutes)
    
    Returns:
        Selected mode: "bass-only" | "bass+piano" | "bass+guitar" | "all"
        Defaults to "bass-only" on timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        job = get_job_from_dynamodb(job_id)
        if job.get('transcriptionMode'):
            return job['transcriptionMode']
        time.sleep(2)  # Poll every 2 seconds
    
    # Timeout: default to bass-only
    update_job_field(job_id, 'transcriptionMode', 'bass-only')
    return 'bass-only'

def wait_for_key_confirmation(job_id: str, detected_key: str, timeout: int = 300) -> str:
    """
    Wait for user to confirm or correct the detected key
    
    Args:
        job_id: Job identifier
        detected_key: Automatically detected key
        timeout: Timeout in seconds (default 5 minutes)
    
    Returns:
        Confirmed key (user-selected or detected if timeout)
    """
    # Store detected key
    update_job_field(job_id, 'detectedKey', detected_key)
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        job = get_job_from_dynamodb(job_id)
        if job.get('confirmedKey'):
            return job['confirmedKey']
        time.sleep(2)
    
    # Timeout: use detected key
    update_job_field(job_id, 'confirmedKey', detected_key)
    return detected_key

def transcribe_stems(
    stems: Dict[str, np.ndarray],
    mode: str,
    tempo: float,
    time_signature: str,
    first_downbeat: float
) -> Dict:
    """
    Transcribe selected stems based on mode
    
    Args:
        stems: Dictionary of stem audio data
        mode: Transcription mode
        tempo, time_signature, first_downbeat: Musical parameters
    
    Returns:
        {
            'bass': {...},
            'piano': {...} or None,
            'guitar': {...} or None
        }
    """
    from stem_transcription import transcribe_stem
    from bass_note_transcription import detect_bass_notes
    
    result = {}
    
    # Always transcribe bass
    result['bass'] = detect_bass_notes(
        stems['bass'], 22050, tempo, time_signature, first_downbeat
    )
    
    # Transcribe piano if requested
    if mode in ['bass+piano', 'all']:
        result['piano'] = transcribe_stem(
            stems['piano'], 22050, 'piano', tempo, time_signature, first_downbeat
        )
    
    # Transcribe guitar if requested
    if mode in ['bass+guitar', 'all']:
        result['guitar'] = transcribe_stem(
            stems['guitar'], 22050, 'guitar', tempo, time_signature, first_downbeat
        )
    
    return result
```

---

## API Contracts

### 1. User Confirmation Endpoints (NEW)

**Endpoint**: `POST /jobs/{jobId}/confirm-mode`

**Purpose**: User selects transcription mode

**Request**:
```json
{
  "transcriptionMode": "bass-only" | "bass+piano" | "bass+guitar" | "all"
}
```

**Response**:
```json
{
  "success": true,
  "jobId": "string",
  "transcriptionMode": "string",
  "message": "Transcription mode confirmed"
}
```

---

**Endpoint**: `POST /jobs/{jobId}/confirm-key`

**Purpose**: User confirms or corrects detected key

**Request**:
```json
{
  "confirmedKey": "string"  // e.g., "C major", "A minor"
}
```

**Response**:
```json
{
  "success": true,
  "jobId": "string",
  "detectedKey": "string",
  "confirmedKey": "string",
  "message": "Key confirmed"
}
```

---

### 2. Job Status Response (EXTENDED)

**Endpoint**: `GET /jobs/{jobId}` (existing, extended)

**Response** (v3.0 additions highlighted):
```json
{
  "jobId": "string",
  "status": "string",
  "progress": "number",
  "statusMessage": "string",
  "filename": "string",
  "createdAt": "string",
  "updatedAt": "string",
  
  // NEW v3.0 fields
  "transcriptionMode": "string",
  "detectedKey": "string",
  "confirmedKey": "string",
  "keyConfidence": "number",
  
  "songMetadata": {
    "title": "string",
    "artist": "string",
    "album": "string",
    "year": "number"
  },
  
  "lyrics": {
    "available": "boolean",
    "sections": [...]
  },
  
  "stemData": {
    "piano": {...},
    "guitar": {...}
  },
  
  // Existing v2.0 fields
  "bassData": {...},
  "pdfUrl": "string"
}
```

---

## Frontend Integration

### TypeScript Type Updates

**File**: `src/services/transcriptionService.ts`


**Updated Types**:
```typescript
export interface TranscriptionJob {
  id: string;
  filename?: string;
  title: string;
  status: 'PENDING' | 'UPLOADING' | 'PROCESSING' | 
          'PENDING_DOWNBEAT_CONFIRMATION' |
          'PROCESSING_STEMS' |              // NEW
          'PENDING_MODE_SELECTION' |        // NEW
          'TRANSCRIBING_STEMS' |            // NEW
          'FETCHING_LYRICS' |               // NEW
          'PENDING_KEY_CONFIRMATION' |      // NEW
          'GENERATING_PDF' |
          'COMPLETED' | 'FAILED';
  currentStep?: string;
  progress?: number;
  statusMessage?: string;
  createdAt: string;
  updatedAt?: string;
  completedAt?: string;
  
  // NEW v3.0 fields
  transcriptionMode?: 'bass-only' | 'bass+piano' | 'bass+guitar' | 'all';
  detectedKey?: string;
  confirmedKey?: string;
  keyConfidence?: number;
  
  songMetadata?: {
    title: string;
    artist: string;
    album?: string;
    year?: number;
  };
  
  lyrics?: {
    available: boolean;
    sections: Array<{
      type: string;
      lines: string[];
      startMeasure: number;
      endMeasure: number;
    }>;
  };
  
  stemData?: {
    piano?: StemTranscription;
    guitar?: StemTranscription;
  };
  
  // Existing v2.0 fields
  chordsData?: any;
  bassData?: any;
  pdfUrl?: string;
  errorMessage?: string;
}

interface StemTranscription {
  notes: Array<{
    pitch: number;
    start: number;
    end: number;
    velocity: number;
    nns: string;
    measure: number;
  }>;
  totalNotes: number;
}
```

**New API Functions**:
```typescript
export async function confirmTranscriptionMode(
  jobId: string,
  mode: 'bass-only' | 'bass+piano' | 'bass+guitar' | 'all'
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/confirm-mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcriptionMode: mode })
  });
  
  if (!response.ok) {
    throw new Error('Failed to confirm transcription mode');
  }
}

export async function confirmKey(
  jobId: string,
  key: string
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/confirm-key`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ confirmedKey: key })
  });
  
  if (!response.ok) {
    throw new Error('Failed to confirm key');
  }
}
```

---

### UI Components (NEW)

**Component**: `src/components/TranscriptionModeSelector.tsx`

**Purpose**: Allow user to select which stems to transcribe

```typescript
interface TranscriptionModeSelectorProps {
  jobId: string;
  onModeSelected: (mode: string) => void;
}

export function TranscriptionModeSelector({ jobId, onModeSelected }: TranscriptionModeSelectorProps) {
  const [selectedMode, setSelectedMode] = useState<string>('bass-only');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const modes = [
    {
      value: 'bass-only',
      label: 'Bass Only',
      description: 'Fastest processing (~3 min)',
      icon: '🎸'
    },
    {
      value: 'bass+piano',
      label: 'Bass + Piano',
      description: 'Enhanced chord detection (~5 min)',
      icon: '🎹'
    },
    {
      value: 'bass+guitar',
      label: 'Bass + Guitar',
      description: 'Full harmonic context (~5 min)',
      icon: '🎸'
    },
    {
      value: 'all',
      label: 'All Instruments',
      description: 'Complete transcription (~8 min)',
      icon: '🎵'
    }
  ];
  
  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await confirmTranscriptionMode(jobId, selectedMode);
      onModeSelected(selectedMode);
    } catch (error) {
      console.error('Failed to confirm mode:', error);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="mode-selector">
      <h3>Select Transcription Mode</h3>
      <p>Choose which instruments to transcribe for enhanced accuracy:</p>
      
      <div className="mode-options">
        {modes.map(mode => (
          <button
            key={mode.value}
            className={`mode-option ${selectedMode === mode.value ? 'selected' : ''}`}
            onClick={() => setSelectedMode(mode.value)}
          >
            <span className="icon">{mode.icon}</span>
            <span className="label">{mode.label}</span>
            <span className="description">{mode.description}</span>
          </button>
        ))}
      </div>
      
      <button 
        onClick={handleSubmit} 
        disabled={isSubmitting}
        className="confirm-button"
      >
        {isSubmitting ? 'Confirming...' : 'Confirm Selection'}
      </button>
      
      <p className="timeout-notice">
        Auto-selects "Bass Only" in 5 minutes if no selection made
      </p>
    </div>
  );
}
```

---

**Component**: `src/components/KeyConfirmation.tsx`

**Purpose**: Allow user to confirm or correct detected key

```typescript
interface KeyConfirmationProps {
  jobId: string;
  detectedKey: string;
  keyConfidence: number;
  onKeyConfirmed: (key: string) => void;
}

export function KeyConfirmation({ 
  jobId, 
  detectedKey, 
  keyConfidence, 
  onKeyConfirmed 
}: KeyConfirmationProps) {
  const [selectedKey, setSelectedKey] = useState<string>(detectedKey);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const allKeys = [
    'C major', 'G major', 'D major', 'A major', 'E major', 'B major',
    'F# major', 'Db major', 'Ab major', 'Eb major', 'Bb major', 'F major',
    'A minor', 'E minor', 'B minor', 'F# minor', 'C# minor', 'G# minor',
    'Eb minor', 'Bb minor', 'F minor', 'C minor', 'G minor', 'D minor'
  ];
  
  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await confirmKey(jobId, selectedKey);
      onKeyConfirmed(selectedKey);
    } catch (error) {
      console.error('Failed to confirm key:', error);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="key-confirmation">
      <h3>Confirm Musical Key</h3>
      <div className="detected-key">
        <p>Detected Key: <strong>{detectedKey}</strong></p>
        <p>Confidence: {(keyConfidence * 100).toFixed(0)}%</p>
      </div>
      
      <p>Is this correct? Or select a different key:</p>
      
      <select 
        value={selectedKey} 
        onChange={(e) => setSelectedKey(e.target.value)}
        className="key-selector"
      >
        {allKeys.map(key => (
          <option key={key} value={key}>{key}</option>
        ))}
      </select>
      
      <button 
        onClick={handleSubmit} 
        disabled={isSubmitting}
        className="confirm-button"
      >
        {isSubmitting ? 'Confirming...' : 'Confirm Key'}
      </button>
      
      <p className="timeout-notice">
        Auto-confirms detected key in 5 minutes if no selection made
      </p>
    </div>
  );
}
```

---

### App.tsx Integration

**File**: `src/App.tsx`

**Updates**:
```typescript
function App() {
  const [currentJob, setCurrentJob] = useState<TranscriptionJob | null>(null);
  const [showModeSelector, setShowModeSelector] = useState(false);
  const [showKeyConfirmation, setShowKeyConfirmation] = useState(false);
  
  useEffect(() => {
    if (!currentJob) return;
    
    // Show mode selector when status is PENDING_MODE_SELECTION
    if (currentJob.status === 'PENDING_MODE_SELECTION') {
      setShowModeSelector(true);
    }
    
    // Show key confirmation when status is PENDING_KEY_CONFIRMATION
    if (currentJob.status === 'PENDING_KEY_CONFIRMATION') {
      setShowKeyConfirmation(true);
    }
    
    // Continue polling
    if (!['COMPLETED', 'FAILED'].includes(currentJob.status)) {
      const timer = setTimeout(() => pollJobStatus(currentJob.id), 2000);
      return () => clearTimeout(timer);
    }
  }, [currentJob]);
  
  return (
    <div className="app">
      {/* Existing upload UI */}
      
      {showModeSelector && currentJob && (
        <TranscriptionModeSelector
          jobId={currentJob.id}
          onModeSelected={() => {
            setShowModeSelector(false);
            pollJobStatus(currentJob.id);
          }}
        />
      )}
      
      {showKeyConfirmation && currentJob && (
        <KeyConfirmation
          jobId={currentJob.id}
          detectedKey={currentJob.detectedKey!}
          keyConfidence={currentJob.keyConfidence!}
          onKeyConfirmed={() => {
            setShowKeyConfirmation(false);
            pollJobStatus(currentJob.id);
          }}
        />
      )}
      
      {/* Existing results display */}
    </div>
  );
}
```

---

## Error Handling

### Error Categories and Strategies


#### 1. Stem Separation Failures

**Scenario**: Demucs fails to separate stems

**Strategy**: Graceful degradation to bass-only mode

```python
def separate_stems(audio_path: str, job_id: str, bucket: str) -> Dict:
    """Separate audio into stems with fallback"""
    try:
        stems = run_demucs_separation(audio_path)
        return stems
    except Exception as e:
        log.error(f"Stem separation failed: {e}")
        
        # Fallback: Load full mix as bass stem
        audio, sr = librosa.load(audio_path, sr=22050)
        
        # Update job to indicate fallback
        update_job_field(job_id, 'transcriptionMode', 'bass-only')
        update_job_field(job_id, 'statusMessage', 
                        'Stem separation failed, using bass-only mode')
        
        return {
            'bass': audio,
            'piano': None,
            'guitar': None,
            'drums': None,
            'vocals': None
        }
```

---

#### 2. Song Identification Failures

**Scenario**: Cannot identify song from audio

**Strategy**: Use filename or default to "Unknown Song"

```python
def identify_song(audio_path: str) -> Dict:
    """Identify song with fallback to filename"""
    try:
        # Try metadata extraction
        metadata = extract_audio_metadata(audio_path)
        if metadata['title']:
            return metadata
    except Exception as e:
        log.warning(f"Metadata extraction failed: {e}")
    
    # Fallback: Use filename
    filename = os.path.basename(audio_path)
    title = os.path.splitext(filename)[0]
    
    return {
        'title': title,
        'artist': 'Unknown Artist',
        'album': None,
        'year': None,
        'identificationMethod': 'filename'
    }
```

---

#### 3. Lyrics Fetch Failures

**Scenario**: Genius API unavailable or song not found

**Strategy**: Continue without lyrics (non-blocking)

```python
def fetch_lyrics_async(title: str, artist: str) -> Dict:
    """Fetch lyrics with graceful failure"""
    try:
        genius_token = os.environ.get('GENIUS_ACCESS_TOKEN')
        if not genius_token:
            log.warning("GENIUS_ACCESS_TOKEN not set, skipping lyrics")
            return {'available': False, 'source': None, 'sections': []}
        
        lyrics = fetch_from_genius(title, artist, genius_token, timeout=10)
        return lyrics
        
    except requests.Timeout:
        log.warning("Genius API timeout, continuing without lyrics")
        return {'available': False, 'source': None, 'sections': []}
        
    except Exception as e:
        log.error(f"Lyrics fetch failed: {e}")
        return {'available': False, 'source': None, 'sections': []}
```

---

#### 4. Key Detection Failures

**Scenario**: Cannot determine key from transcription

**Strategy**: Default to C major with low confidence

```python
def detect_key_from_transcription(transcription_data: Dict) -> Dict:
    """Detect key with fallback"""
    try:
        bass_notes = transcription_data['bass']['notes']
        if len(bass_notes) == 0:
            raise ValueError("No notes to analyze")
        
        key_info = analyze_key_from_notes(bass_notes)
        return key_info
        
    except Exception as e:
        log.warning(f"Key detection failed: {e}, defaulting to C major")
        return {
            'key': 'C major',
            'confidence': 0.0,
            'method': 'default'
        }
```

---

#### 5. Transcription Failures

**Scenario**: Basic Pitch fails to transcribe a stem

**Strategy**: Skip that stem, continue with others

```python
def transcribe_stems(stems: Dict, mode: str, ...) -> Dict:
    """Transcribe stems with individual error handling"""
    result = {}
    
    # Bass is critical - fail if it fails
    try:
        result['bass'] = detect_bass_notes(stems['bass'], ...)
    except Exception as e:
        log.error(f"Bass transcription failed: {e}")
        raise  # Critical failure
    
    # Piano is optional
    if mode in ['bass+piano', 'all'] and stems.get('piano') is not None:
        try:
            result['piano'] = transcribe_stem(stems['piano'], 'piano', ...)
        except Exception as e:
            log.warning(f"Piano transcription failed: {e}, skipping")
            result['piano'] = None
    
    # Guitar is optional
    if mode in ['bass+guitar', 'all'] and stems.get('guitar') is not None:
        try:
            result['guitar'] = transcribe_stem(stems['guitar'], 'guitar', ...)
        except Exception as e:
            log.warning(f"Guitar transcription failed: {e}, skipping")
            result['guitar'] = None
    
    return result
```

---

#### 6. Timeout Handling

**Scenario**: User doesn't respond to confirmation prompts

**Strategy**: Auto-proceed with defaults after 5 minutes

```python
def wait_for_confirmation(
    job_id: str,
    field_name: str,
    default_value: Any,
    timeout: int = 300
) -> Any:
    """Generic confirmation wait with timeout"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        job = get_job_from_dynamodb(job_id)
        if job.get(field_name):
            log.info(f"User confirmed {field_name}: {job[field_name]}")
            return job[field_name]
        time.sleep(2)
    
    # Timeout: use default
    log.warning(f"Timeout waiting for {field_name}, using default: {default_value}")
    update_job_field(job_id, field_name, default_value)
    return default_value
```

---

### Error Response Format

**DynamoDB Error Fields**:
```json
{
  "status": "FAILED",
  "errorMessage": "string",
  "errorCode": "string",
  "errorDetails": {
    "stage": "string",
    "originalError": "string",
    "timestamp": "string"
  }
}
```

**Error Codes**:
- `AUDIO_LOAD_FAILED`: Cannot load audio file
- `STEM_SEPARATION_FAILED`: Demucs failed (degraded to bass-only)
- `TRANSCRIPTION_FAILED`: Basic Pitch failed
- `KEY_DETECTION_FAILED`: Cannot determine key (defaulted to C major)
- `LYRICS_FETCH_FAILED`: Genius API failed (continued without lyrics)
- `PDF_GENERATION_FAILED`: PDF Lambda failed
- `TIMEOUT`: ECS task exceeded 15 minutes
- `UNKNOWN_ERROR`: Unexpected error

---

## Deployment Architecture

### Infrastructure Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Account                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  API Gateway                                                │ │
│  │  - /upload (POST)                                           │ │
│  │  - /jobs/{jobId} (GET)                                      │ │
│  │  - /jobs/{jobId}/confirm-mode (POST) [NEW]                 │ │
│  │  - /jobs/{jobId}/confirm-key (POST) [NEW]                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Lambda Functions                                           │ │
│  │  - upload-handler (existing)                                │ │
│  │  - job-status-handler (existing)                            │ │
│  │  - confirm-mode-handler (NEW)                               │ │
│  │  - confirm-key-handler (NEW)                                │ │
│  │  - pdf-generator (existing)                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  ECS Fargate                                                │ │
│  │  - Cluster: bass-transcription-cluster                      │ │
│  │  - Task Definition: bass-transcription-task-v3              │ │
│  │  - CPU: 4 vCPU                                              │ │
│  │  - Memory: 16 GB                                            │ │
│  │  - Timeout: 15 minutes                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  S3 Buckets                                                 │ │
│  │  - chordscout-audio-dev                                     │ │
│  │    - audio/{jobId}/original.m4a                             │ │
│  │    - audio/{jobId}/stems/*.wav [NEW]                        │ │
│  │  - chordscout-pdfs-dev                                      │ │
│  │    - {jobId}.pdf                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  DynamoDB                                                   │ │
│  │  - Table: ChordScout-Jobs-V2-dev                            │ │
│  │  - Extended schema with v3.0 fields                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Secrets Manager                                            │ │
│  │  - GENIUS_ACCESS_TOKEN [NEW]                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  CloudWatch                                                 │ │
│  │  - Logs: /ecs/bass-transcription                            │ │
│  │  - Metrics: Processing time, success rate                   │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Docker Image Updates

**File**: `bass-transcription-pipeline/bass-transcription-ecs/Dockerfile`

**Changes**:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py /app/
COPY bass_note_transcription.py /app/
COPY stem_transcription.py /app/          # NEW
COPY song_metadata_lyrics.py /app/        # NEW

# Copy existing modules
COPY simple-pipeline/chord-detection/downbeat_detection.py /app/simple-pipeline/chord-detection/

CMD ["python", "app.py"]
```

**File**: `bass-transcription-pipeline/bass-transcription-ecs/requirements.txt`

**Additions**:
```
# Existing dependencies
boto3==1.34.0
librosa==0.10.1
numpy==1.26.0
torch==2.1.0
torchaudio==2.1.0
demucs==4.0.1
basic-pitch==0.2.5

# NEW v3.0 dependencies
mutagen==1.47.0          # Audio metadata extraction
requests==2.31.0         # HTTP client for Genius API
beautifulsoup4==4.12.0   # HTML parsing for lyrics
lyricsgenius==3.0.1      # Genius API client
```

---

### Environment Variables

**ECS Task Environment**:
```bash
# Existing
JOB_ID=<job-id>
AUDIO_BUCKET=chordscout-audio-dev
AUDIO_KEY=audio/<job-id>/original.m4a
DYNAMODB_JOBS_TABLE=ChordScout-Jobs-V2-dev
PDF_GENERATOR_FUNCTION=bass-nns-pdf-generator-dev

# NEW v3.0
GENIUS_ACCESS_TOKEN=<from-secrets-manager>
ENABLE_LYRICS=true
ENABLE_MULTI_STEM=true
DEFAULT_TRANSCRIPTION_MODE=bass-only
CONFIRMATION_TIMEOUT=300
```

---

### IAM Permissions

**ECS Task Role Additions**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::chordscout-audio-dev/audio/*/stems/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:*:secret:GENIUS_ACCESS_TOKEN-*"
      ]
    }
  ]
}
```

---

## Migration Strategy

### Phase 1: Backward Compatible Deployment (Week 1)

**Goal**: Deploy v3.0 with v2.0 behavior as default

**Steps**:
1. Deploy updated ECS Docker image with new modules
2. Set `ENABLE_MULTI_STEM=false` initially
3. All jobs default to bass-only mode (v2.0 behavior)
4. Test that existing v2.0 workflows continue to work
5. Monitor for regressions

**Validation**:
- Upload test audio files
- Verify bass-only transcription works identically to v2.0
- Check PDF generation
- Confirm no breaking changes

---

### Phase 2: Enable Multi-Stem (Week 2)

**Goal**: Enable stem separation and transcription mode selection

**Steps**:
1. Set `ENABLE_MULTI_STEM=true`
2. Deploy new Lambda functions for confirmation endpoints
3. Deploy frontend updates with mode selector UI
4. Test mode selection workflow
5. Verify stem separation and transcription

**Validation**:
- Test all transcription modes
- Verify stem files uploaded to S3
- Check timeout behavior (5 min default)
- Validate piano and guitar transcription accuracy

---

### Phase 3: Enable Lyrics and Key Confirmation (Week 3)

**Goal**: Full v3.0 feature set

**Steps**:
1. Add `GENIUS_ACCESS_TOKEN` to Secrets Manager
2. Set `ENABLE_LYRICS=true`
3. Deploy key confirmation UI
4. Test end-to-end workflow with all features
5. Monitor performance and error rates

**Validation**:
- Test song identification
- Verify lyrics fetching and alignment
- Test key detection and confirmation
- Check PDF generation with lyrics
- Validate complete workflow timing

---

### Phase 4: Performance Optimization (Week 4)

**Goal**: Optimize processing time and resource usage

**Steps**:
1. Profile ECS task execution
2. Optimize stem separation (parallel processing)
3. Cache Demucs model in Docker image
4. Tune Basic Pitch parameters
5. Implement parallel lyrics fetching

**Targets**:
- Bass-only: < 3 minutes
- Bass+piano/guitar: < 5 minutes
- All stems: < 8 minutes

---

### Rollback Plan

**If critical issues arise**:

1. **Immediate**: Set `ENABLE_MULTI_STEM=false`
   - Reverts to v2.0 bass-only behavior
   - No code changes needed

2. **Frontend**: Deploy previous version
   - Remove mode selector and key confirmation UI
   - Restore v2.0 status polling

3. **Backend**: Rollback ECS task definition
   - Use previous Docker image tag
   - Restore v2.0 environment variables

4. **Database**: No rollback needed
   - v3.0 fields are additive only
   - v2.0 code ignores new fields

---

## Testing Strategy

### Unit Tests

**New Test Files**:
- `test_stem_transcription.py`
- `test_song_metadata_lyrics.py`
- `test_key_detection.py`
- `test_quantization_8th_notes.py`

**Example Test**:
```python
def test_8th_note_quantization():
    """Verify 8th note quantization is idempotent"""
    notes = [
        {'pitch': 40, 'start': 0.125, 'end': 0.5},
        {'pitch': 43, 'start': 0.625, 'end': 1.0}
    ]
    
    # Quantize once
    quantized_once = quantize_notes(notes, tempo=120, time_signature='4/4', first_downbeat=0.0)
    
    # Quantize again
    quantized_twice = quantize_notes(quantized_once, tempo=120, time_signature='4/4', first_downbeat=0.0)
    
    # Should be identical (idempotence)
    assert quantized_once == quantized_twice
    
    # All notes should be on 8th note grid
    for note in quantized_once:
        assert note['quantization_resolution'] == '8th'
```

---

### Integration Tests

**Test Scenarios**:
1. Complete v2.0 workflow (bass-only, no confirmations)
2. Mode selection with timeout
3. Key confirmation with timeout
4. Lyrics fetching success and failure
5. Stem separation failure fallback
6. Multi-stem transcription (all modes)

---

### Performance Tests

**Metrics to Track**:
- Stem separation time
- Transcription time per stem
- Total processing time by mode
- Memory usage
- CPU utilization

**Targets**:
- Bass-only: 2-3 minutes for 4-minute song
- Bass+piano: 4-5 minutes
- All stems: 7-8 minutes

---

## Monitoring and Observability

### CloudWatch Metrics

**Custom Metrics**:
- `TranscriptionMode` (dimension: mode)
- `ProcessingTime` (dimension: stage)
- `StemSeparationSuccess` (boolean)
- `LyricsFetchSuccess` (boolean)
- `KeyDetectionConfidence` (value)
- `UserConfirmationTimeout` (count)

### CloudWatch Logs

**Structured Logging**:
```python
log.info("Stage completed", extra={
    'jobId': job_id,
    'stage': 'stem_separation',
    'duration': elapsed_time,
    'success': True,
    'transcriptionMode': mode
})
```

### Alarms

**Critical Alarms**:
- ECS task failure rate > 5%
- Processing time > 15 minutes (timeout)
- Stem separation failure rate > 10%
- DynamoDB throttling

---

## Open Questions

1. **Genius API Rate Limits**: What are the rate limits? Need caching strategy?
2. **Stem Storage Retention**: How long to keep stem files in S3? (Recommend 7 days)
3. **Harmonic Context Usage**: How to use piano/guitar transcriptions for chord detection improvement?
4. **Key Detection Algorithm**: Should we use weighted analysis from multiple stems?
5. **Lyrics Alignment Accuracy**: How to improve measure alignment without timing data?

---

## Future Enhancements (Out of Scope for v3.0)

- Real-time progress updates via WebSocket
- Chord detection using multi-stem harmonic analysis
- Melody transcription from vocals stem
- Drum pattern transcription
- Interactive stem playback in UI
- Export to MIDI format
- Collaborative editing of transcriptions
- Mobile app support

---

## Success Criteria

v3.0 will be considered successful when:

1. **Accuracy**: 8th note quantization reduces false positives by 30%
2. **Features**: All 4 transcription modes work reliably
3. **Metadata**: 80%+ songs correctly identified
4. **Lyrics**: 70%+ songs have lyrics in PDF
5. **Performance**: Processing times within targets
6. **Reliability**: < 5% failure rate
7. **Compatibility**: Zero breaking changes to v2.0 API
8. **User Experience**: Confirmation workflows complete in < 1 minute

---

## Appendix: Sequence Diagrams

### Complete v3.0 Processing Flow

```
User          Frontend       API Gateway    Lambda         ECS Task       DynamoDB       S3           Genius API
 │                │              │             │              │              │            │              │
 │─Upload Audio──>│              │             │              │              │            │              │
 │                │─POST /upload─>│            │              │              │            │              │
 │                │              │─invoke──────>│             │              │            │              │
 │                │              │             │─create job──>│              │            │              │
 │                │              │             │              │              │─store─────>│              │
 │                │<─jobId + URL─│<────────────│              │              │            │              │
 │                │─PUT audio────────────────────────────────────────────────>│              │
 │                │              │             │              │              │            │              │
 │                │              │             │─start ECS───>│              │            │              │
 │                │              │             │              │─download─────────────────>│              │
 │                │              │             │              │─analyze audio│            │              │
 │                │              │             │              │─detect tempo─│            │              │
 │                │              │             │              │─detect downbeat           │              │
 │                │              │             │              │─update status>│            │              │
 │                │─poll status──>│            │              │              │            │              │
 │<─PENDING_DOWNBEAT_CONFIRMATION─│            │              │              │            │              │
 │                │              │             │              │              │            │              │
 │─confirm────────>│              │             │              │              │            │              │
 │                │─POST confirm─>│            │              │              │            │              │
 │                │              │─update──────────────────────────────────>│            │              │
 │                │              │             │              │─continue─────│            │              │
 │                │              │             │              │─identify song│            │              │
 │                │              │             │              │─separate stems            │              │
 │                │              │             │              │─upload stems─────────────>│              │
 │                │              │             │              │─update status>│            │              │
 │                │─poll status──>│            │              │              │            │              │
 │<─PENDING_MODE_SELECTION────────│            │              │              │            │              │
 │                │              │             │              │              │            │              │
 │─select mode────>│              │             │              │              │            │              │
 │                │─POST mode────>│            │              │              │            │              │
 │                │              │─update──────────────────────────────────>│            │              │
 │                │              │             │              │─transcribe───│            │              │
 │                │              │             │              │─fetch lyrics─────────────────────────────>│
 │                │              │             │              │<─lyrics──────────────────────────────────│
 │                │              │             │              │─detect key───│            │              │
 │                │              │             │              │─update status>│            │              │
 │                │─poll status──>│            │              │              │            │              │
 │<─PENDING_KEY_CONFIRMATION──────│            │              │              │            │              │
 │                │              │             │              │              │            │              │
 │─confirm key────>│              │             │              │              │            │              │
 │                │─POST key─────>│            │              │              │            │              │
 │                │              │─update──────────────────────────────────>│            │              │
 │                │              │             │              │─generate NNS─│            │              │
 │                │              │             │              │─update data──>│            │              │
 │                │              │             │              │─invoke PDF Lambda         │              │
 │                │              │             │<─────────────│              │            │              │
 │                │              │             │─generate PDF─│              │            │              │
 │                │              │             │─upload PDF───────────────────────────────>│              │
 │                │              │             │─update status────────────────>│            │              │
 │                │─poll status──>│            │              │              │            │              │
 │<─COMPLETED─────────────────────│            │              │              │            │              │
 │                │              │             │              │              │            │              │
```

---

**End of Design Document**
