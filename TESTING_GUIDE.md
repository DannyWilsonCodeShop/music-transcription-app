# Testing Guide - Improved Chord Detection

**Date:** February 5, 2026

---

## Quick Start

### 1. Submit a Test Job

```bash
node submit-test-job.cjs "https://www.youtube.com/watch?v=Q-RKhgsZu64"
```

This will:
- Submit "Like The Dew" for analysis
- Show real-time progress
- Display the job ID when complete

**Expected time:** 5-6 minutes

---

### 2. Analyze the Patterns

Once the job completes, run:

```bash
node test-pattern-analysis.cjs <JOB_ID>
```

This shows:
- Total chords detected
- Repeating patterns with progressions
- Key detection results
- Song structure
- First 20 chords

**What to look for:**
- ✅ Total chords: 40-60 (not 258)
- ✅ Repeating patterns: 3-5 (not 0)
- ✅ Key: F major (not C major)
- ✅ Pattern 1: F → Dm → Gm → C

---

### 3. Create Diagnostic PDF

```bash
node create-pattern-diagnostic-pdf.cjs <JOB_ID>
```

This creates a simple PDF showing:
- Detected repeating patterns
- Chord progressions for each pattern
- Number of occurrences
- Timestamps where patterns appear
- First 50 chords in raw sequence

**Output:** `pattern-diagnostic-<JOB_ID>.pdf`

---

## What You Should See

### Old Algorithm (Before Improvements)

```
Total chords: 258
Average duration: 1.4s
Repeating patterns: 0
Key detected: C major ❌

Pattern Analysis:
  NO REPEATING PATTERNS DETECTED

Raw Chord Sequence:
  C(0.2s)  D(1.8s)  C(3.1s)  A(4.7s)  D(6.2s)  F(7.2s)  F(8.7s)  C(11.1s)  D(12.5s)  D(13.7s)
  ... (248 more chords)
```

### New Algorithm (After Improvements)

```
Total chords: 45
Average duration: 8.3s
Repeating patterns: 3
Key detected: F major ✅

Pattern 1:
  Progression: F  →  Dm  →  Gm  →  C
  Length: 4 chords
  Occurrences: 8 times in the song
  Appears at: 0:15, 0:45, 1:15, 1:45, 2:15, 2:45, 3:15, 3:45

Pattern 2:
  Progression: Bb  →  C  →  F
  Length: 3 chords
  Occurrences: 4 times in the song
  Appears at: 0:30, 1:00, 1:30, 2:00

Pattern 3:
  Progression: Dm  →  Gm  →  C  →  F
  Length: 4 chords
  Occurrences: 3 times in the song
  Appears at: 2:30, 3:00, 3:30

Raw Chord Sequence:
  F(0.2s)  Dm(8.5s)  Gm(16.8s)  C(25.1s)  F(33.4s)  Bb(41.7s)  C(50.0s)  F(58.3s)
  ... (37 more chords)
```

---

## Diagnostic PDF Layout

The diagnostic PDF will show:

```
┌─────────────────────────────────────────────────────────┐
│ Pattern Diagnostic Report                               │
│                                                          │
│ Song: Like The Dew                                      │
│ Key: F major                                            │
│ Tempo: 76 BPM                                           │
│ Total Chords: 45                                        │
│ Duration: 371.5s                                        │
│                                                          │
│ ─────────────────────────────────────────────────────── │
│                                                          │
│ DETECTED REPEATING PATTERNS                             │
│ Found 3 repeating patterns                              │
│                                                          │
│ Pattern 1                                               │
│   F  →  Dm  →  Gm  →  C                                │
│   Length: 4 chords                                      │
│   Occurrences: 8 times in the song                     │
│   Appears at: 0:15, 0:45, 1:15, 1:45, 2:15...         │
│                                                          │
│ Pattern 2                                               │
│   Bb  →  C  →  F                                       │
│   Length: 3 chords                                      │
│   Occurrences: 4 times in the song                     │
│   Appears at: 0:30, 1:00, 1:30, 2:00                  │
│                                                          │
│ Pattern 3                                               │
│   Dm  →  Gm  →  C  →  F                               │
│   Length: 4 chords                                      │
│   Occurrences: 3 times in the song                     │
│   Appears at: 2:30, 3:00, 3:30                        │
│                                                          │
│ ─────────────────────────────────────────────────────── │
│                                                          │
│ RAW CHORD SEQUENCE                                      │
│ First 50 chords detected:                               │
│                                                          │
│ F(0.2s)  Dm(8.5s)  Gm(16.8s)  C(25.1s)  F(33.4s)      │
│ Bb(41.7s)  C(50.0s)  F(58.3s)  Dm(66.6s)  Gm(74.9s)   │
│ ...                                                      │
└─────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### No Patterns Detected

If you see "NO REPEATING PATTERNS DETECTED":

1. **Check total chords**
   - If > 200: Old algorithm still running (too sensitive)
   - If < 100: New algorithm running (good)

2. **Check average duration**
   - If < 2s: Too many chords detected
   - If > 5s: Good chord detection

3. **Possible causes:**
   - Song has no repeating progressions (rare)
   - Chord detection still too noisy
   - Need to adjust confidence threshold

### Wrong Key Detected

If key is wrong (e.g., C instead of F):

1. **Check if patterns were found**
   - No patterns = can't determine key from context
   - Need better chord detection first

2. **Check pattern progressions**
   - Do they make sense musically?
   - Are they consistent?

### Too Many Chords

If still seeing 200+ chords:

1. **Check if new algorithm deployed**
   - ECS pulls `:latest` tag on next run
   - May need to force new task

2. **Check CloudWatch logs**
   - Look for "beat-synchronized detection"
   - Should show "Final chord count: 40-60"

---

## Expected Improvements

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Total chords | 258 | 40-60 | ⏳ Testing |
| Avg duration | 1.4s | 6-9s | ⏳ Testing |
| Patterns found | 0 | 3-5 | ⏳ Testing |
| Key accuracy | ❌ Wrong | ✅ Correct | ⏳ Testing |
| Pattern recognition | ❌ Failed | ✅ Works | ⏳ Testing |

---

## Next Steps After Testing

### If Improvements Work ✅

1. Update main PDF generator to use patterns
2. Add section labels based on patterns
3. Filter lyrics to matched sections
4. Deploy to production

### If Still Issues ❌

1. Adjust confidence threshold (currently 0.3)
2. Adjust min duration (currently 1.0s)
3. Try different smoothing parameters
4. Consider alternative chord detection library

---

## Commands Reference

```bash
# Submit new job
node submit-test-job.cjs "https://www.youtube.com/watch?v=Q-RKhgsZu64"

# Analyze patterns (console output)
node test-pattern-analysis.cjs <JOB_ID>

# Create diagnostic PDF
node create-pattern-diagnostic-pdf.cjs <JOB_ID>

# Check CloudWatch logs
aws logs tail /aws/ecs/chordscout-chord-detector-dev --since 10m --follow --profile chordscout

# Check job in DynamoDB
aws dynamodb get-item \
  --table-name ChordScout-Jobs-V2-dev \
  --key '{"jobId": {"S": "<JOB_ID>"}}' \
  --profile chordscout \
  --output json | jq '.Item.chordsData.M'
```

---

## Test Songs

### "Like The Dew" (Recommended)
- **URL:** `https://www.youtube.com/watch?v=Q-RKhgsZu64`
- **Expected Key:** F major
- **Expected Pattern:** F → Dm → Gm → C (I-vi-ii-V)
- **Why:** Clear repeating progression, good for testing

### Other Test Songs
- Simple progressions (I-IV-V)
- Complex jazz progressions (ii-V-I)
- Different keys and tempos

---

**Ready to test!** Submit a new job and see if the improved algorithm works.
