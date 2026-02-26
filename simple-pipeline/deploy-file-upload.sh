#!/bin/bash
# Deploy File Upload Pipeline

set -e

export AWS_PROFILE=production
STACK_NAME="music-transcription-file-upload"
REGION="us-east-1"
ENVIRONMENT="test"

echo "========================================="
echo "Deploying File Upload Pipeline"
echo "========================================="
echo ""

# Check AWS account
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
echo "AWS Account: $ACCOUNT_ID"

if [ "$ACCOUNT_ID" != "090130568474" ]; then
    echo "WARNING: Not in account 8474!"
    exit 1
fi

echo ""
echo "Deploying CloudFormation stack..."
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo ""

aws cloudformation deploy \
  --template-file cloudformation-file-upload.yaml \
  --stack-name $STACK_NAME \
  --parameter-overrides Environment=$ENVIRONMENT \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""

# Get outputs
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

AUDIO_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`AudioBucket`].OutputValue' \
  --output text)

JOBS_TABLE=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`JobsTable`].OutputValue' \
  --output text)

echo "API Endpoint: $API_ENDPOINT"
echo "Audio Bucket: $AUDIO_BUCKET"
echo "Jobs Table: $JOBS_TABLE"
echo ""

# Save to config file
cat > config-upload.json <<EOF
{
  "apiEndpoint": "$API_ENDPOINT",
  "audioBucket": "$AUDIO_BUCKET",
  "jobsTable": "$JOBS_TABLE",
  "region": "$REGION",
  "accountId": "$ACCOUNT_ID"
}
EOF

echo "Configuration saved to config-upload.json"
echo ""
echo "========================================="
echo "Next Steps:"
echo "========================================="
echo ""
echo "Test the upload:"
echo "  ./test-upload.sh path/to/audio.mp3"
echo ""
