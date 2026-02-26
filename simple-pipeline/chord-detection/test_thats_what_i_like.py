#!/usr/bin/env python3
"""
Test: That's What I Like by Bruno Mars
Pop/Funk with groove-oriented harmony
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from chord_detection_v2 import detect_chords_complete

def main():
    audio_path = '../../public/04 That_s What I Like.m4a'
    
    print("=" * 80)
    print("TESTING: That's What I Like by Bruno Mars")
    print("Genre: Pop/Funk")
    print("=" * 80)
    
    if not os.path.exists(audio_path):
        print(f"❌ File not found: {audio_path}")
        return 1
    
    try:
        # Run complete pipeline
        print("\nRunning complete chord detection pipeline...")
        results = detect_chords_complete(audio_path)
        
        # Display results
        print("\n" + "=" * 80)
        print("RESULTS: That's What I Like")
        print("=" * 80)
        
        print(f"\n📊 Analysis Summary:")
        print(f"  Audio duration: {results['duration']:.2f}s ({results['duration']/60:.1f} minutes)")
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
            
            print(f"  Average chord duration: {sum(durations) / len(durations):.2f}s")
            print(f"  Min duration: {min(durations):.2f}s")
            print(f"  Max duration: {max(durations):.2f}s")
            print(f"  Average confidence: {sum(confidences) / len(confidences):.3f}")
            
            # Show all chords
            print(f"\n  Complete chord progression:")
            for i, chord in enumerate(results['chords'], 1):
                print(f"    {i:2d}. {chord['name']:8s} at {chord['start']:6.2f}s "
                      f"(duration: {chord['duration']:5.2f}s, confidence: {chord['confidence']:.3f})")
            
            # Chord distribution
            chord_counts = {}
            for chord in results['chords']:
                chord_counts[chord['name']] = chord_counts.get(chord['name'], 0) + 1
            
            print(f"\n  Chord distribution:")
            sorted_chords = sorted(chord_counts.items(), key=lambda x: x[1], reverse=True)
            for i, (chord_name, count) in enumerate(sorted_chords, 1):
                percentage = (count / len(results['chords'])) * 100
                print(f"    {i:2d}. {chord_name:8s}: {count:2d} times ({percentage:5.1f}%)")
            
            print(f"\n  Unique chords: {len(chord_counts)}")
        
        # Save results
        output_path = '/tmp/thats_what_i_like_results.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Full results saved to: {output_path}")
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
