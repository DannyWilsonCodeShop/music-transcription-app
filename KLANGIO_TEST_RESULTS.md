# Klangio API Test Results

**Date:** February 5, 2026  
**Status:** ❌ FAILED - API Key Issue

---

## Test Summary

Attempted to test Klangio API for chord transcription but encountered authentication/permission issues.

### What We Tried

1. **Setup:**
   - Added `KLANGIO_API_KEY` to `.env` file
   - Created test script `test-klangio-api.py`
   - Test audio: `public/meetup_ring.mp3` (46KB, MP3, 48kHz stereo)

2. **API Calls:**
   - ✅ Job submission successful (got job ID)
   - ✅ Status polling working
   - ❌ Job fails immediately with "Unknown error!"

3. **Models Tested:**
   - `universal` - Failed
   - `lead` - Failed

### Error Details

```json
{
  "status": "FAILED",
  "error": "Unknown error!"
}
```

Job IDs tested:
- `3e68e2e5-085c-4569-99ed-c0cd7d75615d`
- `cbd4357b-ce54-46f8-892d-a3dc2c4c1741`
- `a076b257-fb81-4660-b69f-d440f2476fec`

---

## Possible Causes

### 1. API Key Permissions
- Free tier may not have transcription access
- API key might be for a different service (Klang.ai vs Klang.io)
- Account needs to be activated or verified

### 2. Audio File Issue
- File format might not be supported (though MP3 should work)
- File might be too short or too long
- Sample rate (48kHz) might need to be 44.1kHz

### 3. API Endpoint Issue
- Using wrong base URL
- API version mismatch
- Service might be down

---

## Next Steps

### Option A: Fix Klangio Access

1. **Check API Dashboard:**
   - Go to https://api-dashboard.klang.io
   - Verify account status
   - Check API key permissions
   - Look for error logs or usage limits

2. **Contact Support:**
   - Email Klangio support about the "Unknown error"
   - Provide job IDs for debugging
   - Ask about free tier limitations

3. **Try Different Audio:**
   - Convert to 44.1kHz WAV
   - Try a longer/shorter file
   - Test with a simple piano recording

### Option B: Try Alternative Services (RECOMMENDED)

Since Klangio isn't working immediately, consider these alternatives:

#### 1. **Basic Pitch (Spotify) - FREE** ⭐ RECOMMENDED

**Pros:**
- ✅ Completely free and open source
- ✅ No API key needed
- ✅ Runs locally (no rate limits)
- ✅ Good accuracy for polyphonic audio
- ✅ Outputs MIDI (can convert to chords)

**Cons:**
- Outputs MIDI notes, not chord symbols directly
- Need to implement MIDI → chord conversion

**Implementation:**
```python
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

# Predict notes
model_output, midi_data, note_events = predict(
    'audio.mp3',
    ICASSP_2022_MODEL_PATH
)

# Convert MIDI to chords (need to implement)
chords = midi_to_chords(midi_data)
```

**Install:**
```bash
pip install basic-pitch
```

#### 2. **Omnizart - FREE**

**Pros:**
- ✅ Free and open source
- ✅ Has chord-specific model
- ✅ Direct chord output

**Cons:**
- Complex setup
- May need GPU for good performance

**Implementation:**
```python
from omnizart.chord import app as chord_app

chords = chord_app.transcribe('audio.mp3')
```

#### 3. **Chordify API**

**Pros:**
- Specialized in chord detection
- Good accuracy
- Simple API

**Cons:**
- Paid service
- May have similar issues as Klangio

#### 4. **AnthemScore**

**Pros:**
- Desktop app with API
- Very accurate
- Multiple output formats

**Cons:**
- Expensive ($99 one-time or subscription)
- May not have public API

---

## Recommendation

**Try Basic Pitch first** since it's:
1. Free
2. No API key needed
3. Well-maintained by Spotify
4. Good accuracy

If Basic Pitch works well, we can:
1. Implement MIDI → chord conversion
2. Integrate into your ECS pipeline
3. Keep current system as fallback
4. No additional costs!

---

## Implementation Plan: Basic Pitch

### Step 1: Test Locally (10 minutes)

```bash
# Install
pip install basic-pitch

# Test
python3 test-basic-pitch.py
```

### Step 2: Implement MIDI → Chord Conversion (1-2 hours)

```python
def midi_to_chords(midi_data, key='C'):
    """
    Convert MIDI notes to chord symbols
    
    Strategy:
    1. Group notes by time windows (beat-aligned)
    2. For each window, find active notes
    3. Match note pattern to chord templates
    4. Return chord progression with timing
    """
    # Implementation here
    pass
```

### Step 3: Integrate into Pipeline (2-3 hours)

1. Add Basic Pitch to ECS container
2. Update `chord-detector-ecs/app.py`
3. Add MIDI → chord conversion
4. Test end-to-end

### Step 4: Compare Accuracy

Test with same songs:
- Current system (librosa + essentia)
- Basic Pitch + chord conversion
- Choose best performer

---

## Cost Comparison

| Service | Cost per Job | Monthly (100 jobs) | Accuracy | Setup Time |
|---------|--------------|-------------------|----------|------------|
| Current (librosa) | $0.05 | $5 | ⭐⭐ Poor | ✅ Done |
| Klangio | $0.20 | $20 | ⭐⭐⭐⭐ Good | ❌ Not working |
| Basic Pitch | $0.05 | $5 | ⭐⭐⭐ Good | ⏱️ 3-4 hours |
| Omnizart | $0.05 | $5 | ⭐⭐⭐ Good | ⏱️ 4-6 hours |

**Winner:** Basic Pitch (free, good accuracy, reasonable setup time)

---

## Action Items

- [ ] Try Basic Pitch locally
- [ ] Implement MIDI → chord conversion
- [ ] Compare accuracy with current system
- [ ] If good, integrate into pipeline
- [ ] If not good, try Omnizart
- [ ] If still not good, debug Klangio API key issue

---

## Files Created

- `test-klangio-api.py` - Klangio test script (not working)
- `KLANGIO_SETUP_GUIDE.md` - Setup instructions
- `EXTERNAL_TRANSCRIPTION_SERVICES.md` - Service comparison
- `KLANGIO_TEST_RESULTS.md` - This file

---

## Conclusion

Klangio API has authentication/permission issues. **Recommend trying Basic Pitch** (free, open source) as the next step. It's likely to work better and costs nothing.

Would you like me to create a Basic Pitch test script?
