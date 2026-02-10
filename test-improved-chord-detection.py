#!/usr/bin/env python3
"""
Test improved chord detection using existing libraries
Uses librosa + better chord templates and analysis
"""

import os
import sys
import json
import librosa
import numpy as np
from collections import defaultdict

# Test audio file
TEST_AUDIO = "public/13_The_Girl_from_Ipanema__feat._Bebe[43060].mp3"

if not os.path.exists(TEST_AUDIO):
    print(f"❌ Error: Test audio file not found: {TEST_AUDIO}")
    sys.exit(1)

print("🎵 Testing Improved Chord Detection")
print("=" * 60)
print(f"Audio file: {TEST_AUDIO}")
print()

# Load audio
print("1. Loading audio...")
print("-" * 60)

# Load audio
print("2. Loading audio...")
print("-" * 60)
y, sr = librosa.load(TEST_AUDIO, sr=22050)
duration = librosa.get_duration(y=y, sr=sr)
print(f"✓ Audio loaded")
print(f"  Duration: {duration:.2f}s")
print(f"  Sample rate: {sr}Hz")
print()

# Detect tempo and beats
print("2. Detecting tempo and beats...")
print("-" * 60)
try:
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    tempo_value = float(tempo) if isinstance(tempo, (int, float)) else float(tempo[0])
    beat_times = librosa.frames_to_time(beats, sr=sr)
    print(f"✓ Tempo: {tempo_value:.1f} BPM")
    print(f"  Beats detected: {len(beats)}")
except Exception as e:
    print(f"⚠️  Beat detection failed: {e}")
    tempo_value = 120.0
    beats = []
    beat_times = []
    print(f"  Using default tempo: {tempo_value} BPM")
    print(f"  Will analyze at fixed intervals instead")
print()

# Compute chromagram with better parameters
print("3. Computing chromagram...")
print("-" * 60)
chroma = librosa.feature.chroma_cqt(
    y=y,
    sr=sr,
    hop_length=2048,
    n_chroma=12,
    bins_per_octave=36
)
print(f"✓ Chromagram computed: {chroma.shape}")
print()

# Enhanced chord detection
print("4. Detecting chords...")
print("-" * 60)

chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Enhanced chord templates
def create_chord_templates():
    """Create comprehensive chord templates"""
    templates = {}
    
    for root_idx in range(12):
        root = chord_names[root_idx]
        
        # Major (1, 3, 5)
        major = np.zeros(12)
        major[[0, 4, 7]] = [1.0, 0.8, 0.9]
        templates[root] = np.roll(major, root_idx)
        
        # Minor (1, b3, 5)
        minor = np.zeros(12)
        minor[[0, 3, 7]] = [1.0, 0.8, 0.9]
        templates[root + 'm'] = np.roll(minor, root_idx)
        
        # Dominant 7th (1, 3, 5, b7)
        dom7 = np.zeros(12)
        dom7[[0, 4, 7, 10]] = [1.0, 0.7, 0.8, 0.6]
        templates[root + '7'] = np.roll(dom7, root_idx)
        
        # Major 7th (1, 3, 5, 7)
        maj7 = np.zeros(12)
        maj7[[0, 4, 7, 11]] = [1.0, 0.7, 0.8, 0.6]
        templates[root + 'maj7'] = np.roll(maj7, root_idx)
        
        # Minor 7th (1, b3, 5, b7)
        min7 = np.zeros(12)
        min7[[0, 3, 7, 10]] = [1.0, 0.7, 0.8, 0.6]
        templates[root + 'm7'] = np.roll(min7, root_idx)
        
        # Sus4 (1, 4, 5)
        sus4 = np.zeros(12)
        sus4[[0, 5, 7]] = [1.0, 0.7, 0.9]
        templates[root + 'sus4'] = np.roll(sus4, root_idx)
        
        # Diminished (1, b3, b5)
        dim = np.zeros(12)
        dim[[0, 3, 6]] = [1.0, 0.8, 0.8]
        templates[root + 'dim'] = np.roll(dim, root_idx)
    
    return templates

templates = create_chord_templates()
print(f"  Created {len(templates)} chord templates")

# Analyze at beat positions or fixed intervals
chords = []

if len(beats) > 0:
    # Use beat positions
    print(f"  Analyzing at {len(beats)} beat positions")
    analysis_frames = beats
    analysis_times = beat_times
else:
    # Use fixed intervals (every 0.5 seconds)
    interval = 0.5  # seconds
    num_intervals = int(duration / interval)
    analysis_times = np.arange(0, duration, interval)
    analysis_frames = librosa.time_to_frames(analysis_times, sr=sr, hop_length=2048)
    print(f"  Analyzing at {len(analysis_frames)} fixed intervals ({interval}s apart)")

for i, analysis_frame in enumerate(analysis_frames):
    if analysis_frame >= chroma.shape[1]:
        continue
    
    # Get chroma vector at this beat (average nearby frames)
    start_frame = max(0, analysis_frame - 2)
    end_frame = min(chroma.shape[1], analysis_frame + 3)
    chroma_beat = np.mean(chroma[:, start_frame:end_frame], axis=1)
    
    # Normalize
    if np.sum(chroma_beat) > 0:
        chroma_beat = chroma_beat / np.sum(chroma_beat)
    
    # Find best matching chord
    best_score = -1
    best_chord = 'C'
    
    for chord_name, template in templates.items():
        # Normalize template
        if np.sum(template) > 0:
            template_norm = template / np.sum(template)
        else:
            continue
        
        # Calculate correlation
        score = np.dot(chroma_beat, template_norm)
        
        if score > best_score:
            best_score = score
            best_chord = chord_name
    
    beat_time = analysis_times[i] if i < len(analysis_times) else duration
    
    chords.append({
        'chord': best_chord,
        'time': float(beat_time),
        'confidence': float(best_score)
    })

print(f"  Detected {len(chords)} chords at analysis points")

# Debug: show confidence distribution
if chords:
    confidences = [c['confidence'] for c in chords]
    print(f"  Confidence range: {min(confidences):.3f} - {max(confidences):.3f}")
    print(f"  Average confidence: {np.mean(confidences):.3f}")

# Consolidate consecutive identical chords
consolidated = []
if chords:
    current = chords[0].copy()
    current['start'] = current['time']
    current_confidences = [current['confidence']]
    
    for i in range(1, len(chords)):
        if chords[i]['chord'] == current['chord']:
            # Same chord, accumulate
            current_confidences.append(chords[i]['confidence'])
        else:
            # Different chord, save current
            current['end'] = chords[i]['time']
            current['duration'] = current['end'] - current['start']
            current['confidence'] = np.mean(current_confidences)
            
            # Only keep chords with reasonable duration (lowered confidence threshold)
            if current['duration'] >= 0.5 and current['confidence'] > 0.08:  # Very low threshold
                del current['time']
                consolidated.append(current)
            
            # Start new chord
            current = chords[i].copy()
            current['start'] = current['time']
            current_confidences = [current['confidence']]
    
    # Add last chord
    if current:
        current['end'] = duration
        current['duration'] = duration - current['start']
        current['confidence'] = np.mean(current_confidences)
        if current['duration'] >= 0.5 and current['confidence'] > 0.08:  # Very low threshold
            del current['time']
            consolidated.append(current)

print(f"  Consolidated to {len(consolidated)} chords")
print()

# Display results
print("=" * 60)
print("CHORD DETECTION RESULTS")
print("=" * 60)
print()

if consolidated:
    print(f"🎸 Total chords: {len(consolidated)}")
    print()
    print("First 20 chords:")
    for i, chord in enumerate(consolidated[:20], 1):
        print(f"  {i:2d}. {chord['chord']:8s} at {chord['start']:6.1f}s (duration: {chord['duration']:.1f}s, confidence: {chord['confidence']:.2f})")
    
    if len(consolidated) > 20:
        print(f"  ... and {len(consolidated) - 20} more chords")
    
    print()
    
    # Chord statistics
    chord_counts = defaultdict(int)
    for chord in consolidated:
        chord_counts[chord['chord']] += 1
    
    print("Most common chords:")
    sorted_chords = sorted(chord_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (chord, count) in enumerate(sorted_chords[:10], 1):
        print(f"  {i:2d}. {chord:8s} - {count} times")
    
    print()
    
    # Estimate key from most common chords
    most_common = sorted_chords[0][0] if sorted_chords else 'C'
    # Remove quality suffix to get root
    key_estimate = most_common.replace('m', '').replace('7', '').replace('maj', '').replace('sus4', '').replace('dim', '')
    print(f"🎹 Estimated key: {key_estimate} (based on most common chord)")
    print()
    
    # Save results
    output_file = "improved-chord-detection-result.json"
    with open(output_file, 'w') as f:
        json.dump({
            'chords': consolidated,
            'totalChords': len(consolidated),
            'uniqueChords': len(chord_counts),
            'estimatedKey': key_estimate,
            'tempo': tempo_value,
            'duration': duration,
            'model': 'librosa-enhanced-templates'
        }, f, indent=2)
    
    print(f"📄 Results saved to: {output_file}")
    
else:
    print("⚠️  No chords detected")

print()
print("=" * 60)
print("✅ TEST COMPLETE!")
print("=" * 60)
print()
print("This uses your existing libraries (librosa) with:")
print("  ✓ Enhanced chord templates (major, minor, 7th, maj7, m7, sus4, dim)")
print("  ✓ Better normalization and correlation")
print("  ✓ Beat-synchronized analysis")
print("  ✓ Confidence scoring")
print()
print("Compare this with your current system to see if it's better!")
