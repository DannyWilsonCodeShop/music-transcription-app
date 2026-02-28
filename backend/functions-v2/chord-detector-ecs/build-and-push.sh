#!/bin/bash
# Build and push chord-detector-ecs Docker image with simple-pipeline directory

set -e

export AWS_PROFILE=chordscout
REGION="us-east-1"
ACCOUNT_ID="090130568474"
REPO_NAME="chordscout-chord-detector"

echo "========================================="
echo "Building Chord Detector ECS Image"
echo "========================================="
echo ""

# Get ECR URI
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}"
echo "ECR Repository: $ECR_URI"
echo ""

# Create a temporary build context with all needed files
echo "📦 Preparing build context..."
BUILD_DIR=$(mktemp -d)
echo "Build directory: $BUILD_DIR"

# Copy app files
cp app.py "$BUILD_DIR/"
cp section_detection.py "$BUILD_DIR/"
cp test_chord_detection.py "$BUILD_DIR/"
cp requirements.txt "$BUILD_DIR/"
cp Dockerfile "$BUILD_DIR/"

# Copy simple-pipeline directory (3 levels up from here)
echo "Copying simple-pipeline directory..."
cp -r ../../../simple-pipeline "$BUILD_DIR/"

# Build Docker image
echo ""
echo "🐳 Building Docker image for linux/amd64..."
docker build --platform linux/amd64 -t $REPO_NAME:latest "$BUILD_DIR"

# Clean up build directory
rm -rf "$BUILD_DIR"

# Login to ECR
echo ""
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION --profile $AWS_PROFILE | \
  docker login --username AWS --password-stdin $ECR_URI

# Tag and push
echo ""
echo "📤 Pushing image to ECR..."
docker tag $REPO_NAME:latest $ECR_URI:latest
docker push $ECR_URI:latest

echo ""
echo "========================================="
echo "✅ Image pushed successfully!"
echo "========================================="
echo ""
echo "Image: $ECR_URI:latest"
echo ""
echo "To update ECS task definition, run:"
echo "  aws ecs update-service \\"
echo "    --cluster ChordScout-dev \\"
echo "    --service chordscout-chord-detector-dev \\"
echo "    --force-new-deployment \\"
echo "    --profile chordscout \\"
echo "    --region us-east-1"
echo ""
