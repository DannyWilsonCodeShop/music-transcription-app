#!/usr/bin/env python3
"""
Test Part 1: Tempo & Beat Detection
Tests the new chord_detection_v2.py tempo and beat detection functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from chord_detection_v2 import (
    detect_tempo_and_beats,
    calculate_eighth_note_duration,
    calculate_sixteenth_note_duration
)

def test_audio_file(audio_path, expected_name):
    """Test tempo detection on a single audio file"""
    print("\n" + "=" * 80)
    print(f"TESTING: {expected_name}")
    print("=" * 80)
    
    if not os.path.exists(audio_path):
        print(f"❌ File not found: {audio_path}")
        return False
    
    try:
        # Run tempo and beat detection
        timing_grid = detect_tempo_and_beats(audio_path)
        
        # Validate results
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        
        print(f"\n✓ Tempo: {timing_grid.tempo:.1f} BPM")
        print(f"✓ Time Signature: {timing_grid.time_signature}")
        print(f"✓ Beats per measure: {timing_grid.beats_per_measure}")
        print(f"✓ Total beats: {len(timing_grid.beats)}")
        print(f"✓ Total subdivisions (16th notes): {len(timing_grid.subdivisions)}")
        
        # Calculate durations
        eighth_duration = calculate_eighth_note_duration(timing_grid.tempo)
        sixteenth_duration = calculate_sixteenth_note_duration(timing_grid.tempo)
        
        print(f"\n✓ 1/8 note duration: {eighth_duration:.3f}s")
        print(f"✓ 1/16 note duration: {sixteenth_duration:.3f}s")
        
        # Show first few beats and subdivisions
        print(f"\nFirst 8 beats (seconds):")
        for i, beat in enumerate(timing_grid.beats[:8]):
            print(f"  Beat {i+1}: {beat:.3f}s")
        
        print(f"\nFirst 16 subdivisions (16th notes):")
        for i, sub in enumerate(timing_grid.subdivisions[:16]):
            print(f"  16th {i+1}: {sub:.3f}s")
        
        # Calculate average subdivision interval
        if len(timing_grid.subdivisions) > 1:
            avg_interval = sum(
                timing_grid.subdivisions[i+1] - timing_grid.subdivisions[i]
                for i in range(len(timing_grid.subdivisions) - 1)
            ) / (len(timing_grid.subdivisions) - 1)
            print(f"\nAverage subdivision interval: {avg_interval:.3f}s")
            print(f"Expected 16th note duration: {sixteenth_duration:.3f}s")
            print(f"Difference: {abs(avg_interval - sixteenth_duration):.3f}s")
        
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
    print("CHORD DETECTION V2 - PART 1 TEST SUITE")
    print("Testing: Tempo & Beat Detection with 16th-note subdivisions")
    print("=" * 80)
    
    # Test files
    test_files = [
        {
            'path': '../../public/meetup_ring.mp3',
            'name': 'meetup_ring.mp3 (short clip)'
        },
        {
            'path': '../../public/13_The_Girl_from_Ipanema__feat._Bebe[43060].mp3',
            'name': 'The Girl from Ipanema (jazz standard, ~4 min)'
        }
    ]
    
    results = []
    for test_file in test_files:
        success = test_audio_file(test_file['path'], test_file['name'])
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
        print("\nNext steps:")
        print("  1. Review tempo and beat accuracy")
        print("  2. Validate subdivision timing")
        print("  3. Proceed to Part 2: Stem Separation")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Review errors above and fix issues before proceeding")
    
    print("=" * 80)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
