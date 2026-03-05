#!/usr/bin/env python3
"""
Test script to verify all v3.0 dependencies can be imported correctly.
This validates that the requirements.txt file has all necessary dependencies
and that there are no version conflicts.
"""

import sys

def test_imports():
    """Test importing all v3.0 dependencies"""
    errors = []
    
    print("Testing v3.0 dependency imports...")
    print("-" * 50)
    
    # Test mutagen (audio metadata extraction)
    try:
        import mutagen
        print("✓ mutagen imported successfully (version: {})".format(mutagen.version_string))
    except ImportError as e:
        errors.append(f"✗ mutagen import failed: {e}")
        print(errors[-1])
    
    # Test requests (HTTP client for Genius API)
    try:
        import requests
        print("✓ requests imported successfully (version: {})".format(requests.__version__))
    except ImportError as e:
        errors.append(f"✗ requests import failed: {e}")
        print(errors[-1])
    
    # Test beautifulsoup4 (HTML parsing for lyrics)
    try:
        from bs4 import BeautifulSoup
        import bs4
        print("✓ beautifulsoup4 imported successfully (version: {})".format(bs4.__version__))
    except ImportError as e:
        errors.append(f"✗ beautifulsoup4 import failed: {e}")
        print(errors[-1])
    
    # Test lxml (XML/HTML parser)
    try:
        import lxml
        from lxml import etree
        print("✓ lxml imported successfully (version: {})".format(lxml.__version__))
    except ImportError as e:
        errors.append(f"✗ lxml import failed: {e}")
        print(errors[-1])
    
    # Test lyricsgenius (Genius API client)
    try:
        import lyricsgenius
        print("✓ lyricsgenius imported successfully (version: {})".format(lyricsgenius.__version__))
    except ImportError as e:
        errors.append(f"✗ lyricsgenius import failed: {e}")
        print(errors[-1])
    
    # Test existing dependencies still work
    print("\nTesting existing dependencies...")
    print("-" * 50)
    
    try:
        import boto3
        print("✓ boto3 imported successfully")
    except ImportError as e:
        errors.append(f"✗ boto3 import failed: {e}")
        print(errors[-1])
    
    try:
        import librosa
        print("✓ librosa imported successfully (version: {})".format(librosa.__version__))
    except ImportError as e:
        errors.append(f"✗ librosa import failed: {e}")
        print(errors[-1])
    
    try:
        import soundfile
        print("✓ soundfile imported successfully")
    except ImportError as e:
        errors.append(f"✗ soundfile import failed: {e}")
        print(errors[-1])
    
    try:
        import numpy
        print("✓ numpy imported successfully (version: {})".format(numpy.__version__))
    except ImportError as e:
        errors.append(f"✗ numpy import failed: {e}")
        print(errors[-1])
    
    try:
        import torch
        print("✓ torch imported successfully (version: {})".format(torch.__version__))
    except ImportError as e:
        errors.append(f"✗ torch import failed: {e}")
        print(errors[-1])
    
    try:
        import tensorflow
        print("✓ tensorflow imported successfully (version: {})".format(tensorflow.__version__))
    except ImportError as e:
        errors.append(f"✗ tensorflow import failed: {e}")
        print(errors[-1])
    
    try:
        import basic_pitch
        print("✓ basic_pitch imported successfully")
    except ImportError as e:
        errors.append(f"✗ basic_pitch import failed: {e}")
        print(errors[-1])
    
    print("\n" + "=" * 50)
    if errors:
        print(f"FAILED: {len(errors)} import error(s) detected")
        for error in errors:
            print(f"  {error}")
        return 1
    else:
        print("SUCCESS: All dependencies imported successfully!")
        print("No version conflicts detected.")
        return 0

if __name__ == "__main__":
    sys.exit(test_imports())
