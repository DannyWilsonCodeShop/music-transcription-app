#!/bin/bash
# Deploy ECS Infrastructure (without building Docker image)
# Docker image should be built via GitHub Actions

set -e

export AWS_PROFILE=production
REGION="us-east-1"
ACCOUNT_ID="090130568474"
BUCKET="music-transcription-audio-test-090130568474"
TABLE="MusicTranscription-Jobs-test"
CLUSTER_NAME="music-transcription-test"
REPO_NAME="music-transcription-chord-detection"

echo "========================================="
echo "Deploying Chord Detection Infrastructure"
echo "========================================="
echo ""
echo "Account: $ACCOUNT_ID"
echo "Region: $REGION"
echo ""

# Get ECR image URI
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:latest"

echo "Using ECR Image: $ECR_URI"
echo ""
echo "⚠️  Make sure the Docker image has been built via GitHub Actions!"
echo "   Check: https://github.com/YOUR_REPO/actions"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Deploy CloudFormation stack
echo ""
echo "☁️  Deploying CloudFormation stack..."

aws cloudformation deploy \
  --template-file cloudformation-chord-detection.yaml \
  --stack-name music-transcription-chord-detection \
  --parameter-overrides \
      EcrImageUri=$ECR_URI \
      AudioBucket=$BUCKET \
      JobsTable=$TABLE \
      ClusterName=$CLUSTER_NAME \
  --capabilities CAPABILITY_IAM \
  --region $REGION \
  --profile $AWS_PROFILE

echo "✅ CloudFormation stack deployed"

# Get outputs
echo ""
echo "📊 Stack Outputs:"
aws cloudformation describe-stacks \
  --stack-name music-transcription-chord-detection \
  --region $REGION \
  --profile $AWS_PROFILE \
  --query 'Stacks[0].Outputs' \
  --output table

# Get VPC info for Lambda configuration
echo ""
echo "🔍 Getting VPC information for Lambda..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region $REGION --profile $AWS_PROFILE)
SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text --region $REGION --profile $AWS_PROFILE | tr '\t' ',')
SG_ID=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text --region $REGION --profile $AWS_PROFILE)

echo "VPC ID: $VPC_ID"
echo "Subnets: $SUBNETS"
echo "Security Group: $SG_ID"

# Save configuration
cat > ../ecs-config.json <<EOF
{
  "ecsCluster": "$CLUSTER_NAME",
  "ecsTaskDefinition": "music-transcription-chord-detection",
  "ecsSubnets": "$SUBNETS",
  "ecsSecurityGroups": "$SG_ID",
  "ecrImageUri": "$ECR_URI"
}
EOF

echo ""
echo "✅ Configuration saved to ../ecs-config.json"

echo ""
echo "========================================="
echo "✅ Infrastructure Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Update processing Lambda with ECS configuration"
echo "2. Test with: ./test-upload.sh path/to/audio.mp3"
echo ""
