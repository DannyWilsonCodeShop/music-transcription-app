#!/usr/bin/env python3
"""
Diagnostic: Why are we only getting 11 chords?
Show the filtering process step by step
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from chord_detection_v2 import (
    detect_tempo_and_beats,
    separate_stems,
    compute_beat_aligned_chromagram,
    create_chord_templates,
    calculate_eighth_note_duration
)
import librosa

def main():
    audio_path = '../../public/04 That_s What I Like.m4a'
    
    print("=" * 80)
    print("DIAGNOSTIC: HMM Filtering Analysis")
    print("=" * 80)
    
    # Get timing
    print("\n1. Getting timing grid...")
    timing_grid = detect_tempo_and_beats(audio_path)
    print(f"   Tempo: {timing_grid.tempo:.1f} BPM")
    print(f"   Total subdivisions (16th notes): {len(timing_grid.subdivisions)}")
    print(f"   Song duration: {timing_grid.subdivisions[-1]:.1f}s")
    
    # Get audio (skip stem separation for speed)
    print("\n2. Loading audio (skipping stem separation for speed)...")
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Compute chromagram
    print("\n3. Computing chromagram...")
    aligned_chroma = compute_beat_aligned_chromagram(
        y, sr, timing_grid.subdivisions, hop_length_ms=20
    )
    
    # Template matching
    print("\n4. Template matching at each subdivision...")
    templates = create_chord_templates()
    
    raw_chords = []
    for i in range(aligned_chroma.shape[1]):
        chroma_vector = aligned_chroma[:, i]
        if np.sum(chroma_vector) > 0:
            chroma_vector = chroma_vector / np.sum(chroma_vector)
        
        # Find best matching chord
        best_chord = None
        best_similarity = -1
        for chord_name, template in templates.items():
            similarity = np.dot(chroma_vector, template) / (
                np.linalg.norm(chroma_vector) * np.linalg.norm(template) + 1e-10
            )
            if similarity > best_similarity:
                best_similarity = similarity
                best_chord = chord_name
        
        raw_chords.append(best_chord)
    
    print(f"   Raw detections: {len(raw_chords)} chords (one per subdivision)")
    
    # Count unique chords before HMM
    unique_before = len(set(raw_chords))
    print(f"   Unique chords detected: {unique_before}")
    
    # Count chord changes before HMM
    changes_before = sum(1 for i in range(1, len(raw_chords)) if raw_chords[i] != raw_chords[i-1])
    print(f"   Chord changes detected: {changes_before}")
    
    # Show first 50 raw detections
    print(f"\n   First 50 raw chord detections:")
    for i in range(min(50, len(raw_chords))):
        if i == 0 or raw_chords[i] != raw_chords[i-1]:
            print(f"      {i:4d}. {raw_chords[i]:8s} at {timing_grid.subdivisions[i]:.2f}s")
    
    # Simulate HMM smoothing effect
    print("\n5. After HMM smoothing (stay_prob=0.9)...")
    print("   HMM heavily favors staying on same chord")
    print("   This reduces rapid changes but may be too aggressive")
    
    # Simulate minimum duration filtering
    min_duration = calculate_eighth_note_duration(timing_grid.tempo)
    print(f"\n6. After minimum duration filter ({min_duration:.3f}s = 1/8 note)...")
    print(f"   Any chord shorter than {min_duration:.3f}s is merged with neighbors")
    
    # Count how many subdivisions per chord if we have 11 chords
    avg_subdivisions_per_chord = len(timing_grid.subdivisions) / 11
    avg_duration_per_chord = timing_grid.subdivisions[-1] / 11
    
    print(f"\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print(f"\nWith 11 chords for {timing_grid.subdivisions[-1]:.1f}s song:")
    print(f"  Average chord duration: {avg_duration_per_chord:.1f}s")
    print(f"  Average subdivisions per chord: {avg_subdivisions_per_chord:.0f}")
    print(f"  That's {avg_subdivisions_per_chord/4:.1f} beats per chord")
    
    print(f"\nProblem: HMM stay probability (0.9) is TOO HIGH")
    print(f"  - 90% chance of staying on same chord")
    print(f"  - Only 10% chance of changing")
    print(f"  - This works for jazz (long chords)")
    print(f"  - But NOT for pop/funk (frequent changes)")
    
    print(f"\nSolution: Lower HMM stay probability")
    print(f"  - Try 0.7 (70% stay, 30% change)")
    print(f"  - Or 0.6 for even more sensitivity")
    print(f"  - This will detect more chord changes")
    
    print(f"\nAlso: Minimum duration might be too aggressive")
    print(f"  - Current: {min_duration:.3f}s (1/8 note)")
    print(f"  - Could try 1/16 note for faster songs")
    print(f"  - Or make it genre-dependent")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
