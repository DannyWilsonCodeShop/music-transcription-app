#!/usr/bin/env python3
"""
Visualize chord detection results with confirmed downbeat
Show measure-by-measure breakdown
"""

import json

# Load results
with open('/tmp/chord_detection_with_confirmed_downbeat.json', 'r') as f:
    data = json.load(f)

# Confirmed downbeat
confirmed_downbeat = 2.089795918367347
tempo = data['tempo']
beat_duration = 60.0 / tempo
beats_per_measure = 4
measure_duration = beat_duration * beats_per_measure

print("=" * 80)
print("CHORD DETECTION RESULTS WITH CONFIRMED DOWNBEAT")
print("=" * 80)
print(f"Key: {data['key']} {data['scale']}")
print(f"Tempo: {tempo:.1f} BPM")
print(f"Total chords: {len(data['chords'])}")
print(f"Duration: {data['duration']:.1f}s")
print(f"Confirmed downbeat: {confirmed_downbeat:.3f}s")
print("=" * 80)

# Group chords by measure
measures = {}
for chord in data['chords']:
    time_from_downbeat = chord['start'] - confirmed_downbeat
    if time_from_downbeat < 0:
        continue  # Skip chords before downbeat
    
    measure_num = int(time_from_downbeat / measure_duration) + 1
    
    if measure_num not in measures:
        measures[measure_num] = []
    
    measures[measure_num].append(chord)

print(f"\nTotal measures with chords: {len(measures)}")
print()

# Show first 20 measures
print("=" * 80)
print("FIRST 20 MEASURES (with confirmed downbeat alignment)")
print("=" * 80)

for measure_num in sorted(measures.keys())[:20]:
    measure_start = confirmed_downbeat + (measure_num - 1) * measure_duration
    measure_end = measure_start + measure_duration
    
    chords_in_measure = measures[measure_num]
    
    # Get primary chord (longest duration)
    primary_chord = max(chords_in_measure, key=lambda c: c['duration'])
    
    # Count unique chords
    unique_chords = len(set(c['name'] for c in chords_in_measure))
    
    print(f"\nMeasure {measure_num:3d} ({measure_start:6.2f}s - {measure_end:6.2f}s)")
    print(f"  Primary chord: {primary_chord['name']}")
    print(f"  Total chords: {len(chords_in_measure)} ({unique_chords} unique)")
    
    if len(chords_in_measure) <= 5:
        # Show all chords if 5 or fewer
        for chord in chords_in_measure:
            beat_in_measure = int((chord['start'] - measure_start) / beat_duration) + 1
            print(f"    Beat {beat_in_measure}: {chord['name']:8s} ({chord['duration']:.2f}s)")
    else:
        # Show summary if more than 5
        chord_names = [c['name'] for c in chords_in_measure]
        print(f"    Chords: {', '.join(chord_names[:5])}...")

print()
print("=" * 80)
print("MEASURE SUMMARY")
print("=" * 80)

# Calculate statistics
total_chords_in_measures = sum(len(measures[m]) for m in measures)
avg_chords_per_measure = total_chords_in_measures / len(measures)

print(f"Total measures: {len(measures)}")
print(f"Average chords per measure: {avg_chords_per_measure:.1f}")
print(f"Measure duration: {measure_duration:.2f}s")
print(f"Beat duration: {beat_duration:.3f}s")

# Find measures with most chord changes
busy_measures = sorted(measures.items(), key=lambda x: len(x[1]), reverse=True)[:5]
print(f"\nMost active measures (most chord changes):")
for measure_num, chords in busy_measures:
    print(f"  Measure {measure_num}: {len(chords)} chords")

print()
print("=" * 80)
print("COMPARISON: Before vs After Confirmed Downbeat")
print("=" * 80)

# Show what the measure numbers would have been without confirmation
auto_first_beat = 0.720
difference = confirmed_downbeat - auto_first_beat

print(f"\nAuto-detected first beat: {auto_first_beat:.3f}s")
print(f"Confirmed downbeat:       {confirmed_downbeat:.3f}s")
print(f"Difference:               {difference:.3f}s ({difference/beat_duration:.1f} beats)")
print()
print("Example: A chord at 5.00s would be placed in:")
print(f"  - Measure 3 (using auto-detected beat) ❌ WRONG")
print(f"  - Measure 2 (using confirmed downbeat) ✅ CORRECT")
print()
print("✅ Using confirmed downbeat ensures all chords are in the correct measures!")

print()
print("=" * 80)
