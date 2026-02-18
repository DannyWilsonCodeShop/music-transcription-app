#!/usr/bin/env python3
"""
Test Complete Pipeline: All 5 Parts
Tests the entire chord detection system from audio to final results
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from chord_detection_v2 import detect_chords_complete

def test_complete_pipeline(audio_path, expected_name):
    """Test complete pipeline on a single audio file"""
    print("\n" + "=" * 80)
    print(f"TESTING COMPLETE PIPELINE: {expected_name}")
    print("=" * 80)
    
    if not os.path.exists(audio_path):
        print(f"❌ File not found: {audio_path}")
        return False
    
    try:
        # Run complete pipeline
        results = detect_chords_complete(audio_path)
        
        # Validate results
        print("\n" + "=" * 80)
        print("FINAL RESULTS")
        print("=" * 80)
        
        print(f"\n📊 Analysis Summary:")
        print(f"  Audio duration: {results['duration']:.2f}s")
        print(f"  Processing time: {results['processing_time']:.2f}s")
        print(f"  Processing speed: {results['duration'] / results['processing_time']:.1f}x realtime")
        
        print(f"\n🎵 Musical Analysis:")
        print(f"  Tempo: {results['tempo']:.1f} BPM")
        print(f"  Time signature: {results['time_signature']}")
        print(f"  Key: {results['key']} {results['scale']}")
        print(f"  Key confidence: {results['key_confidence']:.3f}")
        
        print(f"\n🎸 Chord Analysis:")
        print(f"  Total chords: {len(results['chords'])}")
        
        if len(results['chords']) > 0:
            durations = [c['duration'] for c in results['chords']]
            confidences = [c['confidence'] for c in results['chords']]
            
            print(f"  Average duration: {sum(durations) / len(durations):.2f}s")
            print(f"  Average confidence: {sum(confidences) / len(confidences):.3f}")
            
            # Show first 10 chords
            print(f"\n  First 10 chords:")
            for i, chord in enumerate(results['chords'][:10], 1):
                print(f"    {i:2d}. {chord['name']:8s} at {chord['start']:6.2f}s "
                      f"(duration: {chord['duration']:5.2f}s, confidence: {chord['confidence']:.3f})")
            
            # Chord distribution
            chord_counts = {}
            for chord in results['chords']:
                chord_counts[chord['name']] = chord_counts.get(chord['name'], 0) + 1
            
            print(f"\n  Top 5 chords:")
            sorted_chords = sorted(chord_counts.items(), key=lambda x: x[1], reverse=True)
            for i, (chord_name, count) in enumerate(sorted_chords[:5], 1):
                percentage = (count / len(results['chords'])) * 100
                print(f"    {i}. {chord_name:8s}: {count:2d} times ({percentage:5.1f}%)")
        
        # Save results to JSON
        output_path = f"/tmp/chord_detection_{expected_name.replace(' ', '_').replace('/', '_')}.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {output_path}")
        
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
    print("COMPLETE PIPELINE TEST SUITE")
    print("Testing: All 5 Parts (Tempo → Stems → Chroma → Chords → Key)")
    print("=" * 80)
    
    # Test files
    test_files = [
        {
            'path': '../../public/meetup_ring.mp3',
            'name': 'meetup_ring.mp3'
        },
        {
            'path': '../../public/13_The_Girl_from_Ipanema__feat._Bebe[43060].mp3',
            'name': 'The_Girl_from_Ipanema'
        }
    ]
    
    results = []
    for test_file in test_files:
        success = test_complete_pipeline(test_file['path'], test_file['name'])
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
        print("\n✅ Complete pipeline working:")
        print("  ✓ Part 1: Tempo & Beat Detection")
        print("  ✓ Part 2: Stem Separation")
        print("  ✓ Part 3: CQT Chromagram")
        print("  ✓ Part 4: Template Matching with HMM")
        print("  ✓ Part 5: Key Detection")
        print("\n🚀 Ready for integration with existing system!")
        print("\nNext steps:")
        print("  1. Review accuracy on test files")
        print("  2. Test with more diverse music")
        print("  3. Integrate into ECS task")
        print("  4. Deploy to production")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Review errors above and fix issues before proceeding")
    
    print("=" * 80)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
