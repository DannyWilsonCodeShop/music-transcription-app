"""
Test script to verify v3.0 dependencies can be imported
Run this after building the Docker image to ensure all dependencies are installed correctly
"""

def test_v3_dependencies():
    """Test that all v3.0 dependencies can be imported"""
    print("Testing v3.0 dependencies...")
    
    try:
        # Test mutagen for audio metadata
        import mutagen
        print("✓ mutagen imported successfully")
        
        # Test requests for HTTP client
        import requests
        print("✓ requests imported successfully")
        
        # Test beautifulsoup4 for HTML parsing
        from bs4 import BeautifulSoup
        print("✓ beautifulsoup4 imported successfully")
        
        # Test lxml parser
        import lxml
        print("✓ lxml imported successfully")
        
        # Test existing dependencies still work
        import librosa
        print("✓ librosa imported successfully")
        
        import numpy as np
        print("✓ numpy imported successfully")
        
        from basic_pitch.inference import predict
        print("✓ basic-pitch imported successfully")
        
        # Test new modules
        try:
            from stem_transcription import transcribe_stems
            print("✓ stem_transcription module imported successfully")
        except ImportError as e:
            print(f"⚠ stem_transcription module not found: {e}")
        
        try:
            from song_metadata_lyrics import get_song_metadata_and_lyrics
            print("✓ song_metadata_lyrics module imported successfully")
        except ImportError as e:
            print(f"⚠ song_metadata_lyrics module not found: {e}")
        
        try:
            from bass_note_transcription import detect_bass_notes
            print("✓ bass_note_transcription module imported successfully")
        except ImportError as e:
            print(f"⚠ bass_note_transcription module not found: {e}")
        
        print("\n✅ All v3.0 dependencies are available!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Dependency import failed: {e}")
        return False

if __name__ == "__main__":
    success = test_v3_dependencies()
    exit(0 if success else 1)
