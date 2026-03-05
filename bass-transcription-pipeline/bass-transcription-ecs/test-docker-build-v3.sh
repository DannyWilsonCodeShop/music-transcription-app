#!/bin/bash
# Test Docker build for v3.0 with new modules

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

IMAGE_NAME="bass-transcription-v3-test"

echo "========================================="
echo "Testing Bass Transcription v3.0 Docker Build"
echo "========================================="
echo ""

# Prepare build context
echo "📦 Preparing build context..."
BUILD_DIR=$(mktemp -d)
echo "Build directory: $BUILD_DIR"

# Copy files
echo "Copying application files..."
cp app.py $BUILD_DIR/
cp bass_note_transcription.py $BUILD_DIR/
cp stem_transcription.py $BUILD_DIR/
cp song_metadata_lyrics.py $BUILD_DIR/
cp test_imports.py $BUILD_DIR/
cp requirements.txt $BUILD_DIR/
cp Dockerfile $BUILD_DIR/

# Copy simple-pipeline directory for downbeat detection
echo "Copying simple-pipeline directory..."
cp -r ../../simple-pipeline $BUILD_DIR/

# Build Docker image
echo ""
echo "🐳 Building Docker image for linux/amd64..."
docker build --platform linux/amd64 -t $IMAGE_NAME:latest $BUILD_DIR

# Clean up build directory
rm -rf $BUILD_DIR

echo ""
echo "========================================="
echo "✅ Image built successfully!"
echo "========================================="
echo ""

# Test imports
echo "🧪 Testing module imports..."
echo ""

docker run --rm $IMAGE_NAME:latest python -c "
import sys
print('Testing v3.0 module imports...')
print()

try:
    import stem_transcription
    print('✅ stem_transcription imported successfully')
except Exception as e:
    print(f'❌ stem_transcription import failed: {e}')
    sys.exit(1)

try:
    import song_metadata_lyrics
    print('✅ song_metadata_lyrics imported successfully')
except Exception as e:
    print(f'❌ song_metadata_lyrics import failed: {e}')
    sys.exit(1)

try:
    import bass_note_transcription
    print('✅ bass_note_transcription imported successfully')
except Exception as e:
    print(f'❌ bass_note_transcription import failed: {e}')
    sys.exit(1)

print()
print('Testing v3.0 dependencies...')
print()

try:
    import mutagen
    print(f'✅ mutagen {mutagen.version_string} imported successfully')
except Exception as e:
    print(f'❌ mutagen import failed: {e}')
    sys.exit(1)

try:
    import requests
    print(f'✅ requests {requests.__version__} imported successfully')
except Exception as e:
    print(f'❌ requests import failed: {e}')
    sys.exit(1)

try:
    import bs4
    print(f'✅ beautifulsoup4 imported successfully')
except Exception as e:
    print(f'❌ beautifulsoup4 import failed: {e}')
    sys.exit(1)

try:
    import lyricsgenius
    print(f'✅ lyricsgenius imported successfully')
except Exception as e:
    print(f'❌ lyricsgenius import failed: {e}')
    sys.exit(1)

print()
print('Testing existing dependencies...')
print()

try:
    import basic_pitch
    print('✅ basic_pitch imported successfully')
except Exception as e:
    print(f'❌ basic_pitch import failed: {e}')
    sys.exit(1)

try:
    import demucs
    print('✅ demucs imported successfully')
except Exception as e:
    print(f'❌ demucs import failed: {e}')
    sys.exit(1)

try:
    import librosa
    print(f'✅ librosa imported successfully')
except Exception as e:
    print(f'❌ librosa import failed: {e}')
    sys.exit(1)

print()
print('========================================')
print('✅ All imports successful!')
print('========================================')
"

echo ""
echo "🧪 Testing module functions..."
echo ""

docker run --rm $IMAGE_NAME:latest python -c "
import sys
from stem_transcription import transcribe_stem
from song_metadata_lyrics import identify_song, fetch_lyrics, align_lyrics_to_measures
from bass_note_transcription import detect_bass_notes, quantize_notes

print('Testing function availability...')
print()

# Check stem_transcription functions
print('✅ stem_transcription.transcribe_stem available')

# Check song_metadata_lyrics functions
print('✅ song_metadata_lyrics.identify_song available')
print('✅ song_metadata_lyrics.fetch_lyrics available')
print('✅ song_metadata_lyrics.align_lyrics_to_measures available')

# Check bass_note_transcription functions
print('✅ bass_note_transcription.detect_bass_notes available')
print('✅ bass_note_transcription.quantize_notes available')

print()
print('========================================')
print('✅ All functions available!')
print('========================================')
"

echo ""
echo "========================================="
echo "✅ Docker build test completed successfully!"
echo "========================================="
echo ""
echo "Image: $IMAGE_NAME:latest"
echo ""
echo "To run the container interactively:"
echo "  docker run -it --rm $IMAGE_NAME:latest /bin/bash"
echo ""
echo "To clean up the test image:"
echo "  docker rmi $IMAGE_NAME:latest"
echo ""
