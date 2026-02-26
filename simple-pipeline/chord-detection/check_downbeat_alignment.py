#!/usr/bin/env python3
"""
Check if beat detection is aligned to the actual downbeat
"""

import sys
import librosa
import numpy as np

sys.path.insert(0, '.')
from chord_detection_v2 import detect_tempo_and_beats

def check_downbeat_alignment(audio_path: str):
    """
    Check if the first detected beat aligns with the actual downbeat
    """
    print("=" * 80)
    print("DOWNBEAT ALIGNMENT CHECK")
    print("=" * 80)
    
    # Load audio
    print(f"\nLoading audio: {audio_path}")
    y, sr = librosa.load(audio_path, sr=22050)
    duration = librosa.get_duration(y=y, sr=sr)
    print(f"Duration: {duration:.2f}s")
    
    # Detect beats
    print("\nDetecting beats...")
    timing_grid = detect_tempo_and_beats(audio_path)
    
    print(f"\nFirst 10 beats:")
    for i in range(min(10, len(timing_grid.beats))):
        print(f"  Beat {i+1}: {timing_grid.beats[i]:.3f}s")
    
    print(f"\nFirst beat starts at: {timing_grid.beats[0]:.3f}s")
    print(f"This is {timing_grid.beats[0] * 1000:.0f}ms into the song")
    
    # Check if there's significant audio before first beat
    first_beat_sample = int(timing_grid.beats[0] * sr)
    pre_beat_audio = y[:first_beat_sample]
    pre_beat_energy = np.sum(np.abs(pre_beat_audio))
    total_energy = np.sum(np.abs(y))
    pre_beat_percentage = (pre_beat_energy / total_energy) * 100
    
    print(f"\nAudio energy before first beat: {pre_beat_percentage:.2f}% of total")
    
    if pre_beat_percentage > 1.0:
        print("⚠️  WARNING: Significant audio before first beat!")
        print("   This suggests the first beat might not be the downbeat.")
        print("   The song might have an intro or pickup notes.")
    else:
        print("✓ First beat appears to be at or near the start of the song")
    
    # Check beat consistency
    print(f"\nBeat intervals (first 20):")
    intervals = np.diff(timing_grid.beats[:20])
    print(f"  Mean: {np.mean(intervals):.3f}s")
    print(f"  Std:  {np.std(intervals):.3f}s")
    print(f"  Min:  {np.min(intervals):.3f}s")
    print(f"  Max:  {np.max(intervals):.3f}s")
    
    if np.std(intervals) > 0.05:
        print("⚠️  WARNING: Beat intervals are inconsistent!")
        print("   This might indicate beat tracking errors.")
    else:
        print("✓ Beat intervals are consistent")
    
    # Check subdivision alignment
    print(f"\nFirst 10 subdivisions (16th notes):")
    for i in range(min(10, len(timing_grid.subdivisions))):
        print(f"  Subdivision {i+1}: {timing_grid.subdivisions[i]:.3f}s")
    
    print(f"\nFirst subdivision starts at: {timing_grid.subdivisions[0]:.3f}s")
    
    # Recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    if timing_grid.beats[0] > 0.5:
        print("⚠️  First beat is significantly delayed ({:.3f}s)".format(timing_grid.beats[0]))
        print("   Consider:")
        print("   1. Check if song has intro/pickup that should be excluded")
        print("   2. Manually adjust beat offset if needed")
        print("   3. Use librosa's beat tracking with different parameters")
    elif pre_beat_percentage > 1.0:
        print("⚠️  Audio exists before first beat")
        print("   The beat tracker might be missing the true downbeat")
        print("   Consider using downbeat detection (librosa.beat.beat_track with downbeat detection)")
    else:
        print("✓ Beat alignment looks good!")
        print("  First beat is at {:.3f}s with minimal pre-beat audio".format(timing_grid.beats[0]))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_downbeat_alignment.py <audio_file>")
        sys.exit(1)
    
    check_downbeat_alignment(sys.argv[1])
