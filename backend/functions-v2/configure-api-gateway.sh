#!/bin/bash

# Configure API Gateway endpoints for v3.0 confirmation workflows
# This script adds the /jobs/{jobId}/confirm-mode and /jobs/{jobId}/confirm-key endpoints

set -e

API_ID="l43ftjo75d"
REGION="us-east-1"
ACCOUNT_ID="090130568474"
AWS_PROFILE="production"

echo "========================================="
echo "Configuring API Gateway Endpoints"
echo "========================================="
echo "API ID: $API_ID"
echo "Region: $REGION"
echo ""

# Get the /jobs resource ID
echo "Finding /jobs resource..."
JOBS_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region $REGION \
  --query 'items[?path==`/jobs`].id' \
  --output text)

if [ -z "$JOBS_RESOURCE_ID" ]; then
  echo "Error: /jobs resource not found"
  exit 1
fi

echo "✓ Found /jobs resource: $JOBS_RESOURCE_ID"

# Check if {jobId} resource exists, create if not
echo "Checking for {jobId} resource..."
JOBID_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region $REGION \
  --query 'items[?pathPart==`{jobId}`].id' \
  --output text)

if [ -z "$JOBID_RESOURCE_ID" ]; then
  echo "Creating {jobId} resource..."
  JOBID_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $JOBS_RESOURCE_ID \
    --path-part '{jobId}' \
    --region $REGION \
    --query 'id' \
    --output text)
  echo "✓ Created {jobId} resource: $JOBID_RESOURCE_ID"
else
  echo "✓ Found existing {jobId} resource: $JOBID_RESOURCE_ID"
fi

# Function to create endpoint
create_endpoint() {
  local PATH_PART=$1
  local LAMBDA_NAME=$2
  local DESCRIPTION=$3
  
  echo ""
  echo "Setting up /$PATH_PART endpoint..."
  echo "-----------------------------------------"
  
  # Check if resource exists
  RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $REGION \
    --query "items[?pathPart==\`$PATH_PART\`].id" \
    --output text)
  
  if [ -z "$RESOURCE_ID" ]; then
    echo "Creating $PATH_PART resource..."
    RESOURCE_ID=$(aws apigateway create-resource \
      --rest-api-id $API_ID \
      --parent-id $JOBID_RESOURCE_ID \
      --path-part "$PATH_PART" \
      --region $REGION \
      --query 'id' \
      --output text)
    echo "✓ Created resource: $RESOURCE_ID"
  else
    echo "✓ Found existing resource: $RESOURCE_ID"
  fi
  
  # Check if POST method exists
  if aws apigateway get-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --region $REGION > /dev/null 2>&1; then
    echo "POST method already exists, deleting to recreate..."
    aws apigateway delete-method \
      --rest-api-id $API_ID \
      --resource-id $RESOURCE_ID \
      --http-method POST \
      --region $REGION
  fi
  
  # Create POST method
  echo "Creating POST method..."
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --authorization-type NONE \
    --region $REGION > /dev/null
  
  # Get Lambda ARN
  LAMBDA_ARN=$(aws lambda get-function \
    --function-name $LAMBDA_NAME \
    --region $REGION \
    --query 'Configuration.FunctionArn' \
    --output text)
  
  echo "✓ Lambda ARN: $LAMBDA_ARN"
  
  # Create integration
  echo "Creating Lambda integration..."
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
    --region $REGION > /dev/null
  
  # Add Lambda permission (remove old one if exists)
  echo "Adding Lambda invoke permission..."
  aws lambda remove-permission \
    --function-name $LAMBDA_NAME \
    --statement-id apigateway-invoke \
    --region $REGION > /dev/null 2>&1 || true
  
  aws lambda add-permission \
    --function-name $LAMBDA_NAME \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/POST/jobs/*/$PATH_PART" \
    --region $REGION > /dev/null
  
  # Enable CORS - OPTIONS method
  echo "Enabling CORS..."
  
  # Delete OPTIONS if exists
  aws apigateway delete-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --region $REGION > /dev/null 2>&1 || true
  
  # Create OPTIONS method
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $REGION > /dev/null
  
  # Create OPTIONS method response
  aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Origin":true}' \
    --region $REGION > /dev/null
  
  # Create OPTIONS integration
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
    --region $REGION > /dev/null
  
  # Create OPTIONS integration response
  aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'POST,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
    --response-templates '{"application/json":""}' \
    --region $REGION > /dev/null
  
  echo "✓ $PATH_PART endpoint configured successfully"
}

# Create both endpoints
create_endpoint "confirm-mode" "confirm-transcription-mode" "Confirm transcription mode selection"
create_endpoint "confirm-key" "confirm-key" "Confirm musical key"

# Deploy API
echo ""
echo "Deploying API to prod stage..."
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --description "v3.0 Phase 2 - Added confirm-mode and confirm-key endpoints" \
  --region $REGION > /dev/null

echo "✓ API deployed successfully"

echo ""
echo "========================================="
echo "✓ API Gateway Configuration Complete!"
echo "========================================="
echo ""
echo "Endpoints available at:"
echo "  POST https://$API_ID.execute-api.$REGION.amazonaws.com/jobs/{jobId}/confirm-mode"
echo "  POST https://$API_ID.execute-api.$REGION.amazonaws.com/jobs/{jobId}/confirm-key"
echo ""
echo "Test with:"
echo "  curl -X POST https://$API_ID.execute-api.$REGION.amazonaws.com/jobs/test-id/confirm-mode \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"transcriptionMode\": \"bass-only\"}'"
echo ""
