# Pattern-Based Key Detection - DEPLOYED ✅

**Date:** February 4, 2026  
**Status:** DEPLOYED AND READY FOR TESTING

---

## Problem

The chord detector was incorrectly identifying the key of "Like The Dew" as **C major** when it should be **F major**.

**User Correction:**
> "Its in F major, going from the 1 chord to the 6, then 2 then 5 then 1 basic chord progression in NNS"

This is the classic **I-vi-ii-V-I** progression: **F - Dm - Gm - C - F**

**Root Cause:**
- The algorithm was picking up the strong presence of C chords (the V chord) and identifying it as tonic instead of F
- Chromagram-based detection doesn't understand harmonic function or cadences
- Simple cadence counting (V-I, IV-I) wasn't sufficient without pattern context

---

## Solution: Pattern-Based Key Detection

### Key Insight
The algorithm now **looks for repeating chord progression patterns** throughout the song to establish context, rather than just analyzing individual chord transitions.

### How It Works

1. **Extract Chord Sequence**
   - Converts all detected chords into a sequence of roots and qualities (major/minor)
   - Example: `[F, Dm, Gm, C, F, Dm, Gm, C, ...]`

2. **Find Repeating Patterns**
   - Searches for patterns of 3-6 chords that repeat at least twice
   - Example: Pattern `(F, Dm, Gm, C)` repeating 8 times in the song

3. **Analyze Patterns Against All Keys**
   - For each repeating pattern, tests it against all 12 possible keys
   - Converts pattern to intervals relative to each potential key
   - Example: If key is F, pattern becomes `(0, 9, 2, 7)` = I-vi-ii-V

4. **Score Common Progressions**
   - **I-vi-ii-V** (0-9-2-7): Score 10 - Very common in jazz/pop
   - **I-IV-V** (0-5-7): Score 9 - Most common in rock/pop
   - **I-V-vi-IV** (0-7-9-5): Score 9 - Very common pop progression
   - **ii-V-I** (2-7-0): Score 8 - Jazz cadence
   - **I-vi-IV-V** (0-9-5-7): Score 8 - 50s progression
   - **V-I cadence** (7-0): Score 7 - Strongest cadence
   - **IV-I cadence** (5-0): Score 6 - Plagal cadence

5. **Weight by Pattern Strength**
   - Score = progression_strength × repetition_count × pattern_length
   - Example: I-vi-ii-V (score 10) × 8 repetitions × 4 chords = 320 points for F major

6. **Determine Mode**
   - Analyzes chord qualities at each scale degree
   - In major keys: I, IV, V are major; ii, iii, vi are minor
   - In minor keys: i, iv, v are minor; III, VI, VII are major

---

## Code Changes

**File:** `backend/functions-v2/chord-detector-ecs/app.py`

**Function:** `detect_key_from_progression(chords)`

### Key Features

```python
# Find repeating patterns (3-6 chord sequences)
for pattern_length in range(3, 7):
    patterns_found = {}
    
    for i in range(len(chord_sequence) - pattern_length + 1):
        pattern = tuple(c['root'] for c in chord_sequence[i:i+pattern_length])
        patterns_found[pattern] = patterns_found.get(pattern, 0) + 1
    
    # Find patterns that repeat at least twice
    for pattern, count in patterns_found.items():
        if count >= 2:  # Pattern repeats at least once
            # Analyze this pattern for each possible key
            ...
```

### Progression Recognition

```python
# I-vi-ii-V (0-9-2-7) - very common in jazz/pop
if tuple(intervals) == (0, 9, 2, 7) or tuple(intervals[:4]) == (0, 9, 2, 7):
    progression_score = 10

# I-IV-V (0-5-7) - most common in rock/pop
elif tuple(intervals) == (0, 5, 7) or tuple(intervals[:3]) == (0, 5, 7):
    progression_score = 9

# I-V-vi-IV (0-7-9-5) - very common pop progression
elif tuple(intervals) == (0, 7, 9, 5) or tuple(intervals[:4]) == (0, 7, 9, 5):
    progression_score = 9
```

### Scoring System

```python
# Weight by: progression strength × repetition count × pattern length
pattern_scores[potential_key] += progression_score * count * pattern_length
```

---

## Expected Results

### For "Like The Dew" (I-vi-ii-V-I in F major)

**Before:**
```json
{
  "key": "C",
  "mode": "major",
  "keyConfidence": 0.82
}
```

**After (Expected):**
```json
{
  "key": "F",
  "mode": "major",
  "keyConfidence": 0.95+
}
```

**Why It Should Work:**
1. Pattern `(F, Dm, Gm, C)` repeats throughout the song
2. When tested against F as key: intervals = `(0, 9, 2, 7)` = I-vi-ii-V
3. This matches the highest-scoring progression (score 10)
4. Multiple repetitions × high score = F major wins decisively

---

## Deployment Details

### Docker Image
- **Repository:** `090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector`
- **Tag:** `latest`
- **Digest:** `sha256:e6f564068dc81fbd70d9591b7af4e2452c8652114f6c270e39f3b0f68e67a17a`
- **Platform:** `linux/amd64`
- **Size:** 4.41 GB
- **Pushed:** February 4, 2026 12:20 EST

### Automatic Deployment
- ECS tasks automatically pull the `:latest` tag on next run
- No manual service update required
- Next job submission will use the new algorithm

---

## How to Test

### Submit Test Job
```bash
# Via frontend or API
YouTube URL: https://www.youtube.com/watch?v=Q-RKhgsZu64
Song: "Like The Dew"
Expected Key: F major
```

### Check Results
```bash
aws dynamodb get-item \
  --table-name ChordScout-Jobs-V2-dev \
  --key '{"jobId": {"S": "NEW_JOB_ID"}}' \
  --profile chordscout \
  --output json | jq '{
    key: .Item.chordsData.M.key.S,
    mode: .Item.chordsData.M.mode.S,
    keyConfidence: .Item.chordsData.M.keyConfidence.N
  }'
```

### Expected Output
```json
{
  "key": "F",
  "mode": "major",
  "keyConfidence": "0.95"
}
```

---

## Advantages Over Previous Algorithm

### Old Algorithm (Cadence-Based)
- ❌ Only looked at adjacent chord pairs (V-I, IV-I)
- ❌ No context of overall progression
- ❌ Confused by strong V chords (C in F major)
- ❌ Didn't recognize common progression patterns

### New Algorithm (Pattern-Based)
- ✅ Analyzes repeating patterns of 3-6 chords
- ✅ Recognizes common progressions (I-vi-ii-V, I-IV-V, etc.)
- ✅ Weights by pattern repetition (more repetitions = higher confidence)
- ✅ Understands harmonic context, not just individual transitions
- ✅ Scores based on music theory (functional harmony)

---

## Common Progressions Recognized

| Progression | Intervals | Score | Common In |
|-------------|-----------|-------|-----------|
| I-vi-ii-V | 0-9-2-7 | 10 | Jazz, Pop, Standards |
| I-IV-V | 0-5-7 | 9 | Rock, Blues, Country |
| I-V-vi-IV | 0-7-9-5 | 9 | Modern Pop (Axis progression) |
| ii-V-I | 2-7-0 | 8 | Jazz (turnaround) |
| I-vi-IV-V | 0-9-5-7 | 8 | 50s Doo-wop |
| V-I | 7-0 | 7 | Classical cadence |
| IV-I | 5-0 | 6 | Plagal cadence (Amen) |

---

## Logging Output

The algorithm now logs detailed pattern analysis:

```
Pattern analysis: Found 12 potential keys
Best key: F (score: 320, confidence: 0.95)
Mode indicators: major=45, minor=8
```

This helps debug and verify the algorithm is working correctly.

---

## Success Criteria

The deployment is successful if:
1. ✅ "Like The Dew" is detected as **F major** (not C major)
2. ✅ Confidence score is **high** (>0.90)
3. ✅ Mode is correctly identified as **major**
4. ✅ Nashville numbers are correct (1-6m-2m-5-1)
5. ✅ PDF shows accurate chord progressions

---

## Next Steps

1. **Test with "Like The Dew"** - Submit new job and verify F major detection
2. **Monitor CloudWatch logs** - Check pattern analysis output
3. **Verify PDF output** - Ensure Nashville numbers are correct (1-6m-2m-5)
4. **Test with other songs** - Verify algorithm works across different keys and progressions
5. **Fine-tune scoring** - Adjust progression scores if needed based on results

---

## Technical Notes

- **Minimum chords required:** 8 (to detect meaningful patterns)
- **Pattern lengths tested:** 3-6 chords
- **Minimum repetitions:** 2 (pattern must repeat at least once)
- **Scoring formula:** `progression_score × repetition_count × pattern_length`
- **Mode detection:** Analyzes chord qualities at each scale degree
- **Fallback:** If no patterns found, uses chromagram-based detection

---

**Status: DEPLOYED AND READY FOR TESTING ✅**

The enhanced pattern-based key detection algorithm is now live and will be used on the next job submission.
