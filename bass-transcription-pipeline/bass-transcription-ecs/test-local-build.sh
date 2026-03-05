#!/bin/bash
# Test Docker build locally for v3.0 accuracy improvements

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

IMAGE_NAME="bass-transcription-test"

echo "========================================="
echo "Testing Bass Transcription Docker Build"
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
echo "🐳 Building Docker image..."
docker build -t $IMAGE_NAME:latest $BUILD_DIR

# Clean up build directory
rm -rf $BUILD_DIR

echo ""
echo "========================================="
echo "✅ Image built successfully!"
echo "========================================="
echo ""

# Test imports
echo "🧪 Testing imports in container..."
echo ""
docker run --rm $IMAGE_NAME:latest python test_imports.py

echo ""
echo "========================================="
echo "✅ All tests passed!"
echo "========================================="
echo ""
echo "Image: $IMAGE_NAME:latest"
echo ""
echo "To run the container with environment variables:"
echo "  docker run --rm --env-file .env $IMAGE_NAME:latest"
echo ""
