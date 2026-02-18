#!/usr/bin/env python3
"""
Diagnostic: Why is "That's What I Like" detecting wrong key?
Expected: B♭ minor / D♭ major
Detected: G# major (A♭ major enharmonic)
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from chord_detection_v2 import (
    detect_tempo_and_beats,
    compute_beat_aligned_chromagram,
    detect_key_from_chromagram
)
import librosa

def main():
    audio_path = '../../public/04 That_s What I Like.m4a'
    
    print("=" * 80)
    print("DIAGNOSTIC: That's What I Like - Key Detection Issue")
    print("=" * 80)
    print("\nExpected: B♭ minor (A# minor) or D♭ major (C# major)")
    print("Previous detection: G# major (A♭ major)")
    print("=" * 80)
    
    # Load audio
    print("\nLoading audio...")
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Get timing
    print("Detecting tempo and beats...")
    timing_grid = detect_tempo_and_beats(audio_path)
    
    # Compute chromagram
    print("Computing chromagram...")
    chroma = librosa.feature.chroma_cqt(
        y=y,
        sr=sr,
        hop_length=int(sr * 20 / 1000),
        n_chroma=12,
        bins_per_octave=36
    )
    
    print(f"Chromagram shape: {chroma.shape}")
    
    # Analyze chroma distribution
    chroma_mean = np.mean(chroma, axis=1)
    chroma_mean = chroma_mean / np.sum(chroma_mean)
    
    pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    print("\nChroma distribution (average across song):")
    for i, pc in enumerate(pitch_classes):
        bar = '█' * int(chroma_mean[i] * 100)
        print(f"  {pc:3s}: {chroma_mean[i]:.3f} {bar}")
    
    # Expected notes for B♭ minor: B♭(A#), C, D♭(C#), E♭(D#), F, G♭(F#), A♭(G#)
    # Expected notes for D♭ major: D♭(C#), E♭(D#), F, G♭(F#), A♭(G#), B♭(A#), C
    
    print("\nExpected strong notes:")
    print("  B♭ minor: A#, C#, D#, F, F#, G#")
    print("  D♭ major: C#, D#, F, F#, G#, A#, C")
    
    print("\nActual strong notes (top 6):")
    top_indices = np.argsort(chroma_mean)[-6:][::-1]
    for idx in top_indices:
        print(f"  {pitch_classes[idx]}: {chroma_mean[idx]:.3f}")
    
    # Run key detection
    print("\n" + "=" * 80)
    print("Running key detection...")
    key_result = detect_key_from_chromagram(chroma, None)
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    # Check if detected notes match expected
    expected_notes_bb_minor = [10, 1, 3, 5, 6, 8]  # A#, C#, D#, F, F#, G#
    expected_notes_db_major = [1, 3, 5, 6, 8, 10, 0]  # C#, D#, F, F#, G#, A#, C
    
    print("\nNote presence analysis:")
    print(f"  A# (B♭): {chroma_mean[10]:.3f} - {'STRONG' if chroma_mean[10] > 0.1 else 'weak'}")
    print(f"  C#  (D♭): {chroma_mean[1]:.3f} - {'STRONG' if chroma_mean[1] > 0.1 else 'weak'}")
    print(f"  D# (E♭): {chroma_mean[3]:.3f} - {'STRONG' if chroma_mean[3] > 0.1 else 'weak'}")
    print(f"  F:       {chroma_mean[5]:.3f} - {'STRONG' if chroma_mean[5] > 0.1 else 'weak'}")
    print(f"  F# (G♭): {chroma_mean[6]:.3f} - {'STRONG' if chroma_mean[6] > 0.1 else 'weak'}")
    print(f"  G# (A♭): {chroma_mean[8]:.3f} - {'STRONG' if chroma_mean[8] > 0.1 else 'weak'}")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    
    if key_result.key in ['A#', 'C#'] and key_result.scale == 'minor':
        print("✓ Key detection is CORRECT!")
    elif key_result.key in ['C#', 'D#'] and key_result.scale == 'major':
        print("✓ Key detection is CORRECT (relative major)!")
    else:
        print(f"✗ Key detection is WRONG")
        print(f"  Detected: {key_result.key} {key_result.scale}")
        print(f"  Expected: A# minor or C# major")
        print(f"\n  Possible reasons:")
        print(f"  1. Drums/vocals polluting the chroma")
        print(f"  2. Key profile mismatch")
        print(f"  3. Song modulates or has ambiguous tonality")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
