#!/usr/bin/env python3
"""
Export the stem audio used for chord detection
This lets you hear exactly what the algorithm is analyzing
"""

import sys
import os
import soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))

from chord_detection_v2 import separate_stems

def export_stem(audio_path: str, output_path: str = None):
    """
    Export the harmonic stem (other) used for chord detection
    
    Args:
        audio_path: Input audio file
        output_path: Output WAV file (default: input_stem.wav)
    """
    if output_path is None:
        base = os.path.splitext(os.path.basename(audio_path))[0]
        output_path = f"{base}_harmonic_stem.wav"
    
    print("=" * 80)
    print("EXPORTING HARMONIC STEM")
    print("=" * 80)
    print(f"Input:  {audio_path}")
    print(f"Output: {output_path}")
    print("=" * 80)
    
    # Separate stems
    print("\nSeparating stems (this will take ~90 seconds)...")
    harmonic_audio, sr = separate_stems(audio_path, chunk_duration=30)
    
    # Save to WAV
    print(f"\nSaving harmonic stem to: {output_path}")
    sf.write(output_path, harmonic_audio, sr)
    
    duration = len(harmonic_audio) / sr
    print(f"\n✓ Stem exported successfully!")
    print(f"  Duration: {duration:.1f}s")
    print(f"  Sample rate: {sr} Hz")
    print(f"  Samples: {len(harmonic_audio)}")
    print(f"\nThis is the 'other' stem containing:")
    print("  ✓ Piano, guitar, keys, strings, synths")
    print("  ✗ Drums (removed)")
    print("  ✗ Bass (removed)")
    print("  ✗ Vocals (removed)")
    print(f"\nYou can now listen to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_stem_audio.py <audio_file> [output.wav]")
        print("Example: python export_stem_audio.py '../../public/04 That_s What I Like.m4a'")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    export_stem(audio_path, output_path)
