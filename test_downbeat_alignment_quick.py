#!/usr/bin/env python3
"""
Quick test: Check if confirmed downbeat fixes measure alignment
Skip stem separation to test faster
"""

import sys
sys.path.insert(0, 'simple-pipeline/chord-detection')

import librosa
import numpy as np

# Test audio file
audio_path = "public/04 That_s What I Like.m4a"

# Confirmed downbeat from user adjustment
confirmed_downbeat = 2.089795918367347
confirmed_time_signature = "4/4"

print("=" * 80)
print("QUICK TEST: DOWNBEAT ALIGNMENT")
print("=" * 80)
print(f"Audio: {audio_path}")
print(f"Confirmed downbeat: {confirmed_downbeat:.3f}s")
print()

# Load audio and detect tempo
print("Loading audio and detecting tempo...")
y, sr = librosa.load(audio_path, sr=22050)
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
tempo = float(tempo) if not isinstance(tempo, float) else tempo
beat_times = librosa.frames_to_time(beat_frames, sr=sr)

print(f"✓ Tempo: {tempo:.1f} BPM")
print(f"✓ Beats detected: {len(beat_times)}")
print(f"✓ First auto-detected beat: {beat_times[0]:.3f}s")
print()

# Calculate beat duration
beat_duration = 60.0 / tempo
beats_per_measure = 4

print("=" * 80)
print("COMPARISON: AUTO-DETECTED vs CONFIRMED")
print("=" * 80)

# Auto-detected first beat
auto_first_beat = beat_times[0]
difference = confirmed_downbeat - auto_first_beat
beats_off = difference / beat_duration

print(f"Auto-detected first beat: {auto_first_beat:.3f}s")
print(f"Confirmed downbeat:       {confirmed_downbeat:.3f}s")
print(f"Difference:               {difference:.3f}s")
print(f"Beats off:                {beats_off:.1f} beats")
print()

if abs(beats_off) >= 0.5:
    beat_position = int(round(beats_off)) + 1
    print(f"⚠️  The auto-detected first beat was actually BEAT {beat_position} of the measure!")
    print(f"    This means all measure numbers were off by {int(round(beats_off))} beats.")
else:
    print(f"✓ Auto-detected beat was close to the downbeat (within 0.5 beats)")

print()
print("=" * 80)
print("MEASURE ALIGNMENT DEMONSTRATION")
print("=" * 80)

# Show first 10 measures with both alignments
print("\nUsing AUTO-DETECTED first beat (WRONG):")
print("-" * 80)
for measure in range(1, 11):
    measure_start = auto_first_beat + (measure - 1) * beats_per_measure * beat_duration
    print(f"Measure {measure:2d}: starts at {measure_start:6.2f}s")

print("\nUsing CONFIRMED downbeat (CORRECT):")
print("-" * 80)
for measure in range(1, 11):
    measure_start = confirmed_downbeat + (measure - 1) * beats_per_measure * beat_duration
    print(f"Measure {measure:2d}: starts at {measure_start:6.2f}s")

print()
print("=" * 80)
print("IMPACT ON CHORD PLACEMENT")
print("=" * 80)

# Simulate some chord times
example_chord_times = [2.5, 3.8, 5.2, 6.9, 8.3, 10.1, 11.5, 13.2]

print("\nExample chord times and their measure placement:")
print("-" * 80)
print(f"{'Chord Time':>12} | {'Wrong Measure':>14} | {'Correct Measure':>16} | {'Difference':>12}")
print("-" * 80)

for chord_time in example_chord_times:
    # Wrong: using auto-detected first beat
    time_from_auto = chord_time - auto_first_beat
    wrong_measure = int(time_from_auto / (beat_duration * beats_per_measure)) + 1
    
    # Correct: using confirmed downbeat
    time_from_confirmed = chord_time - confirmed_downbeat
    correct_measure = int(time_from_confirmed / (beat_duration * beats_per_measure)) + 1
    
    diff = correct_measure - wrong_measure
    
    print(f"{chord_time:11.2f}s | Measure {wrong_measure:6d} | Measure {correct_measure:8d} | {diff:+11d}")

print()
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()

if abs(beats_off) >= 1.0:
    print("🔴 CRITICAL ISSUE FOUND:")
    print(f"   The auto-detected first beat is {abs(beats_off):.1f} beats off from the true downbeat.")
    print(f"   This causes ALL measure numbers to be incorrect by {int(round(beats_off))} beats.")
    print()
    print("✅ SOLUTION:")
    print("   Using the confirmed downbeat will fix all measure alignments.")
    print("   All chords will be placed in the correct measures.")
else:
    print("✓ Auto-detection was accurate enough.")
    print("  Confirmed downbeat provides minor improvement.")

print()
print("=" * 80)
