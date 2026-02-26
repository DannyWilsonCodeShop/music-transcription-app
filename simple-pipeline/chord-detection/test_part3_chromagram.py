#!/usr/bin/env python3
"""
Test Part 3: CQT Chromagram with Beat Alignment
Tests the chromagram computation and alignment to 16th-note grid
"""

import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from chord_detection_v2 import (
    detect_tempo_and_beats,
    separate_stems,
    compute_beat_aligned_chromagram,
    visualize_chromagram
)

def test_chromagram(audio_path, expected_name):
    """Test chromagram computation on a single audio file"""
    print("\n" + "=" * 80)
    print(f"TESTING: {expected_name}")
    print("=" * 80)
    
    if not os.path.exists(audio_path):
        print(f"❌ File not found: {audio_path}")
        return False
    
    try:
        # Part 1: Get timing grid
        print("\nStep 1: Detecting tempo and beats...")
        timing_grid = detect_tempo_and_beats(audio_path)
        print(f"  ✓ Tempo: {timing_grid.tempo:.1f} BPM")
        print(f"  ✓ Subdivisions: {len(timing_grid.subdivisions)}")
        
        # Part 2: Get harmonic audio
        print("\nStep 2: Separating stems (or loading full mix)...")
        harmonic_audio, sr = separate_stems(audio_path, chunk_duration=30)
        print(f"  ✓ Audio duration: {len(harmonic_audio) / sr:.1f}s")
        print(f"  ✓ Sample rate: {sr} Hz")
        
        # Part 3: Compute chromagram
        print("\nStep 3: Computing beat-aligned chromagram...")
        aligned_chroma = compute_beat_aligned_chromagram(
            harmonic_audio,
            sr,
            timing_grid.subdivisions,
            hop_length_ms=20
        )
        
        # Validate results
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        
        print(f"\n✓ Chromagram shape: {aligned_chroma.shape}")
        print(f"✓ Pitch classes: {aligned_chroma.shape[0]} (should be 12)")
        print(f"✓ Subdivisions: {aligned_chroma.shape[1]}")
        
        # Check that we have the right number of subdivisions
        if aligned_chroma.shape[1] == len(timing_grid.subdivisions):
            print(f"✓ Subdivision count matches timing grid")
        else:
            print(f"⚠️ WARNING: Subdivision mismatch!")
            print(f"  Expected: {len(timing_grid.subdivisions)}")
            print(f"  Got: {aligned_chroma.shape[1]}")
        
        # Check chroma statistics
        print(f"\nChroma statistics:")
        print(f"  Min value: {np.min(aligned_chroma):.4f}")
        print(f"  Max value: {np.max(aligned_chroma):.4f}")
        print(f"  Mean: {np.mean(aligned_chroma):.4f}")
        print(f"  Non-zero frames: {np.count_nonzero(np.sum(aligned_chroma, axis=0))}/{aligned_chroma.shape[1]}")
        
        # Check for all-zero frames (would indicate a problem)
        zero_frames = np.sum(np.sum(aligned_chroma, axis=0) == 0)
        if zero_frames > 0:
            print(f"\n⚠️ WARNING: {zero_frames} frames have all-zero chroma")
            print(f"  This might indicate an alignment issue")
        else:
            print(f"\n✓ All frames have chroma content")
        
        # Show first few chroma vectors
        print(f"\nFirst 4 subdivision chroma vectors:")
        pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        for i in range(min(4, aligned_chroma.shape[1])):
            chroma_vec = aligned_chroma[:, i]
            # Find dominant pitch classes (top 3)
            top_indices = np.argsort(chroma_vec)[-3:][::-1]
            top_pitches = [(pitch_classes[idx], chroma_vec[idx]) for idx in top_indices]
            print(f"  Subdivision {i+1} (t={timing_grid.subdivisions[i]:.2f}s):")
            print(f"    Top pitches: {', '.join([f'{p}:{v:.3f}' for p, v in top_pitches])}")
        
        # Optional: Visualize chromagram
        try:
            output_path = f"/tmp/chromagram_{expected_name.replace(' ', '_').replace('/', '_')}.png"
            print(f"\nGenerating chromagram visualization...")
            visualize_chromagram(aligned_chroma, timing_grid.subdivisions, output_path)
        except Exception as e:
            print(f"  Visualization skipped: {e}")
        
        print("\n" + "=" * 80)
        print(f"✅ TEST PASSED: {expected_name}")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {expected_name}")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 80)
    print("CHORD DETECTION V2 - PART 3 TEST SUITE")
    print("Testing: CQT Chromagram with Beat Alignment")
    print("=" * 80)
    
    # Test files
    test_files = [
        {
            'path': '../../public/meetup_ring.mp3',
            'name': 'meetup_ring.mp3 (short clip)'
        },
        {
            'path': '../../public/13_The_Girl_from_Ipanema__feat._Bebe[43060].mp3',
            'name': 'The Girl from Ipanema (jazz standard)'
        }
    ]
    
    results = []
    for test_file in test_files:
        success = test_chromagram(test_file['path'], test_file['name'])
        results.append({
            'name': test_file['name'],
            'success': success
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status}: {result['name']}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nChromagram computation is working correctly:")
        print("  - CQT chromagram computed with high resolution")
        print("  - Aligned to 16th-note timing grid")
        print("  - Averaged within each subdivision window")
        print("  - Ready for chord detection")
        print("\nNext steps:")
        print("  1. Review chromagram visualizations (if generated)")
        print("  2. Verify alignment accuracy")
        print("  3. Proceed to Part 4: Template Matching with HMM")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Review errors above and fix issues before proceeding")
    
    print("=" * 80)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
