#!/bin/bash
# Simple deployment using existing resources

set -e

export AWS_PROFILE=production
REGION="us-east-1"
BUCKET="music-transcription-audio-test-090130568474"  # Use existing bucket
TABLE="MusicTranscription-Jobs-test"  # Use existing table

echo "========================================="
echo "Deploying File Upload (Simple)"
echo "========================================="
echo ""
echo "Using existing resources:"
echo "  Bucket: $BUCKET"
echo "  Table: $TABLE"
echo ""

# Create Lambda function code
cat > /tmp/upload-lambda.py << 'EOF'
import json
import boto3
import os
import uuid
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

AUDIO_BUCKET = os.environ['AUDIO_BUCKET']
JOBS_TABLE = os.environ['JOBS_TABLE']

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    
    # Parse body
    if 'body' in event:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
    else:
        body = event
    
    filename = body.get('filename', 'audio.mp3')
    content_type = body.get('contentType', 'audio/mpeg')
    user_id = body.get('userId', 'anonymous')
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # S3 key for upload
    s3_key = f"uploads/{job_id}/{filename}"
    
    # Generate presigned URL for upload
    presigned_url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': AUDIO_BUCKET,
            'Key': s3_key,
            'ContentType': content_type
        },
        ExpiresIn=3600
    )
    
    # Create job in DynamoDB
    table = dynamodb.Table(JOBS_TABLE)
    table.put_item(Item={
        'jobId': job_id,
        'userId': user_id,
        'status': 'UPLOADING',
        'progress': 0,
        's3Key': s3_key,
        'filename': filename,
        'createdAt': datetime.utcnow().isoformat(),
        'updatedAt': datetime.utcnow().isoformat()
    })
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'jobId': job_id,
            'uploadUrl': presigned_url,
            's3Key': s3_key
        })
    }
EOF

# Zip the Lambda function
cd /tmp
zip upload-lambda.zip upload-lambda.py
cd - > /dev/null

# Get or create IAM role
ROLE_ARN=$(aws iam get-role --role-name MusicTranscription-Lambda-test --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$ROLE_ARN" ]; then
    echo "IAM role not found, using existing role from CloudFormation..."
    ROLE_ARN="arn:aws:iam::090130568474:role/MusicTranscription-Lambda-test"
fi

echo "Using IAM Role: $ROLE_ARN"

# Create or update Lambda function
echo "Creating/updating Lambda function..."

# Check if function exists
if aws lambda get-function --function-name music-transcription-upload-test --region $REGION &>/dev/null; then
    echo "Function exists, updating..."
    aws lambda update-function-code \
      --function-name music-transcription-upload-test \
      --zip-file fileb:///tmp/upload-lambda.zip \
      --region $REGION > /dev/null
    
    aws lambda update-function-configuration \
      --function-name music-transcription-upload-test \
      --environment "Variables={AUDIO_BUCKET=$BUCKET,JOBS_TABLE=$TABLE}" \
      --timeout 30 \
      --region $REGION > /dev/null
else
    echo "Function doesn't exist, creating..."
    aws lambda create-function \
      --function-name music-transcription-upload-test \
      --runtime python3.9 \
      --role $ROLE_ARN \
      --handler upload-lambda.lambda_handler \
      --zip-file fileb:///tmp/upload-lambda.zip \
      --environment "Variables={AUDIO_BUCKET=$BUCKET,JOBS_TABLE=$TABLE}" \
      --timeout 30 \
      --region $REGION > /dev/null
fi

echo "✅ Lambda function created/updated"

# Get existing API Gateway
API_ID=$(aws cloudformation describe-stacks \
  --stack-name music-transcription-pipeline \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text 2>/dev/null | cut -d'/' -f3 | cut -d'.' -f1)

if [ -z "$API_ID" ]; then
    echo "Error: API Gateway not found"
    exit 1
fi

echo "Using API Gateway: $API_ID"

# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function \
  --function-name music-transcription-upload-test \
  --region $REGION \
  --query 'Configuration.FunctionArn' \
  --output text)

# Create API Gateway integration
echo "Creating API Gateway integration..."
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id $API_ID \
  --integration-type AWS_PROXY \
  --integration-uri $LAMBDA_ARN \
  --payload-format-version 2.0 \
  --region $REGION \
  --query 'IntegrationId' \
  --output text 2>/dev/null || echo "")

if [ -z "$INTEGRATION_ID" ]; then
    echo "Integration might already exist, getting existing..."
    INTEGRATION_ID=$(aws apigatewayv2 get-integrations \
      --api-id $API_ID \
      --region $REGION \
      --query "Items[?IntegrationUri=='$LAMBDA_ARN'].IntegrationId" \
      --output text | head -1)
fi

echo "Integration ID: $INTEGRATION_ID"

# Create route
echo "Creating API route..."
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key 'POST /upload' \
  --target "integrations/$INTEGRATION_ID" \
  --region $REGION 2>/dev/null || echo "Route might already exist"

# Add Lambda permission
echo "Adding Lambda permission..."
aws lambda add-permission \
  --function-name music-transcription-upload-test \
  --statement-id apigateway-upload \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:090130568474:$API_ID/*" \
  --region $REGION 2>/dev/null || echo "Permission might already exist"

# Get API endpoint
API_ENDPOINT="https://${API_ID}.execute-api.${REGION}.amazonaws.com"

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""
echo "API Endpoint: $API_ENDPOINT"
echo "Bucket: $BUCKET"
echo "Table: $TABLE"
echo ""

# Save config
cat > config-upload.json <<EOF
{
  "apiEndpoint": "$API_ENDPOINT",
  "audioBucket": "$BUCKET",
  "jobsTable": "$TABLE",
  "region": "$REGION"
}
EOF

echo "Configuration saved to config-upload.json"
echo ""
echo "Test with:"
echo "  ./test-upload.sh path/to/audio.mp3"
echo ""
