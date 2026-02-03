# Chord Display Fix Status

## Issue
- Only one chord per measure showing in PDF
- Lyrics not displaying
- Chord alignment off

## Root Cause Analysis

### 1. Missing Tempo Data ✅ FIXED IN CODE
**Problem**: Chord detector wasn't saving tempo to DynamoDB
- PDF generator defaults to 120 BPM when tempo is missing
- Wrong tempo = wrong measure duration calculation
- Wrong measure duration = chords grouped incorrectly

**Solution**: Updated `backend/functions-v2/chord-detector-ecs/app.py`
- Added `tempo` and `time_signature` fields to `ChordProgression` dataclass
- Calculate tempo using `librosa.beat.beat_track()` during chord detection
- Include tempo in `to_dict()` output for DynamoDB
- Committed in: `33e81b9`

**Status**: Code pushed, Docker image building via GitHub Actions

### 2. PDF Generator Code ✅ ALREADY CORRECT
**Analysis**: The PDF generator code is actually correct!
- `convertChordsToMeasures()` properly groups all chords by measure
- `generatePerfectMeasureLine()` renders all chords with beat positioning
- First chord = RED (downbeat), subsequent = BLACK (passing chords)
- Chords positioned proportionally based on beat (0-4 for 4/4 time)

**Code Flow**:
```javascript
// Groups chords by measure number
chords.forEach(chord => {
  const chordTime = chord.start;
  const measureNum = Math.floor(chordTime / secondsPerMeasure) + 1;
  const beatInMeasure = (chordTime % secondsPerMeasure) / secondsPerBeat;
  
  measureMap[measureNum].chords.push({
    chord: chord.chord,
    beat: beatInMeasure,
    isDownbeat: beatInMeasure < 0.5
  });
});
```

### 3. Test Data Issue
**Problem**: Existing job (8fc160ca-a1cc-4d03-8181-1b0aa91846cf) has no tempo
- Created before tempo fix
- Missing `tempo` and `timeSignature` fields in DynamoDB
- PDF generator falls back to 120 BPM default

**Verification**:
```bash
$ aws dynamodb get-item ... | jq '.Item.chordsData.M | keys'
[
  "averageConfidence",
  "chords",
  "duration",
  "key",
  "model",
  "scale",
  "sections",
  "totalChords"
]
# No "tempo" or "timeSignature"!
```

## Next Steps

### 1. Wait for Docker Build ⏳
- GitHub Actions building new chord-detector image
- Image will be pushed to ECR: `090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest`
- ECS will automatically use new image on next task run

### 2. Test with New Job ✅ READY
Once Docker build completes:
```bash
curl -X POST https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev/jobs \
  -H "Content-Type: application/json" \
  -d '{"youtubeUrl":"https://www.youtube.com/watch?v=kJQP7kiw5Fk"}'
```

Expected result:
- Chord data will include `tempo` and `timeSignature`
- PDF will show multiple chords per measure
- Chords will be positioned correctly by beat
- First chord RED, passing chords BLACK

### 3. Fix Lyrics Display 🔜
After verifying chords work, address lyrics:
- Check if `lyricsData.words` has timing information
- Verify lyrics are being matched to measure time ranges
- May need to adjust lyrics extraction in lyrics-transcriber

## Files Modified
- `backend/functions-v2/chord-detector-ecs/app.py` - Added tempo/timeSignature
- Commit: `33e81b9`
- Branch: `dev`
- Pushed to GitHub

## Testing Checklist
- [ ] Docker image built successfully
- [ ] New job created with test video
- [ ] Chord data includes tempo field
- [ ] PDF shows multiple chords per measure
- [ ] Chords positioned correctly by beat
- [ ] First chord RED, passing chords BLACK
- [ ] Lyrics display (separate issue)
