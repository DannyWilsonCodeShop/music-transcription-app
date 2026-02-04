#!/usr/bin/env python3
"""
Test chord detection on an isolated C# minor chord
"""

import sys
import os

# Add the chord detector directory to path
sys.path.insert(0, 'backend/functions-v2/chord-detector-ecs')

# Now we can import from app.py
from app import detect_key_improved
import librosa
import numpy as np

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

# Average chroma over time
chroma_mean = np.mean(chroma, axis=1)

# Normalize
if np.sum(chroma_mean) > 0:
    chroma_mean = chroma_mean / np.sum(chroma_mean)

print("\nChroma values (normalized):")
chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
for i, name in enumerate(chord_names):
    bar = '█' * int(chroma_mean[i] * 50)
    print(f"  {name:3s}: {chroma_mean[i]:.4f} {bar}")

# Find dominant pitch
dominant_pitch = np.argmax(chroma_mean)
print(f"\nDominant pitch: {chord_names[dominant_pitch]}")

# Use the improved key detection from app.py
print("\nUsing Krumhansl-Schmuckler algorithm...")
key, mode, confidence = detect_key_improved(chroma)

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
