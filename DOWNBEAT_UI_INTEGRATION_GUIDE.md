# Downbeat Confirmation UI Integration Guide

## Overview

Created a clean React component for downbeat confirmation that provides:
- Visual waveform with beat markers
- Audio playback with click track
- Interactive downbeat adjustment
- Time signature selection
- Professional, user-friendly interface

---

## Component Created

**File**: `src/components/DownbeatConfirmation.tsx`

**Features**:
- ✅ Waveform visualization with beat markers
- ✅ Red lines for downbeats (loud clicks)
- ✅ Blue lines for regular beats (soft clicks)
- ✅ Play/pause audio with click track
- ✅ Previous/next beat adjustment buttons
- ✅ Time signature dropdown selector
- ✅ Real-time playback indicator
- ✅ Clear instructions for users
- ✅ Confirm/cancel actions

---

## Component Props

```typescript
interface DownbeatConfirmationProps {
  audioUrl: string;                    // URL to audio file
  detectedDownbeat: number;             // Initial downbeat time (seconds)
  detectedTempo: number;                // BPM
  detectedTimeSignature: string;        // e.g., "4/4"
  beatTimes: number[];                  // Array of all beat timestamps
  onConfirm: (downbeat: number, timeSignature: string) => void;
  onCancel: () => void;
}
```

---

## Usage Example

```typescript
import { DownbeatConfirmation } from './components/DownbeatConfirmation';

function TranscriptionWorkflow() {
  const [showDownbeatConfirmation, setShowDownbeatConfirmation] = useState(false);
  const [downbeatData, setDownbeatData] = useState(null);

  const handleDownbeatConfirm = async (downbeat: number, timeSignature: string) => {
    // Save confirmed downbeat
    await saveDownbeat(downbeat, timeSignature);
    
    // Continue with chord detection
    setShowDownbeatConfirmation(false);
    startChordDetection(downbeat, timeSignature);
  };

  return (
    <>
      {showDownbeatConfirmation && downbeatData && (
        <DownbeatConfirmation
          audioUrl={downbeatData.audioUrl}
          detectedDownbeat={downbeatData.downbeat}
          detectedTempo={downbeatData.tempo}
          detectedTimeSignature={downbeatData.timeSignature}
          beatTimes={downbeatData.beatTimes}
          onConfirm={handleDownbeatConfirm}
          onCancel={() => setShowDownbeatConfirmation(false)}
        />
      )}
      
      {/* Rest of your UI */}
    </>
  );
}
```

---

## Backend API Endpoint Needed

### POST /api/detect-downbeat

**Request**:
```json
{
  "audioUrl": "s3://bucket/audio.m4a",
  "songId": "song-123"
}
```

**Response**:
```json
{
  "tempo": 136.0,
  "timeSignature": "4/4",
  "detectedDownbeat": 1.625,
  "confidence": 0.362,
  "beatTimes": [0.720, 1.184, 1.625, 2.090, ...],
  "downbeats": [1.625, 3.413, 5.201, ...],
  "audioUrl": "https://cdn.../audio.m4a"
}
```

**Implementation** (Python):
```python
from downbeat_detection import detect_downbeats
import librosa

@app.route('/api/detect-downbeat', methods=['POST'])
def detect_downbeat_endpoint():
    data = request.json
    audio_path = download_from_s3(data['audioUrl'])
    
    # Detect tempo and beats
    y, sr = librosa.load(audio_path, sr=22050)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo) if isinstance(tempo, (int, float)) else float(tempo[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
    
    # Detect downbeats
    downbeats, first_downbeat, info = detect_downbeats(
        audio_path,
        np.array(beat_times),
        tempo,
        time_signature="4/4"
    )
    
    return jsonify({
        'tempo': tempo,
        'timeSignature': '4/4',
        'detectedDownbeat': first_downbeat,
        'confidence': info['first_confidence'],
        'beatTimes': beat_times,
        'downbeats': downbeats.tolist(),
        'audioUrl': data['audioUrl']
    })
```

---

## Workflow Integration

### Step 1: After Audio Upload

```typescript
// After user uploads audio
const uploadResponse = await uploadAudio(file);

// Detect downbeat
const downbeatResponse = await fetch('/api/detect-downbeat', {
  method: 'POST',
  body: JSON.stringify({
    audioUrl: uploadResponse.audioUrl,
    songId: uploadResponse.songId
  })
});

const downbeatData = await downbeatResponse.json();

// Show confirmation UI
setDownbeatData(downbeatData);
setShowDownbeatConfirmation(true);
```

### Step 2: User Confirms

```typescript
const handleDownbeatConfirm = async (downbeat: number, timeSignature: string) => {
  // Save confirmed values
  await fetch('/api/confirm-downbeat', {
    method: 'POST',
    body: JSON.stringify({
      songId: currentSongId,
      downbeat,
      timeSignature
    })
  });
  
  // Continue with chord detection using confirmed downbeat
  await startChordDetection(currentSongId, downbeat, timeSignature);
  
  setShowDownbeatConfirmation(false);
};
```

### Step 3: Chord Detection with Confirmed Downbeat

```python
@app.route('/api/detect-chords', methods=['POST'])
def detect_chords_endpoint():
    data = request.json
    audio_path = download_from_s3(data['audioUrl'])
    confirmed_downbeat = data['downbeat']
    time_signature = data['timeSignature']
    
    # Use confirmed downbeat for measure alignment
    results = detect_chords_complete(
        audio_path,
        downbeat=confirmed_downbeat,
        time_signature=time_signature
    )
    
    return jsonify(results)
```

---

## UI/UX Flow

```
1. User uploads audio
   ↓
2. Backend detects tempo, beats, downbeat
   ↓
3. Show DownbeatConfirmation modal
   ├─ Display waveform with beat markers
   ├─ Play audio with click track
   ├─ User listens and confirms/adjusts
   └─ User selects time signature
   ↓
4. User clicks "Confirm & Continue"
   ↓
5. Save confirmed downbeat & time signature
   ↓
6. Run chord detection with correct measure alignment
   ↓
7. Display results with accurate measure numbers
```

---

## Styling Notes

The component uses Tailwind CSS classes. Make sure these are available:
- `bg-*`, `text-*`, `border-*` color utilities
- `rounded-*` border radius utilities
- `p-*`, `m-*` spacing utilities
- `flex`, `grid` layout utilities
- `hover:*` state utilities
- `transition-*` animation utilities

If using a different CSS framework, update the className attributes accordingly.

---

## Dependencies

**Frontend**:
- React 18+
- lucide-react (for icons)
- Web Audio API (built-in browser API)

**Backend**:
- librosa (beat detection)
- numpy (array operations)
- downbeat_detection.py (custom module)

---

## Testing Checklist

### Frontend
- [ ] Component renders correctly
- [ ] Audio plays when clicking play button
- [ ] Click track generates correctly
- [ ] Waveform shows beat markers
- [ ] Previous/next buttons adjust downbeat
- [ ] Time signature selector works
- [ ] Confirm button calls onConfirm with correct values
- [ ] Cancel button calls onCancel
- [ ] Responsive on mobile devices

### Backend
- [ ] /api/detect-downbeat returns correct data
- [ ] Beat detection works for various tempos
- [ ] Downbeat detection accuracy is acceptable
- [ ] Response time is reasonable (<5 seconds)
- [ ] Error handling for invalid audio files

### Integration
- [ ] Workflow progresses correctly after confirmation
- [ ] Confirmed downbeat is used in chord detection
- [ ] Measure numbers are accurate in final output
- [ ] User can go back and re-confirm if needed

---

## Deployment Steps

### 1. Frontend Deployment

```bash
# Add component to src/components/
cp DownbeatConfirmation.tsx src/components/

# Install dependencies if needed
npm install lucide-react

# Build and test
npm run build
npm run dev
```

### 2. Backend Deployment

```bash
# Copy downbeat detection module
cp simple-pipeline/chord-detection/downbeat_detection.py backend/functions-v2/chord-detector-ecs/

# Add endpoint to API
# (Update app.py with /api/detect-downbeat endpoint)

# Deploy to dev
./deploy-to-dev.sh
```

### 3. Test End-to-End

1. Upload audio file
2. Verify downbeat detection modal appears
3. Play audio and confirm alignment
4. Verify chord detection uses confirmed downbeat
5. Check measure numbers in output

---

## Future Enhancements

1. **Waveform from actual audio**:
   - Currently shows placeholder waveform
   - Could use Web Audio API to generate real waveform
   - Or pre-generate waveform data on backend

2. **Visual feedback**:
   - Highlight current measure during playback
   - Show measure numbers on waveform
   - Animate beat markers with audio

3. **Advanced adjustments**:
   - Fine-tune downbeat with slider
   - Manual time signature entry (e.g., "7/8")
   - Save/load downbeat presets

4. **Accessibility**:
   - Keyboard shortcuts (space = play/pause, arrows = adjust)
   - Screen reader support
   - High contrast mode

5. **Mobile optimization**:
   - Touch-friendly controls
   - Responsive waveform
   - Simplified UI for small screens

---

## Troubleshooting

### Click track not playing
- Check browser audio permissions
- Verify Web Audio API is supported
- Check console for errors

### Waveform not showing beats
- Verify beatTimes array is populated
- Check canvas rendering
- Ensure downbeat is within audio duration

### Audio not loading
- Check audioUrl is accessible
- Verify CORS headers on audio file
- Check network tab for 404/403 errors

### Downbeat adjustment not working
- Verify beatTimes array is sorted
- Check currentDownbeat is in beatTimes
- Ensure state updates correctly

---

## Summary

Created a professional, user-friendly React component for downbeat confirmation that:
- ✅ Provides visual feedback with waveform and beat markers
- ✅ Plays audio with synchronized click track
- ✅ Allows easy adjustment of downbeat and time signature
- ✅ Integrates cleanly into existing workflow
- ✅ Ensures accurate measure alignment for chord detection

Ready for deployment to dev branch!
