# Note Attack Detection - How It Works

## Concept: Attacks vs. Sustained Notes

**Attack**: When a new note is played (plucked, struck, articulated)
**Sustained**: When a note continues ringing (tied, held)

We only show **attacks** in the output, not sustained notes.

## Detection Logic

A note is considered an **attack** if:

1. **Pitch changed** - Different note than previous
2. **Gap in time** - Silence (>50ms) before this note
3. **Volume increase** - Re-attack of same note (velocity increase >30%)

## Examples

### Example 1: Whole Notes (1 attack per measure)

**Audio**: `Bb----------|Eb----------|Gb----------|F----------|`

**Detected attacks**: 4 notes total (one per measure)

**Output**:
```
Measure 1: 1  |  (Bb - whole note)
Measure 2: 4  |  (Eb - whole note)
Measure 3: 6  |  (Gb - whole note)
Measure 4: 5  |  (F - whole note)
```

### Example 2: Quarter Notes (4 attacks per measure)

**Audio**: `Bb Bb Bb Bb|Eb Eb Eb Eb|`

**Detected attacks**: 8 notes (4 per measure)

**Output**:
```
Measure 1: 1 1 1 1  |  (Bb Bb Bb Bb - 4 quarter notes)
Measure 2: 4 4 4 4  |  (Eb Eb Eb Eb - 4 quarter notes)
```

### Example 3: Eighth Notes (8 attacks per measure)

**Audio**: `Bb Bb Bb Bb Bb Bb Bb Bb|`

**Detected attacks**: 8 notes

**Output**:
```
Measure 1: 1 1 1 1 1 1 1 1  |  (Bb - 8 eighth notes)
```

### Example 4: Syncopated Rhythm (variable attacks)

**Audio**: `Bb--Eb-Gb-F-|` (syncopated, not on every beat)

**Detected attacks**: 4 notes (not evenly spaced)

**Output**:
```
Measure 1: 1 . . 4 . 6 . 5  |  (Bb on 1, Eb on 2.5, Gb on 3.5, F on 4.5)
```

Where `.` = no attack on that 16th note position

### Example 5: Sixteenth Notes (16 attacks per measure)

**Audio**: `Bb Bb Bb Bb Bb Bb Bb Bb Bb Bb Bb Bb Bb Bb Bb Bb|`

**Detected attacks**: 16 notes

**Output**:
```
Measure 1: 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1  |  (Bb - 16 sixteenth notes)
```

## Real-World Example: "That's What I Like"

**Tempo**: 134 BPM
**Time Signature**: 4/4
**Key**: Bb minor (Db major)

**Typical bass pattern** (verse):
```
Audio timeline:
Beat:     1   2   3   4   |
Note:     Bb  .   Bb  .   |  (two attacks per measure)
```

**Output**:
```
Measure 1: 1 . 1 .  |  (Bb on beat 1, Bb on beat 3)
Measure 2: 4 . 4 .  |  (Eb on beat 1, Eb on beat 3)
Measure 3: 6 . 6 .  |  (Gb on beat 1, Gb on beat 3)
Measure 4: 5 . 5 .  |  (F on beat 1, F on beat 3)
```

Or simplified (showing only attacks):
```
Measure 1: 1 1  |  (Bb Bb - 2 attacks)
Measure 2: 4 4  |  (Eb Eb - 2 attacks)
Measure 3: 6 6  |  (Gb Gb - 2 attacks)
Measure 4: 5 5  |  (F F - 2 attacks)
```

## Attack Detection Algorithm

```python
def is_note_attack(current_note, previous_note):
    """
    Determine if current note is a new attack
    """
    # First note is always an attack
    if previous_note is None:
        return True
    
    # Different pitch = new note = attack
    if current_note.pitch != previous_note.pitch:
        return True
    
    # Gap in time = silence = new attack
    gap = current_note.start - previous_note.end
    if gap > 0.05:  # 50ms silence
        return True
    
    # Volume increase = re-attack of same note
    if current_note.velocity > previous_note.velocity * 1.3:
        return True
    
    # Otherwise, it's a sustained note (tie/hold)
    return False
```

## Why This Matters

### Without Attack Detection:
```
Measure 1: 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1  |  (shows every 16th note position)
```
This is wrong - the bass isn't playing 16 notes, it's holding one note!

### With Attack Detection:
```
Measure 1: 1  |  (shows only the attack - one whole note)
```
This is correct - shows what the bassist actually played.

## Edge Cases

### Case 1: Repeated Notes (Staccato)
**Audio**: `Bb Bb Bb Bb` (each note clearly separated)
**Detection**: 4 attacks (gap between each note)
**Output**: `1 1 1 1`

### Case 2: Tied Notes (Legato)
**Audio**: `Bb-------` (one long note)
**Detection**: 1 attack (no gaps, same pitch)
**Output**: `1`

### Case 3: Re-attacked Same Note
**Audio**: `Bb--Bb--` (same note, but re-plucked)
**Detection**: 2 attacks (volume increase on second Bb)
**Output**: `1 1`

### Case 4: Slide/Glissando
**Audio**: `Bb~Eb` (slide from Bb to Eb)
**Detection**: 2 attacks (pitch changed)
**Output**: `1 4`

## Output Format Options

### Option A: Show All 16th Note Positions
```
Measure 1: 1 . . . 1 . . . 1 . . . 1 . . .  |
           ^       ^       ^       ^
           attacks (dots = no attack)
```

### Option B: Show Only Attacks (Compact)
```
Measure 1: 1 1 1 1  |  (4 quarter note attacks)
```

### Option C: Show Attacks with Rhythm Notation
```
Measure 1: 1(q) 1(q) 1(q) 1(q)  |  (q = quarter note)
Measure 2: 4(h) 4(h)  |  (h = half note)
```

## Implementation Status

- ✅ Pitch change detection
- ✅ Gap detection (silence)
- ✅ Volume increase detection (re-attack)
- ✅ Quantization to 16th note grid
- ✅ Measure grouping
- ✅ Attack counting per measure
- ⏳ Rhythm notation (quarter, eighth, etc.) - TODO

## Testing

To verify attack detection is working:

1. **Test with whole notes** - Should show 1 attack per measure
2. **Test with quarter notes** - Should show 4 attacks per measure
3. **Test with repeated notes** - Should show each attack separately
4. **Test with tied notes** - Should show only the first attack

Example test:
```python
# Whole note (should detect 1 attack)
assert len(measure['notes']) == 1

# Quarter notes (should detect 4 attacks)
assert len(measure['notes']) == 4

# Sixteenth notes (should detect 16 attacks)
assert len(measure['notes']) == 16
```
