#!/bin/bash
# Test script for validating Docker build with v3.0 dependencies
# This script builds the Docker image and verifies all imports work correctly

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Bass Transcription v3.0 Docker Build Test"
echo "=========================================="
echo ""

# Prepare build context
echo "Step 1: Preparing build context..."
BUILD_DIR=$(mktemp -d)
echo "Build directory: $BUILD_DIR"

# Copy necessary files
echo "Copying application files..."
cp app.py $BUILD_DIR/
cp bass_note_transcription.py $BUILD_DIR/
cp requirements.txt $BUILD_DIR/
cp Dockerfile $BUILD_DIR/
cp test_imports.py $BUILD_DIR/

# Copy simple-pipeline directory for downbeat detection
echo "Copying simple-pipeline directory from ../../simple-pipeline..."
cp -r ../../simple-pipeline $BUILD_DIR/

echo "✓ Build context prepared"
echo ""

# Build the Docker image
echo "Step 2: Building Docker image..."
docker build -t bass-transcription-test:v3.0 $BUILD_DIR

if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed"
    rm -rf $BUILD_DIR
    exit 1
fi

echo "✓ Docker image built successfully"
echo ""

# Test imports in the container
echo "Step 3: Testing dependency imports..."
docker run --rm bass-transcription-test:v3.0 python test_imports.py

if [ $? -ne 0 ]; then
    echo "ERROR: Import tests failed"
    rm -rf $BUILD_DIR
    exit 1
fi

echo ""
echo "Step 4: Verifying specific v3.0 dependencies..."

# Test mutagen
echo -n "Testing mutagen... "
docker run --rm bass-transcription-test:v3.0 python -c "import mutagen; print('OK - version:', mutagen.version_string)"

# Test requests
echo -n "Testing requests... "
docker run --rm bass-transcription-test:v3.0 python -c "import requests; print('OK - version:', requests.__version__)"

# Test beautifulsoup4
echo -n "Testing beautifulsoup4... "
docker run --rm bass-transcription-test:v3.0 python -c "from bs4 import BeautifulSoup; import bs4; print('OK - version:', bs4.__version__)"

# Test lxml
echo -n "Testing lxml... "
docker run --rm bass-transcription-test:v3.0 python -c "import lxml; print('OK - version:', lxml.__version__)"

# Test lyricsgenius
echo -n "Testing lyricsgenius... "
docker run --rm bass-transcription-test:v3.0 python -c "import lyricsgenius; print('OK - version:', lyricsgenius.__version__)"

echo ""
echo "Step 5: Checking for version conflicts..."
docker run --rm bass-transcription-test:v3.0 pip list | grep -E "(mutagen|requests|beautifulsoup4|lxml|lyricsgenius)"

echo ""
echo "Step 6: Cleaning up..."
rm -rf $BUILD_DIR
echo "✓ Temporary build directory removed"

echo ""
echo "=========================================="
echo "✓ All tests passed successfully!"
echo "Docker image is ready for deployment"
echo "=========================================="
