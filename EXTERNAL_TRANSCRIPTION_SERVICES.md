# External Music Transcription Services Integration Plan

**Date:** February 5, 2026  
**Goal:** Use specialized AI services for accurate chord/MIDI transcription

---

## Problem

Current chord detection (librosa + essentia) is not accurate enough:
- Wrong chords detected
- Wrong key detection
- Missing minor chords
- Too many or too few chords

**Solution:** Use specialized services that have trained on millions of songs.

---

## Recommended Services

### 1. **Klangio / Melody Scanner** ⭐ RECOMMENDED

**Website:** https://www.klangio.com  
**API:** Available  
**Pricing:** Pay-per-use or subscription

**Features:**
- Upload audio (MP3, WAV, YouTube links)
- Get sheet music, MIDI, or MusicXML
- Instrument-specific variants (piano, guitar, vocals, drums)
- Polyphonic transcription
- Chord detection
- Key detection

**Output Formats:**
- MIDI
- MusicXML
- PDF sheet music
- Chord symbols

**Why Recommended:**
- ✅ Handles YouTube links directly
- ✅ Multiple output formats
- ✅ Good accuracy
- ✅ Reasonable pricing
- ✅ API available

**Integration:**
```python
import requests

def transcribe_with_klangio(youtube_url):
    response = requests.post(
        'https://api.klangio.com/v1/transcribe',
        json={
            'url': youtube_url,
            'output_format': 'musicxml'
        },
        headers={'Authorization': f'Bearer {API_KEY}'}
    )
    return response.json()
```

---

### 2. **Songscription** ⭐ GOOD ALTERNATIVE

**Website:** https://songscription.com  
**Type:** Browser-based AI platform  
**Status:** Expanding support

**Features:**
- Audio to notation
- Tabs generation
- MIDI export
- Single instruments (expanding)
- Browser-based processing

**Pros:**
- Modern AI approach
- Clean interface
- Growing feature set

**Cons:**
- Limited to single instruments currently
- May not have API yet

---

### 3. **Ivory (Piano Specialist)**

**Focus:** Piano audio → piano sheet music/MIDI  
**Best for:** Piano-heavy songs

**Features:**
- Specialized for piano
- High accuracy for piano parts
- MIDI output
- Sheet music generation

**Use case:** If song is piano-based, use Ivory for best results

---

### 4. **ScoreCloud**

**Website:** https://scorecloud.com  
**Features:**
- Music notation software
- Audio capture
- Polyphonic transcription
- Sheet music creation

**Pros:**
- Established product
- Good polyphonic support
- Multiple instruments

**Cons:**
- May require desktop app
- Pricing model unclear

---

## Recommended Approach: Hybrid Pipeline

### Phase 1: Use Klangio for Transcription

```
YouTube URL
    ↓
Download Audio (existing)
    ↓
Send to Klangio API
    ↓
Get MusicXML/MIDI
    ↓
Parse chords + key
    ↓
Convert to NNS
    ↓
Combine with lyrics (existing)
    ↓
Generate PDF
```

### Phase 2: Parse MusicXML to Extract Data

**MusicXML contains:**
- Chord symbols
- Key signature
- Time signature
- Tempo
- Measures
- Notes (for MIDI)

**Parse to get:**
```python
{
  'key': 'F major',
  'tempo': 76,
  'timeSignature': '4/4',
  'chords': [
    {'chord': 'F', 'measure': 1, 'beat': 1},
    {'chord': 'Dm', 'measure': 2, 'beat': 1},
    {'chord': 'Gm', 'measure': 3, 'beat': 1},
    {'chord': 'C', 'measure': 4, 'beat': 1}
  ]
}
```

### Phase 3: Convert to NNS

Use our existing `convert_chord_to_nashville()` function:
```python
for chord in chords:
    chord['nns'] = convert_chord_to_nashville(
        chord['chord'], 
        key=detected_key
    )
```

---

## Implementation Plan

### Step 1: Add Klangio Integration (2-3 hours)

**Create new Lambda function:**
```python
# backend/functions-v2/klangio-transcriber/index.py

import requests
import os

KLANGIO_API_KEY = os.environ['KLANGIO_API_KEY']

def transcribe_audio(audio_url):
    """
    Send audio to Klangio for transcription
    Returns MusicXML with chords and key
    """
    response = requests.post(
        'https://api.klangio.com/v1/transcribe',
        json={
            'url': audio_url,
            'output_format': 'musicxml',
            'include_chords': True
        },
        headers={'Authorization': f'Bearer {KLANGIO_API_KEY}'}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Klangio API error: {response.text}")
```

### Step 2: Parse MusicXML (1-2 hours)

**Use music21 library:**
```python
from music21 import converter

def parse_musicxml(musicxml_data):
    """
    Parse MusicXML to extract chords, key, tempo
    """
    score = converter.parse(musicxml_data)
    
    # Extract key
    key = score.analyze('key')
    
    # Extract tempo
    tempo = score.metronomeMarkBoundaries()[0][2].number
    
    # Extract chords
    chords = []
    for element in score.flatten().getElementsByClass('ChordSymbol'):
        chords.append({
            'chord': element.figure,
            'measure': element.measureNumber,
            'beat': element.beat,
            'offset': element.offset
        })
    
    return {
        'key': str(key),
        'tempo': tempo,
        'timeSignature': score.timeSignature.ratioString,
        'chords': chords
    }
```

### Step 3: Update Workflow (1 hour)

**Modify Step Functions workflow:**
```json
{
  "States": {
    "DownloadAudio": {...},
    "TranscribeLyrics": {...},
    "TranscribeChords": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:klangio-transcriber",
      "Next": "ParseMusicXML"
    },
    "ParseMusicXML": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:musicxml-parser",
      "Next": "ConvertToNNS"
    },
    "ConvertToNNS": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:nns-converter",
      "Next": "GeneratePDF"
    }
  }
}
```

---

## Cost Analysis

### Klangio Pricing (Estimated)

**Pay-per-use:**
- ~$0.10 - $0.50 per transcription
- Depends on song length

**Subscription:**
- ~$10-30/month for unlimited
- Better for high volume

### Comparison to Current Costs

**Current (ECS):**
- ECS task: ~$0.05 per job
- But: Inaccurate results

**With Klangio:**
- Klangio: ~$0.20 per job
- ECS (lyrics only): ~$0.02 per job
- Total: ~$0.22 per job
- But: Accurate results ✅

**ROI:** Worth the extra $0.17 for accuracy!

---

## Alternative: MIDI-Based Approach

If services don't work well, use MIDI as intermediate:

### Option A: Basic Pitch (Spotify's Model)

**Free and open source!**

```python
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

model_output, midi_data, note_events = predict(
    audio_path,
    ICASSP_2022_MODEL_PATH
)

# Convert MIDI to chords
chords = midi_to_chords(midi_data)
```

**Pros:**
- ✅ Free
- ✅ Open source
- ✅ Good accuracy
- ✅ No API limits

**Cons:**
- Outputs MIDI (need to convert to chords)
- May need post-processing

### Option B: Omnizart

**Open source music transcription:**

```python
from omnizart.chord import app as chord_app

chords = chord_app.transcribe(audio_path)
```

**Pros:**
- ✅ Free
- ✅ Chord-specific model
- ✅ No API needed

**Cons:**
- Complex setup
- May need GPU

---

## Recommended Next Steps

### Immediate (Today)

1. **Research Klangio API**
   - Sign up for account
   - Test API with sample song
   - Check pricing
   - Verify output quality

2. **Test Basic Pitch (Free Alternative)**
   - Install locally
   - Test with sample song
   - See if MIDI → chord conversion works

### Short-term (This Week)

1. **Implement Klangio Integration**
   - Create Lambda function
   - Add MusicXML parser
   - Update workflow
   - Test end-to-end

2. **Compare Results**
   - Current system vs Klangio
   - Accuracy comparison
   - Cost analysis

### Decision Point

**If Klangio works well:**
- ✅ Use it for production
- Keep current system as fallback
- Much better accuracy

**If Klangio doesn't work:**
- Try Basic Pitch (free)
- Try Omnizart (free)
- Consider other services

---

## Fallback Strategy

Keep current system as backup:

```python
def detect_chords(audio_path):
    try:
        # Try Klangio first
        return transcribe_with_klangio(audio_path)
    except Exception as e:
        log(f"Klangio failed: {e}, using fallback")
        # Fall back to current system
        return detect_chords_librosa(audio_path)
```

**Benefits:**
- Always works (fallback available)
- Best accuracy when service works
- Graceful degradation

---

## Summary

**Problem:** Current chord detection not accurate enough

**Solution:** Use specialized services (Klangio recommended)

**Benefits:**
- ✅ Much better accuracy
- ✅ Trained on millions of songs
- ✅ Multiple output formats
- ✅ Reasonable cost (~$0.20/job)

**Next Steps:**
1. Test Klangio API
2. Test Basic Pitch (free alternative)
3. Implement integration
4. Compare results

**Timeline:** 4-6 hours to implement and test

---

**Let's test Klangio first and see if it solves the accuracy problem!**
