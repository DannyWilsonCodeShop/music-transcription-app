#!/usr/bin/env python3
"""
Test Basic Pitch (Spotify) for chord detection
Free and open source - no API key needed!
"""

import os
import sys
import numpy as np
from collections import defaultdict

# Test audio file
TEST_AUDIO = "public/meetup_ring.mp3"

if not os.path.exists(TEST_AUDIO):
    print(f"❌ Error: Test audio file not found: {TEST_AUDIO}")
    sys.exit(1)

print("🎵 Testing Basic Pitch (Spotify)")
print("=" * 60)
print(f"Audio file: {TEST_AUDIO}")
print()

# Check if basic-pitch is installed
try:
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
    print("✓ basic-pitch is installed")
except ImportError:
    print("❌ basic-pitch not installed")
    print("\nInstalling basic-pitch...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "basic-pitch"])
    print("✓ Installation complete")
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH

print()

# Step 1: Predict notes from audio
print("1. Analyzing audio with Basic Pitch...")
print("-" * 60)

try:
    model_output, midi_data, note_events = predict(
        TEST_AUDIO,
        ICASSP_2022_MODEL_PATH
    )
    
    print(f"✓ Analysis complete")
    print(f"  Notes detected: {len(note_events)}")
    print()
    
except Exception as e:
    print(f"❌ Error during analysis: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Convert MIDI to chords
print("2. Converting notes to chords...")
print("-" * 60)

def midi_to_chord_name(midi_notes):
    """
    Convert a set of MIDI note numbers to a chord name
    
    Args:
        midi_notes: list of MIDI note numbers (e.g., [60, 64, 67] = C major)
    
    Returns:
        chord name (e.g., "C", "Dm", "F")
    """
    if not midi_notes:
        return None
    
    # Note names
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # Get unique pitch classes (0-11)
    pitch_classes = sorted(set(note % 12 for note in midi_notes))
    
    if len(pitch_classes) < 2:
        # Single note - just return the note name
        root_pc = pitch_classes[0]
        return note_names[root_pc]
    
    # Find root (lowest note)
    root_pc = pitch_classes[0]
    root_name = note_names[root_pc]
    
    # Calculate intervals from root
    intervals = [(pc - root_pc) % 12 for pc in pitch_classes]
    intervals_set = set(intervals)
    
    # Chord templates
    # Major: root, major third (4), perfect fifth (7)
    if 4 in intervals_set and 7 in intervals_set:
        return root_name
    
    # Minor: root, minor third (3), perfect fifth (7)
    if 3 in intervals_set and 7 in intervals_set:
        return root_name + 'm'
    
    # Diminished: root, minor third (3), diminished fifth (6)
    if 3 in intervals_set and 6 in intervals_set:
        return root_name + 'dim'
    
    # Augmented: root, major third (4), augmented fifth (8)
    if 4 in intervals_set and 8 in intervals_set:
        return root_name + 'aug'
    
    # Dominant 7th: root, major third (4), perfect fifth (7), minor seventh (10)
    if 4 in intervals_set and 7 in intervals_set and 10 in intervals_set:
        return root_name + '7'
    
    # Major 7th: root, major third (4), perfect fifth (7), major seventh (11)
    if 4 in intervals_set and 7 in intervals_set and 11 in intervals_set:
        return root_name + 'maj7'
    
    # Minor 7th: root, minor third (3), perfect fifth (7), minor seventh (10)
    if 3 in intervals_set and 7 in intervals_set and 10 in intervals_set:
        return root_name + 'm7'
    
    # Sus4: root, perfect fourth (5), perfect fifth (7)
    if 5 in intervals_set and 7 in intervals_set and 4 not in intervals_set:
        return root_name + 'sus4'
    
    # Sus2: root, major second (2), perfect fifth (7)
    if 2 in intervals_set and 7 in intervals_set and 4 not in intervals_set:
        return root_name + 'sus2'
    
    # Default: just return root if we can't identify the chord
    return root_name

def notes_to_chords(note_events, time_window=0.5):
    """
    Convert note events to chord progression
    
    Args:
        note_events: list of (start_time, end_time, pitch, amplitude) tuples
        time_window: time window in seconds to group notes into chords
    
    Returns:
        list of chord dictionaries with timing
    """
    if not note_events:
        return []
    
    # Group notes by time windows
    time_buckets = defaultdict(list)
    
    for start_time, end_time, pitch, amplitude in note_events:
        # Round to nearest time window
        bucket = round(start_time / time_window) * time_window
        time_buckets[bucket].append(int(pitch))
    
    # Convert each time bucket to a chord
    chords = []
    sorted_times = sorted(time_buckets.keys())
    
    for i, time in enumerate(sorted_times):
        notes = time_buckets[time]
        chord_name = midi_to_chord_name(notes)
        
        if chord_name:
            # Calculate duration (until next chord or end)
            if i < len(sorted_times) - 1:
                duration = sorted_times[i + 1] - time
            else:
                # Last chord - estimate duration
                duration = 2.0
            
            chords.append({
                'chord': chord_name,
                'start': round(time, 2),
                'duration': round(duration, 2),
                'notes': sorted(set(notes))
            })
    
    # Consolidate consecutive identical chords
    consolidated = []
    if chords:
        current = chords[0].copy()
        
        for i in range(1, len(chords)):
            if chords[i]['chord'] == current['chord']:
                # Extend duration
                current['duration'] += chords[i]['duration']
            else:
                # Save current and start new
                consolidated.append(current)
                current = chords[i].copy()
        
        # Add last chord
        consolidated.append(current)
    
    return consolidated

# Convert notes to chords
chords = notes_to_chords(note_events, time_window=0.5)

print(f"✓ Chord conversion complete")
print(f"  Chords detected: {len(chords)}")
print()

# Step 3: Display results
print("=" * 60)
print("CHORD DETECTION RESULTS")
print("=" * 60)
print()

if chords:
    print(f"🎸 Total chords: {len(chords)}")
    print()
    print("First 20 chords:")
    for i, chord in enumerate(chords[:20], 1):
        print(f"  {i:2d}. {chord['chord']:8s} at {chord['start']:6.1f}s (duration: {chord['duration']:.1f}s)")
    
    if len(chords) > 20:
        print(f"  ... and {len(chords) - 20} more chords")
    
    print()
    
    # Chord statistics
    chord_counts = defaultdict(int)
    for chord in chords:
        chord_counts[chord['chord']] += 1
    
    print("Most common chords:")
    sorted_chords = sorted(chord_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (chord, count) in enumerate(sorted_chords[:10], 1):
        print(f"  {i:2d}. {chord:8s} - {count} times")
    
    print()
    
    # Save results
    import json
    output_file = "basic-pitch-result.json"
    with open(output_file, 'w') as f:
        json.dump({
            'chords': chords,
            'totalChords': len(chords),
            'uniqueChords': len(chord_counts),
            'model': 'basic-pitch-spotify'
        }, f, indent=2)
    
    print(f"📄 Results saved to: {output_file}")
    
else:
    print("⚠️  No chords detected")

print()
print("=" * 60)
print("✅ TEST COMPLETE!")
print("=" * 60)
print()
print("Next steps:")
print("1. Review chord accuracy")
print("2. Compare with current system (librosa + essentia)")
print("3. If good, integrate into pipeline")
print("4. If not good, try Omnizart")
print()
print("Pros of Basic Pitch:")
print("  ✓ Free and open source")
print("  ✓ No API key needed")
print("  ✓ Runs locally (no rate limits)")
print("  ✓ Good accuracy for polyphonic audio")
print()
print("Cons:")
print("  ⚠ Chord detection is simplified (may miss complex chords)")
print("  ⚠ May need refinement for better accuracy")
