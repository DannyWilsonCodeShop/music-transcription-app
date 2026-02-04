# Monitoring Data Quality Fixes

Quick reference for monitoring the deployed fixes.

---

## CloudWatch Logs

### Lyrics Transcriber Logs
**Log Group:** `/aws/lambda/chordscout-v2-lyrics-transcriber-dev`

**What to look for:**
```
First word "now" starts at: 161.81s
⚠️ TIMESTAMP OFFSET DETECTED: 161.81s
Adjusting all timestamps by -161.81s to align with actual audio
✓ Timestamps adjusted. First word now starts at: 0s
```

**Check logs:**
```bash
aws logs tail /aws/lambda/chordscout-v2-lyrics-transcriber-dev \
  --follow \
  --profile chordscout \
  --filter-pattern "TIMESTAMP OFFSET"
```

---

### Chord Detector Logs
**Log Group:** `/ecs/chordscout-chord-detector`

**What to look for:**
```
Detecting tempo...
✓ Tempo detected: 152.3 BPM
  Beats detected: 487
  Detection time: 1.23s

Detecting key...
✓ Key detection complete
  Detected key: D major
  Confidence: 0.87
  Detection time: 0.45s
```

**Check logs:**
```bash
aws logs tail /ecs/chordscout-chord-detector \
  --follow \
  --profile chordscout \
  --filter-pattern "Tempo detected"
```

---

## DynamoDB Queries

### Check Timestamp Fix
```bash
# Get first word timestamp
aws dynamodb get-item \
  --table-name ChordScout-Jobs-V2-dev \
  --key '{"jobId": {"S": "YOUR_JOB_ID"}}' \
  --profile chordscout \
  --output json | jq '{
    firstWord: .Item.lyricsData.M.words.L[0].M.word.S,
    firstWordStart: .Item.lyricsData.M.words.L[0].M.start.N,
    firstWordEnd: .Item.lyricsData.M.words.L[0].M.end.N
  }'
```

**Expected:**
```json
{
  "firstWord": "now",
  "firstWordStart": "16.2",  // ✅ ~16s (not 161s)
  "firstWordEnd": "16.5"
}
```

---

### Check Tempo Detection
```bash
# Get tempo
aws dynamodb get-item \
  --table-name ChordScout-Jobs-V2-dev \
  --key '{"jobId": {"S": "YOUR_JOB_ID"}}' \
  --profile chordscout \
  --output json | jq '{
    tempo: .Item.chordsData.M.tempo.N,
    duration: .Item.chordsData.M.duration.N,
    totalChords: (.Item.chordsData.M.chords.L | length)
  }'
```

**Expected:**
```json
{
  "tempo": "152.3",  // ✅ Actual BPM (not null)
  "duration": "367.45",
  "totalChords": 258
}
```

---

### Check Key Detection
```bash
# Get key, mode, and confidence
aws dynamodb get-item \
  --table-name ChordScout-Jobs-V2-dev \
  --key '{"jobId": {"S": "YOUR_JOB_ID"}}' \
  --profile chordscout \
  --output json | jq '{
    key: .Item.chordsData.M.key.S,
    mode: .Item.chordsData.M.mode.S,
    keyConfidence: .Item.chordsData.M.keyConfidence.N,
    model: .Item.chordsData.M.model.S
  }'
```

**Expected:**
```json
{
  "key": "D",
  "mode": "major",  // ✅ Detected (not null)
  "keyConfidence": "0.87",  // ✅ Detected (not null)
  "model": "librosa-chromagram-enhanced"
}
```

---

### Full Job Status
```bash
# Get complete job data
aws dynamodb get-item \
  --table-name ChordScout-Jobs-V2-dev \
  --key '{"jobId": {"S": "YOUR_JOB_ID"}}' \
  --profile chordscout \
  --output json | jq '{
    jobId: .Item.jobId.S,
    status: .Item.status.S,
    progress: .Item.progress.N,
    videoTitle: .Item.videoTitle.S,
    pdfUrl: .Item.pdfUrl.S,
    lyrics: {
      firstWord: .Item.lyricsData.M.words.L[0].M.word.S,
      firstWordStart: .Item.lyricsData.M.words.L[0].M.start.N,
      totalWords: (.Item.lyricsData.M.words.L | length)
    },
    chords: {
      key: .Item.chordsData.M.key.S,
      mode: .Item.chordsData.M.mode.S,
      tempo: .Item.chordsData.M.tempo.N,
      keyConfidence: .Item.chordsData.M.keyConfidence.N,
      totalChords: (.Item.chordsData.M.chords.L | length)
    }
  }'
```

---

## Verification Checklist

### ✅ Timestamp Offset Fix
- [ ] First word starts at ~16s (not 161s)
- [ ] CloudWatch logs show "TIMESTAMP OFFSET DETECTED"
- [ ] All word timestamps are adjusted
- [ ] Syllable timestamps are adjusted

### ✅ Tempo Detection
- [ ] `chordsData.tempo` is not null
- [ ] Tempo value is reasonable (60-200 BPM)
- [ ] CloudWatch logs show "Tempo detected: X.X BPM"
- [ ] Beats detected count is logged

### ✅ Key Detection
- [ ] `chordsData.key` is detected
- [ ] `chordsData.mode` is "major" or "minor"
- [ ] `chordsData.keyConfidence` is between 0.0 and 1.0
- [ ] CloudWatch logs show "Detected key: X major/minor"

### ✅ PDF Output
- [ ] Lyrics start at correct verse (Verse 1, not Verse 17)
- [ ] Tempo shows actual BPM (not 120)
- [ ] Key shows detected key with mode
- [ ] Lyrics align with chords correctly

---

## Troubleshooting

### Issue: Timestamp offset not detected
**Symptom:** First word still starts at 161s  
**Check:**
```bash
# Check if Lambda was updated
aws lambda get-function \
  --function-name chordscout-v2-lyrics-transcriber-dev \
  --profile chordscout \
  --output json | jq '{
    LastModified,
    CodeSize,
    State
  }'
```
**Expected:** LastModified should be 2026-02-04 14:22 or later

---

### Issue: Tempo still null
**Symptom:** `chordsData.tempo` is null  
**Check:**
```bash
# Check ECS task definition
aws ecs describe-task-definition \
  --task-definition chordscout-v2-dev-chord-detector \
  --profile chordscout \
  --output json | jq '.taskDefinition.containerDefinitions[0].image'
```
**Expected:** Image should be `090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest`

**Check Docker image digest:**
```bash
aws ecr describe-images \
  --repository-name chordscout-chord-detector \
  --profile chordscout \
  --output json | jq '.imageDetails[] | select(.imageTags[] == "latest") | .imageDigest'
```
**Expected:** `sha256:78c38141090b9974bb418be9cab1b98b05e36006b1d556fc8d1c6d929cc31a6a`

---

### Issue: Key detection not improved
**Symptom:** `chordsData.mode` and `keyConfidence` are null  
**Check:** Same as tempo issue - verify Docker image is updated

---

## Quick Test Commands

### Test with existing job
```bash
JOB_ID="c3ab9fe9-b43d-408a-9a04-5aef7fcf59c9"

echo "Before fixes:"
aws dynamodb get-item \
  --table-name ChordScout-Jobs-V2-dev \
  --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
  --profile chordscout \
  --output json | jq '{
    firstWordStart: .Item.lyricsData.M.words.L[0].M.start.N,
    tempo: .Item.chordsData.M.tempo,
    mode: .Item.chordsData.M.mode
  }'
```

### Monitor new job
```bash
# Replace with your new job ID
NEW_JOB_ID="YOUR_NEW_JOB_ID"

# Watch job progress
watch -n 2 "aws dynamodb get-item \
  --table-name ChordScout-Jobs-V2-dev \
  --key '{\"jobId\": {\"S\": \"$NEW_JOB_ID\"}}' \
  --profile chordscout \
  --output json | jq '{status: .Item.status.S, progress: .Item.progress.N}'"
```

---

## Success Indicators

### Lyrics Transcriber
✅ Log message: "TIMESTAMP OFFSET DETECTED"  
✅ Log message: "Timestamps adjusted"  
✅ First word start time: ~16s

### Chord Detector
✅ Log message: "Tempo detected: X.X BPM"  
✅ Log message: "Detected key: X major/minor"  
✅ Log message: "Confidence: 0.XX"

### DynamoDB
✅ `lyricsData.words[0].start`: ~16  
✅ `chordsData.tempo`: Not null  
✅ `chordsData.mode`: "major" or "minor"  
✅ `chordsData.keyConfidence`: 0.0-1.0

### PDF
✅ Lyrics start at Verse 1  
✅ Tempo shows actual BPM  
✅ Key shows with mode  
✅ Lyrics align correctly

---

**Last Updated:** February 4, 2026
