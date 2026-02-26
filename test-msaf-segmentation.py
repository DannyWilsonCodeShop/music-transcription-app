#!/usr/bin/env python3
"""
Test MSAF structural segmentation locally
"""

import sys
import os

# Test if MSAF is available
try:
    import msaf
    print("✓ MSAF is available")
    print(f"  Version: {msaf.__version__ if hasattr(msaf, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"✗ MSAF not available: {e}")
    print("\nInstall with: pip install msaf")
    sys.exit(1)

# Test with a sample audio file
test_audio = "public/meetup_ring.mp3"

if not os.path.exists(test_audio):
    print(f"\n✗ Test audio file not found: {test_audio}")
    print("Please provide a valid audio file path")
    sys.exit(1)

print(f"\n🎵 Testing MSAF with: {test_audio}")
print("=" * 60)

try:
    # Run MSAF analysis
    print("\n1. Running MSAF boundary detection...")
    boundaries, labels = msaf.process(
        test_audio,
        boundaries_id='cnmf',  # CNN-based method
        labels_id='cnmf',
        feature='mfcc'
    )
    
    print(f"✓ MSAF completed successfully")
    print(f"  Detected {len(boundaries)-1} segments")
    print(f"\n2. Boundaries (in seconds):")
    for i, b in enumerate(boundaries):
        print(f"  {i+1}. {b:.2f}s")
    
    print(f"\n3. Labels (segment identifiers):")
    for i, label in enumerate(labels):
        if i < len(boundaries) - 1:
            duration = boundaries[i+1] - boundaries[i]
            print(f"  Segment {i+1}: {label} ({boundaries[i]:.1f}s - {boundaries[i+1]:.1f}s, {duration:.1f}s)")
    
    # Count repetitions
    print(f"\n4. Label distribution:")
    label_counts = {}
    for label in labels:
        label_counts[label] = label_counts.get(label, 0) + 1
    
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {label}: {count} occurrence(s)")
        if count > 1:
            print(f"    → Repeated section (likely Verse or Chorus)")
    
    print("\n" + "=" * 60)
    print("✅ MSAF test completed successfully!")
    print("\nNext steps:")
    print("1. MSAF is working correctly")
    print("2. Ready to integrate into ECS container")
    print("3. Will provide A-B-A-C style segmentation")
    
except Exception as e:
    print(f"\n✗ MSAF test failed: {e}")
    import traceback
    print("\nFull error:")
    print(traceback.format_exc())
    sys.exit(1)
