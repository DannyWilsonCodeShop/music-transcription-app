# Nashville Number System Implementation

**Date:** February 5, 2026  
**Status:** ✅ Implemented and building

---

## What Changed

Switched from Roman numeral notation (I, ii, iii, IV, V, vi, vii) to **Nashville Number System** (1, 2, 3, 4, 5, 6, 7).

### Why Nashville Numbers?

**Simpler and more intuitive:**
- Numbers instead of Roman numerals
- Easier to read and understand
- Standard in Nashville music industry
- Used by session musicians worldwide

### Before (Roman Numerals)

```
Pattern 1:
  Chords:  F → Dm → Gm → C
  Roman:   I → vi → ii → V
```

**Issues:**
- Uppercase/lowercase distinction (I vs i)
- Less familiar to many musicians
- More complex notation

### After (Nashville Numbers)

```
Pattern 1:
  Chords:  F → Dm → Gm → C
  Numbers: 1 → 6m → 2m → 5
```

**Benefits:**
- ✅ Simple numbers (1-7)
- ✅ Quality modifiers (m for minor)
- ✅ Easier to read
- ✅ Industry standard

---

## Notation Guide

### Basic Numbers

In the key of **C major**:

| Chord | Nashville Number | Explanation |
|-------|------------------|-------------|
| C     | 1                | Tonic (root) |
| D     | 2                | Second degree |
| E     | 3                | Third degree |
| F     | 4                | Fourth degree (subdominant) |
| G     | 5                | Fifth degree (dominant) |
| A     | 6                | Sixth degree |
| B     | 7                | Seventh degree |

### Quality Modifiers

| Chord | Nashville Number | Explanation |
|-------|------------------|-------------|
| C     | 1                | Major (no modifier) |
| Cm    | 1m               | Minor (m suffix) |
| Dm    | 2m               | Minor second |
| Am    | 6m               | Minor sixth |

### Accidentals

| Chord | Nashville Number | Explanation |
|-------|------------------|-------------|
| C#    | #1               | Sharp one |
| Db    | b2               | Flat two |
| Bb    | b7               | Flat seven |

---

## Common Progressions

### I-vi-ii-V (1-6m-2m-5)

**In C major:**
- Chords: C → Am → Dm → G
- Numbers: 1 → 6m → 2m → 5

**In F major:**
- Chords: F → Dm → Gm → C
- Numbers: 1 → 6m → 2m → 5

### I-IV-V (1-4-5)

**In C major:**
- Chords: C → F → G
- Numbers: 1 → 4 → 5

**In F major:**
- Chords: F → Bb → C
- Numbers: 1 → 4 → 5

### I-V-vi-IV (1-5-6m-4)

**In C major:**
- Chords: C → G → Am → F
- Numbers: 1 → 5 → 6m → 4

**In F major:**
- Chords: F → C → Dm → Bb
- Numbers: 1 → 5 → 6m → 4

---

## Implementation Details

### Chord Detection (app.py)

```python
def convert_chord_to_nashville(chord_name, key='C'):
    """
    Convert a chord name to Nashville Number System notation
    Returns simple numbers (1-7) with modifiers
    
    Examples:
    - C in key of C = "1"
    - Dm in key of C = "2m"
    - F in key of C = "4"
    - G in key of C = "5"
    - Am in key of C = "6m"
    """
    # ... implementation ...
```

### PDF Generator (index.js)

```javascript
// Display Nashville numbers below chord names
const nashvilleProgression = pattern.nashvilleProgression 
  ? pattern.nashvilleProgression.join('  →  ')
  : 'N/A';

doc.text(`(${nashvilleProgression})`, 25, yPos);
```

---

## Testing

### Expected Output

**Job with "Like The Dew" (F major):**

```
Pattern 1:
  Chords:  F → Dm → Gm → C
  Numbers: 1 → 6m → 2m → 5
  
Pattern 2:
  Chords:  F → Bb → C → F
  Numbers: 1 → 4 → 5 → 1
```

### Test Command

```bash
# Submit new job
curl -X POST https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev/jobs \
  -H "Content-Type: application/json" \
  -d '{"youtubeUrl": "https://www.youtube.com/watch?v=Q-RKhgsZu64"}'

# Get job ID from response, then check status
curl https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev/jobs/{JOB_ID}
```

### What to Look For

**In the diagnostic PDF:**
- ✅ Numbers instead of Roman numerals
- ✅ Quality modifiers (m for minor)
- ✅ Simple, readable notation
- ✅ No "!" characters

**Example:**
```
Pattern 1:
  F → Dm → Gm → C
  (1 → 6m → 2m → 5)  ✅ CORRECT

NOT:
  F → Dm → Gm → C
  (I → vi → ii → V)  ❌ OLD STYLE
```

---

## Advantages Over Roman Numerals

### 1. Simplicity
- **Nashville:** 1, 2m, 5
- **Roman:** I, ii, V

### 2. No Case Sensitivity
- **Nashville:** 1m (minor), 1 (major)
- **Roman:** i (minor), I (major)

### 3. Industry Standard
- Used in Nashville recording sessions
- Standard in country, pop, rock music
- Familiar to session musicians

### 4. Easier to Read
- Numbers are universally understood
- No need to remember Roman numeral rules
- Faster to parse visually

### 5. Better for Communication
- "Play a one-six-two-five" is clearer than "Play a one-six-two-five in Roman numerals"
- Works across languages
- Less ambiguous

---

## Migration Notes

### Old Jobs

Jobs created before this change will still have Roman numerals in their data. To see Nashville numbers, submit a **new job**.

### Backward Compatibility

The system still stores both:
- `progression`: Original chord names (F, Dm, Gm, C)
- `nashvilleProgression`: Nashville numbers (1, 6m, 2m, 5)

This allows for future flexibility if needed.

---

## Summary

**Change:** Roman numerals → Nashville numbers  
**Format:** 1, 2, 3, 4, 5, 6, 7 (with m for minor)  
**Status:** Building in GitHub Actions  
**ETA:** 3-5 minutes

**Benefits:**
- ✅ Simpler notation
- ✅ Industry standard
- ✅ Easier to read
- ✅ Better for musicians

**Next Steps:**
1. Wait for build to complete
2. Submit new job
3. Verify Nashville numbers in PDF
4. No more "!" characters!

---

**Build Status:** https://github.com/DannyWilsonCodeShop/music-transcription-app/actions
