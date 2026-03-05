#!/bin/bash
# Build and push bass transcription ECS image

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

export AWS_PROFILE=production
REGION="us-east-1"
ACCOUNT_ID="090130568474"
ECR_REPO="bass-transcription"
IMAGE_NAME="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO}"

# Allow custom tag via command line argument (default: latest)
TAG="${1:-latest}"

echo "========================================="
echo "Building Bass Transcription ECS Image"
echo "========================================="
echo ""
echo "ECR Repository: $IMAGE_NAME"
echo "Tag: $TAG"
echo ""

# Create ECR repository if it doesn't exist
echo "📦 Ensuring ECR repository exists..."
aws ecr describe-repositories --repository-names $ECR_REPO --region $REGION 2>/dev/null || \
  aws ecr create-repository --repository-name $ECR_REPO --region $REGION

# Prepare build context
echo "📦 Preparing build context..."
BUILD_DIR=$(mktemp -d)
echo "Build directory: $BUILD_DIR"

# Copy files
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
docker build --platform linux/amd64 -t $ECR_REPO:latest $BUILD_DIR

# Clean up build directory
rm -rf $BUILD_DIR

# Login to ECR
echo ""
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Tag and push
echo ""
echo "📤 Pushing image to ECR..."
docker tag $ECR_REPO:latest $IMAGE_NAME:$TAG
docker push $IMAGE_NAME:$TAG

# Also tag and push as 'latest' if a specific tag was provided
if [ "$TAG" != "latest" ]; then
  echo ""
  echo "📤 Also tagging and pushing as 'latest'..."
  docker tag $ECR_REPO:latest $IMAGE_NAME:latest
  docker push $IMAGE_NAME:latest
fi

echo ""
echo "========================================="
echo "✅ Image pushed successfully!"
echo "========================================="
echo ""
echo "Image: $IMAGE_NAME:$TAG"
if [ "$TAG" != "latest" ]; then
  echo "Also tagged as: $IMAGE_NAME:latest"
fi
echo ""
echo "To update ECS task definition, run:"
echo "  aws ecs update-service \\"
echo "    --cluster ChordScout-dev \\"
echo "    --service bass-transcription-dev \\"
echo "    --force-new-deployment \\"
echo "    --profile production \\"
echo "    --region $REGION"
echo ""
