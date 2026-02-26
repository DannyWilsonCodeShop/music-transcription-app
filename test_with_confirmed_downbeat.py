#!/usr/bin/env python3
"""
Test chord detection with confirmed downbeat
Compare results with and without confirmed downbeat
"""

import sys
sys.path.insert(0, 'simple-pipeline/chord-detection')

from chord_detection_v2 import detect_chords_complete
import json

# Test audio file
audio_path = "public/04 That_s What I Like.m4a"

# Confirmed downbeat from user adjustment
confirmed_downbeat = 2.089795918367347
confirmed_time_signature = "4/4"

print("=" * 80)
print("TESTING CHORD DETECTION WITH CONFIRMED DOWNBEAT")
print("=" * 80)
print(f"Audio: {audio_path}")
print(f"Confirmed downbeat: {confirmed_downbeat:.3f}s")
print(f"Confirmed time signature: {confirmed_time_signature}")
print("=" * 80)

# Run chord detection WITH confirmed downbeat
print("\n🎯 Running chord detection WITH confirmed downbeat...")
results_with_downbeat = detect_chords_complete(
    audio_path,
    confirmed_downbeat=confirmed_downbeat,
    confirmed_time_signature=confirmed_time_signature
)

print("\n" + "=" * 80)
print("RESULTS WITH CONFIRMED DOWNBEAT")
print("=" * 80)
print(f"Tempo: {results_with_downbeat['tempo']:.1f} BPM")
print(f"Time signature: {results_with_downbeat['time_signature']}")
print(f"Key: {results_with_downbeat['key']} {results_with_downbeat['scale']}")
print(f"Total chords: {len(results_with_downbeat['chords'])}")
print(f"Duration: {results_with_downbeat['duration']:.1f}s")

# Show first 20 chords with measure numbers
print("\n📊 First 20 chords with measure numbers:")
print("-" * 80)

beat_duration = 60.0 / results_with_downbeat['tempo']
beats_per_measure = 4

for i, chord in enumerate(results_with_downbeat['chords'][:20]):
    # Calculate measure number from confirmed downbeat
    time_from_downbeat = chord['start'] - confirmed_downbeat
    measure_num = int(time_from_downbeat / (beat_duration * beats_per_measure)) + 1
    beat_in_measure = int((time_from_downbeat % (beat_duration * beats_per_measure)) / beat_duration) + 1
    
    print(f"{i+1:3d}. Measure {measure_num:3d}, Beat {beat_in_measure} | "
          f"{chord['name']:8s} | {chord['start']:6.2f}s - {chord['end']:6.2f}s | "
          f"Duration: {chord['duration']:.2f}s")

# Save results
output_file = "/tmp/chord_detection_with_confirmed_downbeat.json"
with open(output_file, 'w') as f:
    json.dump(results_with_downbeat, f, indent=2)

print(f"\n✅ Results saved to: {output_file}")

# Compare with auto-detected downbeat
print("\n" + "=" * 80)
print("COMPARISON: AUTO-DETECTED vs CONFIRMED DOWNBEAT")
print("=" * 80)

# The auto-detected first beat was 0.720s (from previous session)
auto_detected_first_beat = 0.720
difference = confirmed_downbeat - auto_detected_first_beat

print(f"Auto-detected first beat: {auto_detected_first_beat:.3f}s")
print(f"Confirmed downbeat:       {confirmed_downbeat:.3f}s")
print(f"Difference:               {difference:.3f}s ({difference/beat_duration:.1f} beats)")
print(f"\nThis means the auto-detected first beat was actually beat {int(difference/beat_duration) + 1} of the measure!")

print("\n" + "=" * 80)
print("TESTING COMPLETE")
print("=" * 80)
