#!/bin/bash
# Deploy Simple Pipeline to Account 8474

set -e

STACK_NAME="music-transcription-pipeline"
REGION="us-east-1"
ENVIRONMENT="test"

echo "========================================="
echo "Deploying Simple Pipeline"
echo "========================================="
echo ""

# Use production profile for account 8474
export AWS_PROFILE=production

# Check AWS account
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
echo "AWS Account: $ACCOUNT_ID"

if [ "$ACCOUNT_ID" != "090130568474" ]; then
    echo "WARNING: Not in account 8474!"
    echo "Current account: $ACCOUNT_ID"
    echo "Expected account: 090130568474"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Deploying CloudFormation stack..."
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo ""

aws cloudformation deploy \
  --template-file cloudformation-simple.yaml \
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
cat > config.json <<EOF
{
  "apiEndpoint": "$API_ENDPOINT",
  "audioBucket": "$AUDIO_BUCKET",
  "jobsTable": "$JOBS_TABLE",
  "region": "$REGION",
  "accountId": "$ACCOUNT_ID"
}
EOF

echo "Configuration saved to config.json"
echo ""
echo "========================================="
echo "Next Steps:"
echo "========================================="
echo ""
echo "1. Add your RapidAPI key:"
echo "   aws lambda update-function-configuration \\"
echo "     --function-name music-transcription-youtube-downloader-test \\"
echo "     --environment Variables={AUDIO_BUCKET=$AUDIO_BUCKET,JOBS_TABLE=$JOBS_TABLE,RAPIDAPI_KEY=YOUR_KEY} \\"
echo "     --region $REGION"
echo ""
echo "2. Test the pipeline:"
echo "   ./test.sh"
echo ""
