#!/bin/bash
# Deploy processing pipeline components

set -e

export AWS_PROFILE=production
REGION="us-east-1"
BUCKET="music-transcription-audio-test-090130568474"
TABLE="MusicTranscription-Jobs-test"
ROLE_ARN="arn:aws:iam::090130568474:role/MusicTranscription-Lambda-test"

echo "========================================="
echo "Deploying Processing Pipeline"
echo "========================================="
echo ""

# Load ECS configuration
if [ ! -f ecs-config.json ]; then
    echo "ERROR: ecs-config.json not found. Run chord-detection/deploy-infrastructure.sh first"
    exit 1
fi

ECS_CLUSTER=$(cat ecs-config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['ecsCluster'])")
ECS_TASK_DEF=$(cat ecs-config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['ecsTaskDefinition'])")
ECS_SUBNETS=$(cat ecs-config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['ecsSubnets'])")
ECS_SG=$(cat ecs-config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['ecsSecurityGroups'])")

echo "ECS Configuration:"
echo "  Cluster: $ECS_CLUSTER"
echo "  Task Definition: $ECS_TASK_DEF"
echo "  Subnets: ${ECS_SUBNETS:0:50}..."
echo "  Security Group: $ECS_SG"
echo ""

# 1. Deploy process-audio Lambda
echo "📦 Creating process-audio Lambda..."
cd /tmp
cat > process-audio.py << 'PYEOF'
import json
import boto3
import os
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
ecs = boto3.client('ecs')

JOBS_TABLE = os.environ['JOBS_TABLE']
ECS_CLUSTER = os.environ.get('ECS_CLUSTER', 'music-transcription-test')
ECS_TASK_DEFINITION = os.environ.get('ECS_TASK_DEFINITION', 'music-transcription-chord-detection')
ECS_SUBNETS = os.environ.get('ECS_SUBNETS', '').split(',')  # Comma-separated subnet IDs
ECS_SECURITY_GROUPS = os.environ.get('ECS_SECURITY_GROUPS', '').split(',')  # Comma-separated SG IDs

def lambda_handler(event, context):
    """
    Triggered by S3 upload event.
    Launches ECS task for chord detection.
    """
    print(f"Event: {json.dumps(event)}")
    
    # Parse S3 event
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        # Extract job ID from key: uploads/{jobId}/filename.mp3
        parts = key.split('/')
        if len(parts) < 3 or parts[0] != 'uploads':
            print(f"Skipping non-upload key: {key}")
            continue
        
        job_id = parts[1]
        
        print(f"Processing job: {job_id}")
        
        # Update job status to PROCESSING
        table = dynamodb.Table(JOBS_TABLE)
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, progress = :progress, updatedAt = :updatedAt',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'PROCESSING',
                ':progress': 5,
                ':updatedAt': datetime.utcnow().isoformat()
            }
        )
        
        print(f"Job {job_id} marked as PROCESSING")
        
        # Launch ECS task for chord detection
        print(f"Launching ECS task...")
        print(f"  Cluster: {ECS_CLUSTER}")
        print(f"  Task Definition: {ECS_TASK_DEFINITION}")
        print(f"  Subnets: {ECS_SUBNETS}")
        print(f"  Security Groups: {ECS_SECURITY_GROUPS}")
        
        try:
            response = ecs.run_task(
                cluster=ECS_CLUSTER,
                taskDefinition=ECS_TASK_DEFINITION,
                launchType='FARGATE',
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': ECS_SUBNETS,
                        'securityGroups': ECS_SECURITY_GROUPS,
                        'assignPublicIp': 'ENABLED'
                    }
                },
                overrides={
                    'containerOverrides': [
                        {
                            'name': 'chord-detection',
                            'environment': [
                                {'name': 'JOB_ID', 'value': job_id},
                                {'name': 'AUDIO_BUCKET', 'value': bucket},
                                {'name': 'AUDIO_KEY', 'value': key}
                            ]
                        }
                    ]
                }
            )
            
            task_arn = response['tasks'][0]['taskArn']
            print(f"✅ ECS task launched: {task_arn}")
            
            # Update job with task ARN
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET ecsTaskArn = :taskArn, updatedAt = :updatedAt',
                ExpressionAttributeValues={
                    ':taskArn': task_arn,
                    ':updatedAt': datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            print(f"ERROR launching ECS task: {str(e)}")
            # Update job status to FAILED
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET #status = :status, errorMessage = :error, updatedAt = :updatedAt',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': str(e),
                    ':updatedAt': datetime.utcnow().isoformat()
                }
            )
            raise
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Processing started'})
    }
PYEOF

zip process-audio.zip process-audio.py

# Check if function exists
if aws lambda get-function --function-name music-transcription-process-audio-test --region $REGION &>/dev/null; then
    echo "Function exists, updating..."
    aws lambda update-function-code \
      --function-name music-transcription-process-audio-test \
      --zip-file fileb://process-audio.zip \
      --region $REGION > /dev/null
    
    # Wait for code update to complete
    echo "Waiting for code update to complete..."
    aws lambda wait function-updated \
      --function-name music-transcription-process-audio-test \
      --region $REGION
    
    # Update configuration with JSON format to handle commas in values
    cat > /tmp/lambda-env.json <<EOF
{
  "Variables": {
    "JOBS_TABLE": "$TABLE",
    "ECS_CLUSTER": "$ECS_CLUSTER",
    "ECS_TASK_DEFINITION": "$ECS_TASK_DEF",
    "ECS_SUBNETS": "$ECS_SUBNETS",
    "ECS_SECURITY_GROUPS": "$ECS_SG"
  }
}
EOF
    
    aws lambda update-function-configuration \
      --function-name music-transcription-process-audio-test \
      --environment file:///tmp/lambda-env.json \
      --timeout 60 \
      --region $REGION > /dev/null
else
    echo "Function doesn't exist, creating..."
    
    # Create configuration with JSON format
    cat > /tmp/lambda-env.json <<EOF
{
  "Variables": {
    "JOBS_TABLE": "$TABLE",
    "ECS_CLUSTER": "$ECS_CLUSTER",
    "ECS_TASK_DEFINITION": "$ECS_TASK_DEF",
    "ECS_SUBNETS": "$ECS_SUBNETS",
    "ECS_SECURITY_GROUPS": "$ECS_SG"
  }
}
EOF
    
    aws lambda create-function \
      --function-name music-transcription-process-audio-test \
      --runtime python3.9 \
      --role $ROLE_ARN \
      --handler process-audio.lambda_handler \
      --zip-file fileb://process-audio.zip \
      --environment file:///tmp/lambda-env.json \
      --timeout 60 \
      --region $REGION > /dev/null
fi

echo "✅ process-audio Lambda deployed"

# 2. Deploy get-job-status Lambda
echo "📦 Creating get-job-status Lambda..."
cat > get-job-status.py << 'PYEOF'
import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')

JOBS_TABLE = os.environ['JOBS_TABLE']

def lambda_handler(event, context):
    """
    GET /jobs/{jobId}
    Returns job status and results.
    """
    print(f"Event: {json.dumps(event)}")
    
    # Extract job ID from path
    job_id = event.get('pathParameters', {}).get('jobId')
    
    if not job_id:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Missing jobId'})
        }
    
    # Get job from DynamoDB
    table = dynamodb.Table(JOBS_TABLE)
    response = table.get_item(Key={'jobId': job_id})
    
    if 'Item' not in response:
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Job not found'})
        }
    
    job = response['Item']
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(job, default=str)
    }
PYEOF

zip get-job-status.zip get-job-status.py

# Check if function exists
if aws lambda get-function --function-name music-transcription-get-job-status-test --region $REGION &>/dev/null; then
    echo "Function exists, updating..."
    aws lambda update-function-code \
      --function-name music-transcription-get-job-status-test \
      --zip-file fileb://get-job-status.zip \
      --region $REGION > /dev/null
    
    aws lambda update-function-configuration \
      --function-name music-transcription-get-job-status-test \
      --environment "Variables={JOBS_TABLE=$TABLE}" \
      --timeout 30 \
      --region $REGION > /dev/null
else
    echo "Function doesn't exist, creating..."
    aws lambda create-function \
      --function-name music-transcription-get-job-status-test \
      --runtime python3.9 \
      --role $ROLE_ARN \
      --handler get-job-status.lambda_handler \
      --zip-file fileb://get-job-status.zip \
      --environment "Variables={JOBS_TABLE=$TABLE}" \
      --timeout 30 \
      --region $REGION > /dev/null
fi

echo "✅ get-job-status Lambda deployed"

# 3. Add S3 event notification
echo "🔔 Configuring S3 event notification..."

# Get Lambda ARN
PROCESS_LAMBDA_ARN=$(aws lambda get-function \
  --function-name music-transcription-process-audio-test \
  --region $REGION \
  --query 'Configuration.FunctionArn' \
  --output text)

# Add Lambda permission for S3
aws lambda add-permission \
  --function-name music-transcription-process-audio-test \
  --statement-id s3-trigger \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn "arn:aws:s3:::$BUCKET" \
  --region $REGION 2>/dev/null || echo "Permission already exists"

# Create notification configuration
cat > /tmp/s3-notification.json << EOF
{
  "LambdaFunctionConfigurations": [
    {
      "Id": "ProcessAudioUpload",
      "LambdaFunctionArn": "$PROCESS_LAMBDA_ARN",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "prefix",
              "Value": "uploads/"
            }
          ]
        }
      }
    }
  ]
}
EOF

aws s3api put-bucket-notification-configuration \
  --bucket $BUCKET \
  --notification-configuration file:///tmp/s3-notification.json \
  --region $REGION

echo "✅ S3 event notification configured"

# 4. Add API Gateway route for GET /jobs/{jobId}
echo "🌐 Adding API Gateway route..."

# Get API Gateway ID
API_ID=$(aws cloudformation describe-stacks \
  --stack-name music-transcription-pipeline \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text 2>/dev/null | cut -d'/' -f3 | cut -d'.' -f1)

if [ -z "$API_ID" ]; then
    echo "Error: API Gateway not found"
    exit 1
fi

# Get Lambda ARN
STATUS_LAMBDA_ARN=$(aws lambda get-function \
  --function-name music-transcription-get-job-status-test \
  --region $REGION \
  --query 'Configuration.FunctionArn' \
  --output text)

# Create integration
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id $API_ID \
  --integration-type AWS_PROXY \
  --integration-uri $STATUS_LAMBDA_ARN \
  --payload-format-version 2.0 \
  --region $REGION \
  --query 'IntegrationId' \
  --output text 2>/dev/null || echo "")

if [ -z "$INTEGRATION_ID" ]; then
    echo "Integration might already exist, getting existing..."
    INTEGRATION_ID=$(aws apigatewayv2 get-integrations \
      --api-id $API_ID \
      --region $REGION \
      --query "Items[?IntegrationUri=='$STATUS_LAMBDA_ARN'].IntegrationId" \
      --output text | head -1)
fi

echo "Integration ID: $INTEGRATION_ID"

# Create route
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key 'GET /jobs/{jobId}' \
  --target "integrations/$INTEGRATION_ID" \
  --region $REGION 2>/dev/null || echo "Route might already exist"

# Add Lambda permission
aws lambda add-permission \
  --function-name music-transcription-get-job-status-test \
  --statement-id apigateway-get-job-status \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:090130568474:$API_ID/*" \
  --region $REGION 2>/dev/null || echo "Permission already exists"

echo "✅ API Gateway route configured"

# Get API endpoint
API_ENDPOINT="https://${API_ID}.execute-api.${REGION}.amazonaws.com"

echo ""
echo "========================================="
echo "✅ Processing Pipeline Deployed!"
echo "========================================="
echo ""
echo "API Endpoint: $API_ENDPOINT"
echo ""
echo "Endpoints:"
echo "  POST $API_ENDPOINT/upload"
echo "  GET  $API_ENDPOINT/jobs/{jobId}"
echo ""
echo "S3 Trigger: Configured for uploads/ prefix"
echo ""
echo "Test the full pipeline:"
echo "  ./test-upload.sh path/to/audio.mp3"
echo ""
