#!/bin/bash
# Build and push v3.0 Docker image for development environment
# Creates a new ECR repository to avoid affecting production

set -e

export AWS_PROFILE=chordscout
REGION="us-east-1"
ACCOUNT_ID="090130568474"
REPO_NAME="chordscout-chord-detector-v3-dev"
IMAGE_TAG="v3.0-phase3"

echo "=========================================="
echo "Building v3.0 Docker Image for Dev"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "Dockerfile" ]; then
  echo "Error: Dockerfile not found. Run this script from bass-transcription-pipeline/bass-transcription-ecs/"
  exit 1
fi

# Check if simple-pipeline exists (two levels up from bass-transcription-ecs)
if [ ! -d "../../simple-pipeline" ]; then
  echo "Error: simple-pipeline directory not found at ../../simple-pipeline"
  echo "Current directory: $(pwd)"
  echo "Expected structure: ChordScout/simple-pipeline and ChordScout/bass-transcription-pipeline"
  exit 1
fi

# Check if required files exist
echo "Checking required files..."
REQUIRED_FILES=(
  "app.py"
  "bass_note_transcription.py"
  "stem_transcription.py"
  "song_metadata_lyrics.py"
  "requirements.txt"
  "Dockerfile"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    echo "✗ Missing: $file"
    exit 1
  else
    echo "✓ Found: $file"
  fi
done

echo ""
echo "Creating ECR repository (if it doesn't exist)..."
aws ecr describe-repositories \
  --repository-names $REPO_NAME \
  --region $REGION \
  2>/dev/null || \
aws ecr create-repository \
  --repository-name $REPO_NAME \
  --region $REGION \
  --image-scanning-configuration scanOnPush=true \
  --query 'repository.{name:repositoryName,uri:repositoryUri}' \
  --output table

echo ""
echo "Logging in to ECR..."
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo ""
echo "Building Docker image..."
echo "  Tag: $REPO_NAME:$IMAGE_TAG"
echo "  Context: ../../ (includes both bass-transcription-pipeline and simple-pipeline)"

# Build from two levels up to include both directories
# Dockerfile path is relative to current directory, context is relative to where docker runs
# Use --platform linux/amd64 for ECS Fargate compatibility
cd ../..
docker build --platform linux/amd64 -f bass-transcription-pipeline/bass-transcription-ecs/Dockerfile -t $REPO_NAME:$IMAGE_TAG .
cd -

if [ $? -ne 0 ]; then
  echo "✗ Docker build failed"
  exit 1
fi

echo ""
echo "✓ Docker image built successfully"

# Tag for ECR
ECR_IMAGE="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG"
ECR_LATEST="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest"

echo ""
echo "Tagging image for ECR..."
docker tag $REPO_NAME:$IMAGE_TAG $ECR_IMAGE
docker tag $REPO_NAME:$IMAGE_TAG $ECR_LATEST

echo ""
echo "Pushing to ECR..."
echo "  Pushing: $ECR_IMAGE"
docker push $ECR_IMAGE

echo "  Pushing: $ECR_LATEST"
docker push $ECR_LATEST

echo ""
echo "=========================================="
echo "✓ Build and Push Complete"
echo "=========================================="
echo ""
echo "Repository: $REPO_NAME"
echo "Image URI: $ECR_IMAGE"
echo "Latest URI: $ECR_LATEST"
echo ""
echo "Next steps:"
echo "  1. Update task definition to use new image"
echo "  2. Run Phase 3 test again"
echo ""
echo "Update task definition command:"
echo "  aws ecs register-task-definition \\"
echo "    --family chordscout-chord-detector-dev \\"
echo "    --cli-input-json file://task-definition-v3.json"
echo ""
