# Klangio API Setup Guide

**Goal:** Test Klangio API for accurate chord detection

---

## Step 1: Get API Key

### Sign Up

1. Go to **https://api-dashboard.klang.io**
2. Click "Sign Up" or "Get Started"
3. Create an account (email + password)
4. Verify your email

### Get API Key

1. Log in to the dashboard
2. Navigate to "API Keys" section
3. Click "Create New API Key"
4. Copy your API key (starts with `kl_...`)
5. **Save it securely!**

### Pricing

Check current pricing at: https://api-dashboard.klang.io/pricing

**Typical costs:**
- Free tier: Limited requests for testing
- Pay-per-use: ~$0.10-0.50 per transcription
- Subscription: ~$10-30/month for unlimited

---

## Step 2: Set Up Environment

### Install Dependencies

```bash
pip install requests
```

### Set API Key

**Option A: Environment Variable (Recommended)**
```bash
export KLANGIO_API_KEY='your-api-key-here'
```

**Option B: Add to .env file**
```bash
echo "KLANGIO_API_KEY=your-api-key-here" >> .env
```

---

## Step 3: Run Test

### Basic Test

```bash
python3 test-klangio-api.py
```

### What It Does

1. **Uploads audio** - Sends test audio file to Klangio
2. **Waits for processing** - Polls status every 5 seconds
3. **Gets results** - Downloads JSON and MusicXML
4. **Displays chords** - Shows detected chords, key, tempo

### Expected Output

```
🎵 Testing Klangio API
============================================================
Audio file: public/meetup_ring.mp3
API Key: kl_abc123...

1. Submitting transcription job...
------------------------------------------------------------
✓ Job submitted successfully
  Job ID: abc-123-def-456
  Status endpoint: https://api.klang.io/job/abc-123-def-456/status

2. Waiting for transcription to complete...
------------------------------------------------------------
  Status: PROCESSING (attempt 1/60)
  Status: PROCESSING (attempt 2/60)
  Status: COMPLETED (attempt 3/60)

✓ Transcription completed!

3. Fetching results...
------------------------------------------------------------
✓ Results retrieved successfully

============================================================
TRANSCRIPTION RESULTS
============================================================

🎹 Key: F major
🥁 Tempo: 76 BPM
⏱️  Time Signature: 4/4

🎸 Chords detected: 48

First 20 chords:
  1. F        at 0.20s
  2. Dm       at 3.30s
  3. Gm       at 9.60s
  4. C        at 16.50s
  5. F        at 34.50s
  ...

📄 Full result saved to: klangio-result-abc-123-def-456.json
📄 MusicXML saved to: klangio-result-abc-123-def-456.xml

============================================================
✅ TEST COMPLETE!
============================================================
```

---

## Step 4: Review Results

### Check Accuracy

1. **Open JSON file** - Review detected chords
2. **Compare with song** - Listen and verify accuracy
3. **Check key** - Is the key correct?
4. **Check tempo** - Is the BPM accurate?

### Compare with Current System

**Current system:**
- Chords: Often wrong
- Key: Often wrong
- Minor chords: Sometimes missing

**Klangio (expected):**
- Chords: Much more accurate
- Key: Trained on millions of songs
- Minor chords: Properly detected

---

## Step 5: Integration (If Good)

### Create Lambda Function

```python
# backend/functions-v2/klangio-transcriber/index.py

import requests
import os
import time

KLANGIO_API_KEY = os.environ['KLANGIO_API_KEY']
API_BASE_URL = "https://api.klang.io"

def lambda_handler(event, context):
    """
    Transcribe audio using Klangio API
    """
    audio_url = event['audioUrl']
    
    # Download audio
    audio_data = download_audio(audio_url)
    
    # Submit to Klangio
    job_id = submit_transcription(audio_data)
    
    # Wait for completion
    result = wait_for_completion(job_id)
    
    # Parse and return
    return {
        'key': result['key'],
        'tempo': result['tempo'],
        'chords': result['chords']
    }

def submit_transcription(audio_data):
    response = requests.post(
        f"{API_BASE_URL}/transcription",
        headers={'kl-api-key': KLANGIO_API_KEY},
        params={'model': 'universal'},
        data={'outputs': ['json']},
        files={'file': audio_data}
    )
    return response.json()['job_id']

def wait_for_completion(job_id, max_attempts=60):
    for _ in range(max_attempts):
        status = requests.get(
            f"{API_BASE_URL}/job/{job_id}/status",
            headers={'kl-api-key': KLANGIO_API_KEY}
        ).json()
        
        if status['status'] == 'COMPLETED':
            return requests.get(
                f"{API_BASE_URL}/job/{job_id}/json",
                headers={'kl-api-key': KLANGIO_API_KEY}
            ).json()
        
        time.sleep(5)
    
    raise Exception("Timeout waiting for transcription")
```

### Update Workflow

```json
{
  "States": {
    "DownloadAudio": {...},
    "TranscribeLyrics": {...},
    "TranscribeChords": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:klangio-transcriber",
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

## Troubleshooting

### Error: "Invalid API Key"

- Check API key is correct
- Verify it's set in environment
- Try regenerating key in dashboard

### Error: "Insufficient credits"

- Check your account balance
- Add credits or upgrade plan
- Use free tier for testing

### Error: "File too large"

- Check file size limits
- Compress audio if needed
- Use shorter test file

### Timeout

- Increase max_attempts in script
- Check Klangio status page
- Try again later

---

## Cost Estimation

### Per-Job Cost

**Assumptions:**
- Average song: 3-5 minutes
- Klangio cost: ~$0.20 per transcription

**Current costs:**
- ECS (chord detection): ~$0.05
- Deepgram (lyrics): ~$0.02
- Total: ~$0.07 per job

**With Klangio:**
- Klangio (chords): ~$0.20
- Deepgram (lyrics): ~$0.02
- Total: ~$0.22 per job

**Increase:** +$0.15 per job

### Monthly Cost

**100 jobs/month:**
- Current: $7
- With Klangio: $22
- Increase: +$15/month

**1000 jobs/month:**
- Current: $70
- With Klangio: $220
- Increase: +$150/month

**Worth it?** If accuracy is critical, YES!

---

## Alternative: Free Tier Testing

### Use Free Credits

1. Sign up for free account
2. Get free credits for testing
3. Test with 5-10 songs
4. Evaluate accuracy
5. Decide if worth paying

### Fallback Strategy

```python
def detect_chords(audio_path):
    try:
        # Try Klangio first
        return transcribe_with_klangio(audio_path)
    except Exception as e:
        log(f"Klangio failed: {e}")
        # Fall back to current system
        return detect_chords_librosa(audio_path)
```

**Benefits:**
- Always works (fallback available)
- Best accuracy when credits available
- Graceful degradation

---

## Next Steps

1. ✅ Get Klangio API key
2. ✅ Run test script
3. ⏳ Review accuracy
4. ⏳ Compare with current system
5. ⏳ Decide: integrate or try alternatives

---

## Summary

**Klangio API:**
- ✅ Professional music transcription
- ✅ Trained on millions of songs
- ✅ Multiple output formats
- ✅ Good documentation
- ⚠️ Costs ~$0.20 per job

**Test it now:**
```bash
export KLANGIO_API_KEY='your-key-here'
python3 test-klangio-api.py
```

**If accuracy is good, integrate it!**
