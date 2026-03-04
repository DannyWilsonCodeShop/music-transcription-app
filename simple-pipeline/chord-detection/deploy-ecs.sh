#!/bin/bash
# Deploy Chord Detection ECS Infrastructure

set -e

export AWS_PROFILE=production
REGION="us-east-1"
ACCOUNT_ID="090130568474"
BUCKET="music-transcription-audio-test-090130568474"
TABLE="MusicTranscription-Jobs-test"
CLUSTER_NAME="music-transcription-test"
SERVICE_NAME="chord-detection"
REPO_NAME="music-transcription-chord-detection"

echo "========================================="
echo "Deploying Chord Detection ECS"
echo "========================================="
echo ""
echo "Account: $ACCOUNT_ID"
echo "Region: $REGION"
echo "Cluster: $CLUSTER_NAME"
echo ""

# 1. Create ECR repository
echo "📦 Creating ECR repository..."
aws ecr create-repository \
  --repository-name $REPO_NAME \
  --region $REGION \
  --profile $AWS_PROFILE 2>/dev/null || echo "Repository already exists"

ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}"
echo "✅ ECR Repository: $ECR_URI"

# 2. Build and push Docker image
echo ""
echo "🐳 Building Docker image for linux/amd64..."
docker buildx build --platform linux/amd64 -t $REPO_NAME:latest .

echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION --profile $AWS_PROFILE | \
  docker login --username AWS --password-stdin $ECR_URI

echo "📤 Pushing image to ECR..."
docker tag $REPO_NAME:latest $ECR_URI:latest
docker push $ECR_URI:latest

echo "✅ Docker image pushed: $ECR_URI:latest"

# 3. Deploy CloudFormation stack
echo ""
echo "☁️  Deploying CloudFormation stack..."

aws cloudformation deploy \
  --template-file cloudformation-chord-detection.yaml \
  --stack-name music-transcription-chord-detection \
  --parameter-overrides \
      EcrImageUri=$ECR_URI:latest \
      AudioBucket=$BUCKET \
      JobsTable=$TABLE \
      ClusterName=$CLUSTER_NAME \
  --capabilities CAPABILITY_IAM \
  --region $REGION \
  --profile $AWS_PROFILE

echo "✅ CloudFormation stack deployed"

# 4. Get outputs
echo ""
echo "📊 Stack Outputs:"
aws cloudformation describe-stacks \
  --stack-name music-transcription-chord-detection \
  --region $REGION \
  --profile $AWS_PROFILE \
  --query 'Stacks[0].Outputs' \
  --output table

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""
echo "ECS Cluster: $CLUSTER_NAME"
echo "Task Definition: music-transcription-chord-detection"
echo "ECR Image: $ECR_URI:latest"
echo ""
echo "To run a task manually:"
echo "  aws ecs run-task \\"
echo "    --cluster $CLUSTER_NAME \\"
echo "    --task-definition music-transcription-chord-detection \\"
echo "    --launch-type FARGATE \\"
echo "    --network-configuration \"awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}\" \\"
echo "    --overrides '{\"containerOverrides\":[{\"name\":\"chord-detection\",\"environment\":[{\"name\":\"JOB_ID\",\"value\":\"test-job\"},{\"name\":\"AUDIO_BUCKET\",\"value\":\"'$BUCKET'\"},{\"name\":\"AUDIO_KEY\",\"value\":\"uploads/test/audio.mp3\"}]}]}' \\"
echo "    --region $REGION \\"
echo "    --profile $AWS_PROFILE"
echo ""
