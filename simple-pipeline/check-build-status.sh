#!/bin/bash
# Check if Docker image is ready in ECR

export AWS_PROFILE=production
REGION="us-east-1"
REPO_NAME="music-transcription-chord-detection"

echo "Checking ECR for Docker image..."
echo ""

aws ecr describe-images \
  --repository-name $REPO_NAME \
  --region $REGION \
  --profile $AWS_PROFILE \
  --query 'imageDetails[*].[imageTags[0],imagePushedAt,imageSizeInBytes]' \
  --output table 2>/dev/null || echo "❌ No images found yet. GitHub Actions may still be building."

echo ""
echo "Check build status at:"
echo "https://github.com/DannyWilsonCodeShop/music-transcription-app/actions"
