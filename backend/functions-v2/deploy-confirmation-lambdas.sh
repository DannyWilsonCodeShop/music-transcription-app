#!/bin/bash

# Deploy confirm-transcription-mode and confirm-key Lambda functions
# This script deploys both Lambda functions needed for v3.0 Phase 2

set -e

REGION="us-east-1"
LAMBDA_ROLE="arn:aws:iam::090130568474:role/ChordScout-Lambda-V2-dev"
DYNAMODB_TABLE="ChordScout-Jobs-V2-dev"
AWS_PROFILE="production"

echo "========================================="
echo "Deploying v3.0 Confirmation Lambda Functions"
echo "========================================="

# Function to deploy a Lambda
deploy_lambda() {
    local FUNCTION_NAME=$1
    local FUNCTION_DIR=$2
    
    echo ""
    echo "Deploying $FUNCTION_NAME..."
    echo "-----------------------------------------"
    
    cd "$FUNCTION_DIR"
    
    # Install dependencies
    echo "Installing dependencies..."
    npm install --production
    
    # Create deployment package
    echo "Creating deployment package..."
    zip -r function.zip index.js node_modules/ > /dev/null
    
    # Check if function exists
    if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --profile "$AWS_PROFILE" > /dev/null 2>&1; then
        echo "Function exists, updating code..."
        aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file fileb://function.zip \
            --region "$REGION" \
            --profile "$AWS_PROFILE"
        
        echo "Waiting for function to be ready..."
        aws lambda wait function-updated \
            --function-name "$FUNCTION_NAME" \
            --region "$REGION" \
            --profile "$AWS_PROFILE"
        
        echo "Updating configuration..."
        aws lambda update-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --runtime nodejs18.x \
            --handler index.handler \
            --environment Variables="{DYNAMODB_TABLE=$DYNAMODB_TABLE}" \
            --region "$REGION" \
            --profile "$AWS_PROFILE"
    else
        echo "Creating new function..."
        aws lambda create-function \
            --function-name "$FUNCTION_NAME" \
            --runtime nodejs18.x \
            --role "$LAMBDA_ROLE" \
            --handler index.handler \
            --zip-file fileb://function.zip \
            --environment Variables="{DYNAMODB_TABLE=$DYNAMODB_TABLE}" \
            --timeout 30 \
            --memory-size 256 \
            --region "$REGION" \
            --profile "$AWS_PROFILE"
    fi
    
    # Clean up
    rm function.zip
    
    echo "✓ $FUNCTION_NAME deployed successfully"
    
    cd - > /dev/null
}

# Deploy confirm-transcription-mode
deploy_lambda "confirm-transcription-mode" "confirm-transcription-mode"

# Deploy confirm-key
deploy_lambda "confirm-key" "confirm-key"

echo ""
echo "========================================="
echo "✓ All Lambda functions deployed!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Configure API Gateway endpoints"
echo "2. Test endpoints with curl/Postman"
echo "3. Deploy frontend updates"
echo ""
