#!/usr/bin/env python3
"""
Test Real Audio Analysis
Tests the real audio analyzer with the actual meetup_ring.mp3 file
"""

import sys
import os
import json
from pathlib import Path

# Add the real audio analyzer to path
sys.path.append('backend/functions-v2/real-audio-analyzer')

try:
    from real_audio_analyzer import analyze_audio_file
    print("✅ Real audio analyzer imported successfully")
except ImportError as e:
    print(f"❌ Failed to import real audio analyzer: {e}")
    print("Make sure you have installed the required dependencies:")
    print("pip install librosa numpy scipy soundfile requests")
    sys.exit(1)

def test_real_audio_analysis():
    """Test real audio analysis with meetup_ring.mp3"""
    print("🎼 Testing Real Audio Analysis with meetup_ring.mp3\n")
    
    # Check if audio file exists
    audio_file = Path("public/meetup_ring.mp3")
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return False
    
    print(f"📁 Audio file found: {audio_file}")
    print(f"📊 File size: {audio_file.stat().st_size} bytes ({audio_file.stat().st_size/1024:.1f} KB)")
    
    try:
        # Analyze the actual audio file
        print("\n🚀 Starting real audio analysis...")
        result = analyze_audio_file(str(audio_file), analysis_interval=0.5)
        
        print("\n✅ Real audio analysis completed!")
        
        # Display results
        print("\n📊 ANALYSIS RESULTS:")
        print("=" * 50)
        
        metadata = result['metadata']
        tempo = result['tempo']
        key = result['key']
        time_sig = result['timeSignature']
        chords = result['chords']
        
        print(f"Duration: {metadata['duration']:.2f} seconds")
        print(f"Sample Rate: {metadata['sample_rate']} Hz")
        print(f"Analysis Method: {metadata['analysis_method']}")
        print(f"Libraries Used: {metadata['libraries_used']}")
        
        print(f"\n🥁 TEMPO ANALYSIS:")
        print(f"BPM: {tempo['bpm']:.1f}")
        print(f"Confidence: {tempo['confidence']:.2f}")
        print(f"Method: {tempo['method']}")
        print(f"Beat Times: {len(tempo['beat_times'])} beats detected")
        
        print(f"\n🗝️ KEY ANALYSIS:")
        print(f"Key: {key['root']} {key['mode']}")
        print(f"Confidence: {key['confidence']:.2f}")
        print(f"Method: {key['method']}")
        
        print(f"\n📏 TIME SIGNATURE:")
        print(f"Time Signature: {time_sig['numerator']}/{time_sig['denominator']}")
        print(f"Confidence: {time_sig['confidence']:.2f}")
        print(f"Beats per Measure: {time_sig['beatsPerMeasure']}")
        print(f"Measure Duration: {time_sig['measureDuration']:.2f}s")
        print(f"Total Measures: {len(time_sig['measures'])}")
        
        print(f"\n🎵 CHORD ANALYSIS:")
        print(f"Analysis Interval: {chords['analysisInterval']}s")
        print(f"Total Chords: {chords['totalChords']}")
        print(f"Method: {chords['method']}")
        
        if chords['chords']:
            print(f"\n🎼 DETECTED CHORDS:")
            print("Time    | Chord | Confidence | Downbeat")
            print("-" * 40)
            
            for i, chord in enumerate(chords['chords'][:10]):  # Show first 10
                downbeat = "✓" if chord.get('isDownbeat', False) else " "
                print(f"{chord['start']:6.1f}s | {chord['chord']:5s} | {chord['confidence']:8.2f} | {downbeat:8s}")
            
            if len(chords['chords']) > 10:
                print(f"... and {len(chords['chords']) - 10} more chords")
            
            # Analyze chord distribution
            chord_counts = {}
            for chord in chords['chords']:
                chord_name = chord['chord']
                chord_counts[chord_name] = chord_counts.get(chord_name, 0) + 1
            
            print(f"\n📊 CHORD DISTRIBUTION:")
            sorted_chords = sorted(chord_counts.items(), key=lambda x: x[1], reverse=True)
            for chord_name, count in sorted_chords[:5]:  # Top 5
                percentage = (count / len(chords['chords'])) * 100
                print(f"{chord_name:5s}: {count:3d} times ({percentage:4.1f}%)")
        
        else:
            print("⚠️ No chords detected")
        
        # Test chord change detection
        print(f"\n🔍 TESTING CHORD CHANGE DETECTION:")
        chord_changes = detect_chord_changes_simple(chords['chords'])
        
        original_size = len(json.dumps(chords['chords']))
        reduced_size = len(json.dumps(chord_changes))
        reduction = ((original_size - reduced_size) / original_size * 100) if original_size > 0 else 0
        
        print(f"Original detections: {len(chords['chords'])}")
        print(f"Chord changes: {len(chord_changes)}")
        print(f"Data reduction: {reduction:.1f}%")
        print(f"Size: {original_size} → {reduced_size} bytes")
        
        if chord_changes:
            print(f"\n🎼 CHORD CHANGES:")
            print("Time    | Chord | Duration")
            print("-" * 30)
            for change in chord_changes[:5]:  # Show first 5
                print(f"{change['start']:6.1f}s | {change['chord']:5s} | {change['duration']:6.1f}s")
        
        # Save results
        output_file = "real-audio-analysis-results.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Real audio analysis failed: {e}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        return False

def detect_chord_changes_simple(chords):
    """Simple chord change detection for testing"""
    if not chords:
        return []
    
    changes = []
    current_chord = None
    start_time = 0
    
    for chord in chords:
        if chord['chord'] != current_chord:
            if current_chord is not None:
                changes.append({
                    'chord': current_chord,
                    'start': start_time,
                    'end': chord['start'],
                    'duration': chord['start'] - start_time
                })
            current_chord = chord['chord']
            start_time = chord['start']
    
    # Add final chord
    if current_chord is not None and chords:
        last_chord = chords[-1]
        changes.append({
            'chord': current_chord,
            'start': start_time,
            'end': last_chord['end'],
            'duration': last_chord['end'] - start_time
        })
    
    return changes

if __name__ == "__main__":
    print("🧪 Real Audio Analysis Test")
    print("=" * 50)
    
    success = test_real_audio_analysis()
    
    if success:
        print("\n🎉 REAL AUDIO ANALYSIS TEST: SUCCESS!")
        print("The real audio analyzer is working with actual audio files!")
    else:
        print("\n❌ REAL AUDIO ANALYSIS TEST: FAILED!")
        print("Check the error messages above for troubleshooting.")
    
    print("\n📋 Next Steps:")
    print("1. Install Python dependencies: pip install librosa numpy scipy soundfile")
    print("2. Deploy the real audio analyzer to AWS Lambda")
    print("3. Test with various audio files")
    print("4. Integrate with the existing chord change detection system")