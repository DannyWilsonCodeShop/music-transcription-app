#!/usr/bin/env python3
"""
Test chord detection on an isolated C# minor chord
Standalone version without dependencies on app.py
"""

try:
    import librosa
    import numpy as np
except ImportError:
    print("Error: librosa not installed")
    print("Install with: pip install librosa")
    exit(1)

def detect_key_improved(chroma):
    """
    Improved key detection using Krumhansl-Schmuckler algorithm
    Returns: (key, mode, confidence)
    """
    # Krumhansl-Schmuckler key profiles
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    
    # Average chroma over time
    chroma_mean = np.mean(chroma, axis=1)
    
    # Normalize
    if np.sum(chroma_mean) > 0:
        chroma_mean = chroma_mean / np.sum(chroma_mean)
    
    # Calculate correlation with each key
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    best_corr = -1
    best_key = 'C'
    best_mode = 'major'
    
    for i in range(12):
        # Rotate profiles to match each key
        major_rot = np.roll(major_profile, i)
        minor_rot = np.roll(minor_profile, i)
        
        # Normalize profiles
        major_rot = major_rot / np.sum(major_rot)
        minor_rot = minor_rot / np.sum(minor_rot)
        
        # Calculate correlation
        major_corr = np.corrcoef(chroma_mean, major_rot)[0, 1]
        minor_corr = np.corrcoef(chroma_mean, minor_rot)[0, 1]
        
        if major_corr > best_corr:
            best_corr = major_corr
            best_key = chord_names[i]
            best_mode = 'major'
        
        if minor_corr > best_corr:
            best_corr = minor_corr
            best_key = chord_names[i]
            best_mode = 'minor'
    
    return best_key, best_mode, best_corr, chroma_mean

# Load the audio file
audio_path = "/Users/dannywilson/DevOps/ChordScout/frontend/public/Piano -  C# min.mp3"

print("=" * 60)
print("Testing Chord Detection on Isolated C# Minor Chord")
print("=" * 60)
print(f"\nAudio file: {audio_path}")

# Load audio
y, sr = librosa.load(audio_path, sr=22050)
duration = librosa.get_duration(y=y, sr=sr)

print(f"Duration: {duration:.2f}s")
print(f"Sample rate: {sr}Hz")
print(f"Samples: {len(y)}")

# Compute chromagram
print("\nComputing chromagram...")
chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
print(f"Chromagram shape: {chroma.shape}")

# Use the improved key detection
print("\nUsing Krumhansl-Schmuckler algorithm...")
key, mode, confidence, chroma_mean = detect_key_improved(chroma)

print("\nChroma values (normalized):")
chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
for i, name in enumerate(chord_names):
    bar = '█' * int(chroma_mean[i] * 50)
    print(f"  {name:3s}: {chroma_mean[i]:.4f} {bar}")

# Find dominant pitch
dominant_pitch = np.argmax(chroma_mean)
print(f"\nDominant pitch: {chord_names[dominant_pitch]}")

print(f"\nDetection Result:")
print(f"  Key: {key}")
print(f"  Mode: {mode}")
print(f"  Confidence: {confidence:.4f}")

print(f"\n{'=' * 60}")
print(f"Expected: C# minor")
print(f"Detected: {key} {mode}")
if key == 'C#' and mode == 'minor':
    print("✅ CORRECT!")
else:
    print(f"❌ INCORRECT (expected C# minor, got {key} {mode})")
print(f"{'=' * 60}")

# Also show top 3 notes in the chord
print("\nTop 3 notes in chord:")
top_3_indices = np.argsort(chroma_mean)[-3:][::-1]
for idx in top_3_indices:
    print(f"  {chord_names[idx]}: {chroma_mean[idx]:.4f}")

# C# minor should have: C# (root), E (minor third), G# (fifth)
print("\nExpected notes in C# minor: C#, E, G#")
