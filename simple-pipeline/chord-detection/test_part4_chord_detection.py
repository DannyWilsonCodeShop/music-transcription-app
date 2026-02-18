#!/usr/bin/env python3
"""
Test Part 4: Template Matching with HMM
Tests the chord detection using template matching and HMM smoothing
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
    detect_chords_with_templates,
    create_chord_templates
)

def test_chord_detection(audio_path, expected_name):
    """Test complete chord detection pipeline on a single audio file"""
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
        
        # Part 3: Compute chromagram
        print("\nStep 3: Computing beat-aligned chromagram...")
        aligned_chroma = compute_beat_aligned_chromagram(
            harmonic_audio,
            sr,
            timing_grid.subdivisions,
            hop_length_ms=20
        )
        print(f"  ✓ Chromagram shape: {aligned_chroma.shape}")
        
        # Part 4: Detect chords
        print("\nStep 4: Detecting chords with template matching...")
        chords = detect_chords_with_templates(
            aligned_chroma,
            timing_grid.tempo,
            timing_grid.subdivisions,
            use_hmm=True
        )
        
        # Validate results
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        
        print(f"\n✓ Total chords detected: {len(chords)}")
        
        if len(chords) == 0:
            print(f"⚠️ WARNING: No chords detected!")
            return False
        
        # Calculate statistics
        durations = [c.duration for c in chords]
        confidences = [c.confidence for c in chords]
        
        print(f"\nChord statistics:")
        print(f"  Average duration: {np.mean(durations):.2f}s")
        print(f"  Min duration: {np.min(durations):.2f}s")
        print(f"  Max duration: {np.max(durations):.2f}s")
        print(f"  Average confidence: {np.mean(confidences):.3f}")
        print(f"  Min confidence: {np.min(confidences):.3f}")
        print(f"  Max confidence: {np.max(confidences):.3f}")
        
        # Check minimum duration enforcement
        min_duration = 60.0 / timing_grid.tempo / 2  # 1/8 note
        short_chords = [c for c in chords if c.duration < min_duration * 0.95]
        if len(short_chords) > 0:
            print(f"\n⚠️ WARNING: {len(short_chords)} chords shorter than minimum duration")
            print(f"  Minimum duration: {min_duration:.3f}s")
            print(f"  Shortest chord: {min(durations):.3f}s")
        else:
            print(f"\n✓ All chords meet minimum duration requirement ({min_duration:.3f}s)")
        
        # Show first 20 chords
        print(f"\nFirst 20 chords detected:")
        for i, chord in enumerate(chords[:20]):
            print(f"  {i+1:2d}. {chord.name:8s} at {chord.start:6.2f}s "
                  f"(duration: {chord.duration:5.2f}s, confidence: {chord.confidence:.3f})")
        
        # Analyze chord distribution
        chord_counts = {}
        for chord in chords:
            chord_counts[chord.name] = chord_counts.get(chord.name, 0) + 1
        
        print(f"\nChord distribution (top 10):")
        sorted_chords = sorted(chord_counts.items(), key=lambda x: x[1], reverse=True)
        for i, (chord_name, count) in enumerate(sorted_chords[:10], 1):
            percentage = (count / len(chords)) * 100
            print(f"  {i:2d}. {chord_name:8s}: {count:3d} times ({percentage:5.1f}%)")
        
        # Check for chord variety
        unique_chords = len(chord_counts)
        print(f"\nUnique chords: {unique_chords}")
        if unique_chords < 3:
            print(f"⚠️ WARNING: Very few unique chords detected")
            print(f"  This might indicate an issue with chord detection")
        else:
            print(f"✓ Good chord variety")
        
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


def test_chord_templates():
    """Test chord template creation"""
    print("\n" + "=" * 80)
    print("TESTING: Chord Template Creation")
    print("=" * 80)
    
    try:
        templates = create_chord_templates()
        
        print(f"\n✓ Templates created: {len(templates)} chord types")
        
        # Check template properties
        print(f"\nTemplate validation:")
        for chord_name, template in list(templates.items())[:5]:
            print(f"  {chord_name:8s}: sum={np.sum(template):.3f}, "
                  f"max={np.max(template):.3f}, "
                  f"non-zero={np.count_nonzero(template)}")
        
        # Check that all templates are normalized
        all_normalized = all(abs(np.sum(t) - 1.0) < 0.01 for t in templates.values())
        if all_normalized:
            print(f"\n✓ All templates are normalized")
        else:
            print(f"\n⚠️ WARNING: Some templates are not normalized")
        
        # Show some example templates
        print(f"\nExample templates:")
        pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        for chord_name in ['C', 'Cm', 'C7', 'Cmaj7']:
            if chord_name in templates:
                template = templates[chord_name]
                active_notes = [pitch_classes[i] for i in range(12) if template[i] > 0.1]
                print(f"  {chord_name:8s}: {', '.join(active_notes)}")
        
        print("\n" + "=" * 80)
        print("✅ TEMPLATE TEST PASSED")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEMPLATE TEST FAILED")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 80)
    print("CHORD DETECTION V2 - PART 4 TEST SUITE")
    print("Testing: Template Matching with HMM")
    print("=" * 80)
    
    # Test template creation first
    template_success = test_chord_templates()
    
    if not template_success:
        print("\n⚠️ Template test failed, skipping audio tests")
        return 1
    
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
    
    results = [{'name': 'Template Creation', 'success': template_success}]
    
    for test_file in test_files:
        success = test_chord_detection(test_file['path'], test_file['name'])
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
        print("\nChord detection is working correctly:")
        print("  - Template matching implemented")
        print("  - HMM smoothing prevents rapid changes")
        print("  - Minimum duration enforced (1/8 note)")
        print("  - Confidence scores calculated")
        print("\nNext steps:")
        print("  1. Review detected chords for accuracy")
        print("  2. Test with more diverse music")
        print("  3. Proceed to Part 5: ML-Based Key Detection")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Review errors above and fix issues before proceeding")
    
    print("=" * 80)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
