#!/usr/bin/env python3
"""
Test Omnizart for chord detection
Free and open source - no API key needed!
"""

import os
import sys

# Test audio file
TEST_AUDIO = "public/meetup_ring.mp3"

if not os.path.exists(TEST_AUDIO):
    print(f"❌ Error: Test audio file not found: {TEST_AUDIO}")
    sys.exit(1)

print("🎵 Testing Omnizart Chord Detection")
print("=" * 60)
print(f"Audio file: {TEST_AUDIO}")
print()

# Check if omnizart is installed
try:
    from omnizart.chord import app as chord_app
    print("✓ omnizart is installed")
except ImportError:
    print("❌ omnizart not installed")
    print("\nInstalling omnizart...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "omnizart"])
    print("✓ Installation complete")
    from omnizart.chord import app as chord_app

print()

# Step 1: Transcribe chords
print("1. Analyzing audio with Omnizart...")
print("-" * 60)

try:
    # Transcribe chords
    chords_data = chord_app.transcribe(TEST_AUDIO)
    
    print(f"✓ Analysis complete")
    print()
    
except Exception as e:
    print(f"❌ Error during analysis: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Display results
print("=" * 60)
print("CHORD DETECTION RESULTS")
print("=" * 60)
print()

print(f"Result type: {type(chords_data)}")
print(f"Result: {chords_data}")
print()

print("=" * 60)
print("✅ TEST COMPLETE!")
print("=" * 60)
