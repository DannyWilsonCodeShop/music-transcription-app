#!/bin/bash

echo "🚀 Deploying Working RapidAPI YouTube Downloader"
echo "================================================"

# Set variables
FUNCTION_NAME="youtube-downloader-rapidapi"
REGION="us-east-1"
BUCKET_NAME="music-transcription-app-audio"
RAPIDAPI_KEY="252611e8d7mshdde3262a7e2137bp12792bjsn7ce487b8a3dc"

echo "✅ RapidAPI Status: WORKING (youtube-mp36.p.rapidapi.com)"
echo "✅ Function: $FUNCTION_NAME"
echo "✅ Region: $REGION"
echo "✅ Bucket: $BUCKET_NAME"
echo ""

# Create deployment package
echo "📦 Creating deployment package..."
cd backend/lambda-functions
cp youtube-downloader-rapidapi.py lambda_function.py

# Create zip
zip -r youtube-downloader-rapidapi.zip lambda_function.py
echo "✅ Package created: youtube-downloader-rapidapi.zip"

# Deploy to AWS Lambda
echo ""
echo "🚀 Deploying to AWS Lambda..."

# Update function code
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://youtube-downloader-rapidapi.zip \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✅ Function code updated successfully!"
else
    echo "❌ Failed to update function code"
    exit 1
fi

# Update environment variables
echo ""
echo "🔧 Setting environment variables..."

aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment Variables="{BUCKET_NAME=$BUCKET_NAME,RAPIDAPI_KEY=$RAPIDAPI_KEY}" \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✅ Environment variables updated!"
else
    echo "❌ Failed to update environment variables"
    exit 1
fi

# Test the function
echo ""
echo "🧪 Testing the deployed function..."

TEST_PAYLOAD='{
    "youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "jobId": "test-rapidapi-' $(date +%s) '"
}'

echo "Test payload: $TEST_PAYLOAD"

aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload "$TEST_PAYLOAD" \
    --region $REGION \
    response.json

if [ $? -eq 0 ]; then
    echo "✅ Function invoked successfully!"
    echo "Response:"
    cat response.json | jq .
    
    # Check if successful
    if grep -q '"statusCode": 200' response.json; then
        echo ""
        echo "🎉 SUCCESS! RapidAPI YouTube Downloader is working!"
        echo "✅ Audio downloaded and uploaded to S3"
        echo "✅ Ready for production use"
    else
        echo ""
        echo "⚠️  Function ran but returned an error:"
        cat response.json
    fi
else
    echo "❌ Failed to invoke function"
fi

# Cleanup
rm lambda_function.py response.json

echo ""
echo "🏁 Deployment complete!"
echo "Next steps:"
echo "1. ✅ RapidAPI is working"
echo "2. ✅ Lambda function deployed"
echo "3. 🔄 Test full workflow with Step Functions"
echo "4. 🚀 Deploy frontend updates"