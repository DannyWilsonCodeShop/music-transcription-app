#!/bin/bash

API_ID="rzx9drt3z1"
REGION="us-east-1"
PROFILE="chordscout"
LAMBDA_ARN="arn:aws:lambda:us-east-1:090130568474:function:chordscout-api-proxy-dev"
ACCOUNT_ID="090130568474"

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --profile $PROFILE --query 'items[0].id' --output text)
echo "Root resource ID: $ROOT_ID"

# Create /transcription resource
TRANSCRIPTION_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part transcription \
  --region $REGION \
  --profile $PROFILE \
  --query 'id' --output text)
echo "Transcription resource ID: $TRANSCRIPTION_ID"

# Create /transcription/{proxy+} resource for catch-all
PROXY_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $TRANSCRIPTION_ID \
  --path-part '{proxy+}' \
  --region $REGION \
  --profile $PROFILE \
  --query 'id' --output text)
echo "Proxy resource ID: $PROXY_ID"

# Create ANY method on /{proxy+}
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $PROXY_ID \
  --http-method ANY \
  --authorization-type NONE \
  --region $REGION \
  --profile $PROFILE

# Set up Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $PROXY_ID \
  --http-method ANY \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
  --region $REGION \
  --profile $PROFILE

# Add Lambda permission for API Gateway
aws lambda add-permission \
  --function-name chordscout-api-proxy-dev \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*" \
  --region $REGION \
  --profile $PROFILE

# Deploy API
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region $REGION \
  --profile $PROFILE

echo ""
echo "API Gateway URL: https://$API_ID.execute-api.$REGION.amazonaws.com/prod"
