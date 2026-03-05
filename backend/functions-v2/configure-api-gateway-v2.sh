#!/bin/bash

# Configure API Gateway v2 (HTTP API) endpoints for v3.0 confirmation workflows
# This script adds the POST /jobs/{jobId}/confirm-mode and POST /jobs/{jobId}/confirm-key endpoints

set -e

API_ID="l43ftjo75d"
REGION="us-east-1"
ACCOUNT_ID="090130568474"
AWS_PROFILE="production"

echo "========================================="
echo "Configuring API Gateway v2 Endpoints"
echo "========================================="
echo "API ID: $API_ID"
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo ""

# Function to create HTTP API route and integration
create_route() {
  local ROUTE_KEY=$1
  local LAMBDA_NAME=$2
  local DESCRIPTION=$3
  
  echo ""
  echo "Setting up $ROUTE_KEY route..."
  echo "-----------------------------------------"
  
  # Get Lambda ARN
  LAMBDA_ARN=$(aws lambda get-function \
    --function-name $LAMBDA_NAME \
    --region $REGION \
    --profile $AWS_PROFILE \
    --query 'Configuration.FunctionArn' \
    --output text)
  
  echo "✓ Lambda ARN: $LAMBDA_ARN"
  
  # Create integration
  echo "Creating Lambda integration..."
  INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id $API_ID \
    --integration-type AWS_PROXY \
    --integration-uri $LAMBDA_ARN \
    --payload-format-version 2.0 \
    --region $REGION \
    --profile $AWS_PROFILE \
    --query 'IntegrationId' \
    --output text)
  
  echo "✓ Integration ID: $INTEGRATION_ID"
  
  # Create route
  echo "Creating route..."
  ROUTE_ID=$(aws apigatewayv2 create-route \
    --api-id $API_ID \
    --route-key "$ROUTE_KEY" \
    --target "integrations/$INTEGRATION_ID" \
    --region $REGION \
    --profile $AWS_PROFILE \
    --query 'RouteId' \
    --output text)
  
  echo "✓ Route ID: $ROUTE_ID"
  
  # Add Lambda permission
  echo "Adding Lambda invoke permission..."
  aws lambda remove-permission \
    --function-name $LAMBDA_NAME \
    --statement-id apigateway-invoke-v2 \
    --region $REGION \
    --profile $AWS_PROFILE > /dev/null 2>&1 || true
  
  aws lambda add-permission \
    --function-name $LAMBDA_NAME \
    --statement-id apigateway-invoke-v2 \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*" \
    --region $REGION \
    --profile $AWS_PROFILE > /dev/null
  
  echo "✓ $ROUTE_KEY configured successfully"
}

# Create both routes
create_route "POST /jobs/{jobId}/confirm-mode" "confirm-transcription-mode" "Confirm transcription mode selection"
create_route "POST /jobs/{jobId}/confirm-key" "confirm-key" "Confirm musical key"

# Get API endpoint
API_ENDPOINT=$(aws apigatewayv2 get-api \
  --api-id $API_ID \
  --region $REGION \
  --profile $AWS_PROFILE \
  --query 'ApiEndpoint' \
  --output text)

echo ""
echo "========================================="
echo "✓ API Gateway Configuration Complete!"
echo "========================================="
echo ""
echo "Endpoints available at:"
echo "  POST $API_ENDPOINT/jobs/{jobId}/confirm-mode"
echo "  POST $API_ENDPOINT/jobs/{jobId}/confirm-key"
echo ""
echo "Test with:"
echo "  curl -X POST $API_ENDPOINT/jobs/test-id/confirm-mode \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"transcriptionMode\": \"bass-only\"}'"
echo ""
echo "  curl -X POST $API_ENDPOINT/jobs/test-id/confirm-key \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"confirmedKey\": \"C major\"}'"
echo ""
