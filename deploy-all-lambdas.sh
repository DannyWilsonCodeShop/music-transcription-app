#!/bin/bash

echo "🚀 Deploying all Lambda functions..."
echo ""

# Array of Lambda functions to deploy
FUNCTIONS=("create-job" "get-job-status" "lyrics-transcriber" "chord-detector-trigger" "pdf-generator")

for FUNC in "${FUNCTIONS[@]}"; do
    echo "📦 Deploying $FUNC..."
    
    FUNC_DIR="backend/functions-v2/$FUNC"
    
    if [ -d "$FUNC_DIR" ]; then
        cd "$FUNC_DIR"
        
        # Install dependencies if package.json exists
        if [ -f "package.json" ]; then
            echo "   Installing Node.js dependencies..."
            npm install --production --silent 2>/dev/null || true
        fi
        
        # Create zip file
        rm -f function.zip
        
        if [ -f "package.json" ]; then
            # Node.js function
            zip -q -r function.zip . -x "*.git*" -x "*.zip"
        else
            # Python function
            zip -q -r function.zip . -x "*.git*" -x "*.zip" -x "__pycache__/*"
        fi
        
        # Update Lambda function
        FUNC_NAME="chordscout-v2-$FUNC-dev"
        
        echo "   Updating Lambda function: $FUNC_NAME"
        aws lambda update-function-code \
          --function-name $FUNC_NAME \
          --zip-file fileb://function.zip \
          --region us-east-1 \
          --output text --query 'LastUpdateStatus' 2>/dev/null || echo "   ⚠️  Function not found or error"
        
        cd - > /dev/null
        echo "   ✅ Done"
    else
        echo "   ⚠️  Directory not found: $FUNC_DIR"
    fi
    echo ""
done

echo "✅ All Lambda functions deployed!"
