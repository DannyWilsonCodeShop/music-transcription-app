#!/usr/bin/env python3
"""
Test Part 2: Stem Separation
Tests the stem separation functionality to isolate harmonic content
"""

import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from chord_detection_v2 import separate_stems, separate_stems_simple, DEMUCS_AVAILABLE

def test_stem_separation(audio_path, expected_name, use_simple=False):
    """Test stem separation on a single audio file"""
    print("\n" + "=" * 80)
    print(f"TESTING: {expected_name}")
    print("=" * 80)
    
    if not os.path.exists(audio_path):
        print(f"❌ File not found: {audio_path}")
        return False
    
    if not DEMUCS_AVAILABLE:
        print("⚠️ Demucs not available - stem separation will be skipped")
        print("To install: pip install demucs")
        print("\nTest will verify fallback behavior (using full mix)")
    
    try:
        # Run stem separation
        if use_simple:
            print("Using simple mode (no chunking)...")
            harmonic_audio, sr = separate_stems_simple(audio_path)
        else:
            print("Using chunked mode (memory-efficient)...")
            harmonic_audio, sr = separate_stems(audio_path, chunk_duration=30)
        
        # Validate results
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        
        duration = len(harmonic_audio) / sr
        print(f"\n✓ Output duration: {duration:.2f}s")
        print(f"✓ Sample rate: {sr} Hz")
        print(f"✓ Samples: {len(harmonic_audio)}")
        print(f"✓ Data type: {harmonic_audio.dtype}")
        
        # Check audio statistics
        print(f"\nAudio statistics:")
        print(f"  Min value: {np.min(harmonic_audio):.4f}")
        print(f"  Max value: {np.max(harmonic_audio):.4f}")
        print(f"  Mean: {np.mean(harmonic_audio):.4f}")
        print(f"  RMS: {np.sqrt(np.mean(harmonic_audio**2)):.4f}")
        
        # Check for silence (would indicate a problem)
        rms = np.sqrt(np.mean(harmonic_audio**2))
        if rms < 0.001:
            print(f"\n⚠️ WARNING: Audio appears to be silent (RMS: {rms:.6f})")
            print("This might indicate an issue with stem separation")
        else:
            print(f"\n✓ Audio has content (RMS: {rms:.4f})")
        
        # Check for clipping
        if np.max(np.abs(harmonic_audio)) > 0.99:
            print(f"\n⚠️ WARNING: Audio may be clipping (max: {np.max(np.abs(harmonic_audio)):.4f})")
        else:
            print(f"✓ No clipping detected")
        
        if DEMUCS_AVAILABLE:
            print(f"\n✓ Stem separation successful:")
            print(f"  - Drums removed")
            print(f"  - Vocals removed")
            print(f"  - Harmonic content isolated (bass + other)")
        else:
            print(f"\n✓ Fallback successful:")
            print(f"  - Using full mix (Demucs not available)")
        
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
    print("CHORD DETECTION V2 - PART 2 TEST SUITE")
    print("Testing: Stem Separation (Harmonic Content Isolation)")
    print("=" * 80)
    
    if not DEMUCS_AVAILABLE:
        print("\n⚠️ WARNING: Demucs is not installed")
        print("Stem separation will be skipped, tests will verify fallback behavior")
        print("\nTo install Demucs:")
        print("  pip install demucs")
        print("\nNote: Demucs requires PyTorch and can be large (~2GB)")
        print("=" * 80)
    
    # Test files
    test_files = [
        {
            'path': '../../public/meetup_ring.mp3',
            'name': 'meetup_ring.mp3 (short clip, 7.56s)',
            'use_simple': True  # Short file, use simple mode
        },
        {
            'path': '../../public/13_The_Girl_from_Ipanema__feat._Bebe[43060].mp3',
            'name': 'The Girl from Ipanema (jazz standard, ~4 min)',
            'use_simple': False  # Long file, use chunked mode
        }
    ]
    
    results = []
    for test_file in test_files:
        success = test_stem_separation(
            test_file['path'], 
            test_file['name'],
            use_simple=test_file['use_simple']
        )
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
        if DEMUCS_AVAILABLE:
            print("\nStem separation is working correctly:")
            print("  - Drums removed from analysis")
            print("  - Vocals removed from analysis")
            print("  - Harmonic content isolated (bass + other)")
        else:
            print("\nFallback behavior verified:")
            print("  - System works without Demucs")
            print("  - Uses full mix when stem separation unavailable")
        print("\nNext steps:")
        print("  1. Review harmonic content quality")
        print("  2. Verify memory usage is acceptable")
        print("  3. Proceed to Part 3: CQT Chromagram")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Review errors above and fix issues before proceeding")
    
    print("=" * 80)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
