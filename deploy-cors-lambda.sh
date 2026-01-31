#!/bin/bash

# Deploy CORS-enabled API Proxy Lambda Function
# This Lambda acts as a CORS-enabled proxy to the enhanced transcription system

set -e

echo "🚀 Deploying CORS-enabled API Proxy Lambda..."

# Configuration
FUNCTION_NAME="chordscout-cors-api-proxy-dev"
REGION="us-east-1"
STATE_MACHINE_ARN="arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-V2-Transcription-dev"
JOBS_TABLE_NAME="ChordScout-Jobs-V2-dev"

# Create deployment package
echo "📦 Creating deployment package..."
rm -f cors-api-proxy.zip

# Create package.json for dependencies
cat > package.json << EOF
{
  "name": "cors-api-proxy",
  "version": "1.0.0",
  "dependencies": {
    "@aws-sdk/client-sfn": "^3.975.0",
    "@aws-sdk/client-dynamodb": "^3.975.0",
    "@aws-sdk/lib-dynamodb": "^3.975.0",
    "uuid": "^9.0.0"
  }
}
EOF

# Install dependencies
npm install --production

# Create the zip file
zip -r cors-api-proxy.zip fix-cors-lambda.js node_modules/ package.json

echo "✅ Deployment package created: cors-api-proxy.zip"

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &> /dev/null; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://cors-api-proxy.zip \
        --region $REGION
else
    echo "🆕 Creating new Lambda function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime nodejs18.x \
        --role arn:aws:iam::090130568474:role/ChordScout-Lambda-Role-dev \
        --handler fix-cors-lambda.handler \
        --zip-file fileb://cors-api-proxy.zip \
        --timeout 30 \
        --memory-size 256 \
        --region $REGION
fi

# Update environment variables
echo "🔧 Setting environment variables..."
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment Variables="{STATE_MACHINE_ARN=$STATE_MACHINE_ARN,JOBS_TABLE_NAME=$JOBS_TABLE_NAME}" \
    --region $REGION

# Get function ARN
FUNCTION_ARN=$(aws lambda get-function \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'Configuration.FunctionArn' \
    --output text)

echo "✅ Lambda function deployed successfully!"
echo "📋 Function Details:"
echo "  - Name: $FUNCTION_NAME"
echo "  - ARN: $FUNCTION_ARN"
echo "  - Region: $REGION"

# Create or update API Gateway
echo ""
echo "🌐 Setting up API Gateway..."

# Check if API exists
API_ID=$(aws apigateway get-rest-apis \
    --query "items[?name=='chordscout-cors-api'].id" \
    --output text \
    --region $REGION)

if [ "$API_ID" = "None" ] || [ -z "$API_ID" ]; then
    echo "🆕 Creating new API Gateway..."
    API_ID=$(aws apigateway create-rest-api \
        --name chordscout-cors-api \
        --description "CORS-enabled API for ChordScout transcription" \
        --region $REGION \
        --query 'id' \
        --output text)
    
    # Get root resource ID
    ROOT_RESOURCE_ID=$(aws apigateway get-resources \
        --rest-api-id $API_ID \
        --region $REGION \
        --query 'items[?path==`/`].id' \
        --output text)
    
    # Create /jobs resource
    JOBS_RESOURCE_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $ROOT_RESOURCE_ID \
        --path-part jobs \
        --region $REGION \
        --query 'id' \
        --output text)
    
    # Create /jobs/{jobId} resource
    JOB_ID_RESOURCE_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $JOBS_RESOURCE_ID \
        --path-part '{jobId}' \
        --region $REGION \
        --query 'id' \
        --output text)
    
    # Create POST method for /jobs
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $JOBS_RESOURCE_ID \
        --http-method POST \
        --authorization-type NONE \
        --region $REGION
    
    # Create GET method for /jobs/{jobId}
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $JOB_ID_RESOURCE_ID \
        --http-method GET \
        --authorization-type NONE \
        --region $REGION
    
    # Create OPTIONS methods for CORS
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $JOBS_RESOURCE_ID \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region $REGION
    
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $JOB_ID_RESOURCE_ID \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region $REGION
    
    # Set up Lambda integrations
    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $JOBS_RESOURCE_ID \
        --http-method POST \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$FUNCTION_ARN/invocations" \
        --region $REGION
    
    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $JOB_ID_RESOURCE_ID \
        --http-method GET \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$FUNCTION_ARN/invocations" \
        --region $REGION
    
    # Add Lambda permissions
    aws lambda add-permission \
        --function-name $FUNCTION_NAME \
        --statement-id apigateway-cors-invoke \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:execute-api:$REGION:090130568474:$API_ID/*/*" \
        --region $REGION
    
    # Deploy API
    aws apigateway create-deployment \
        --rest-api-id $API_ID \
        --stage-name prod \
        --region $REGION
    
    echo "✅ API Gateway created and deployed!"
else
    echo "✅ Using existing API Gateway: $API_ID"
fi

# Get API endpoint
API_ENDPOINT="https://$API_ID.execute-api.$REGION.amazonaws.com/prod"

echo ""
echo "🎉 CORS-enabled API deployment complete!"
echo "📋 API Details:"
echo "  - API ID: $API_ID"
echo "  - Endpoint: $API_ENDPOINT"
echo ""
echo "🔧 Next Steps:"
echo "1. Update frontend to use: $API_ENDPOINT"
echo "2. Set USE_MOCK_DATA = false"
echo "3. Test the enhanced transcription system"
echo ""
echo "📝 Test the API:"
echo "curl -X POST $API_ENDPOINT/jobs \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"youtubeUrl\": \"https://www.youtube.com/watch?v=CDdvReNKKuk\"}'"

# Cleanup
rm -f cors-api-proxy.zip package.json package-lock.json
rm -rf node_modules/

echo ""
echo "✅ Deployment complete!"