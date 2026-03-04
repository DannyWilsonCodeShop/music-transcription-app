#!/bin/bash
# Comprehensive Pipeline Test for Account 8474
# Tests all components end-to-end

set -e

export AWS_PROFILE=production
EXPECTED_ACCOUNT="090130568474"
REGION="us-east-1"

echo "========================================="
echo "Pipeline End-to-End Test - Account 8474"
echo "========================================="
echo ""

# Verify we're in the correct account
echo "1. Verifying AWS Account..."
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text)
if [ "$CURRENT_ACCOUNT" != "$EXPECTED_ACCOUNT" ]; then
    echo "❌ ERROR: Wrong AWS account!"
    echo "   Expected: $EXPECTED_ACCOUNT"
    echo "   Current:  $CURRENT_ACCOUNT"
    exit 1
fi
echo "✅ Correct account: $CURRENT_ACCOUNT"
echo ""

# Check API Gateway
echo "2. Checking API Gateway..."
API_ID="hfv1glzbxi"
API_ENDPOINT=$(aws apigatewayv2 get-api --api-id $API_ID --query 'ApiEndpoint' --output text 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ API Gateway exists: $API_ENDPOINT"
    
    # Check routes
    echo "   Checking routes..."
    ROUTES=$(aws apigatewayv2 get-routes --api-id $API_ID --query 'Items[*].RouteKey' --output text)
    echo "   Routes: $ROUTES"
    
    if echo "$ROUTES" | grep -q "POST /upload"; then
        echo "   ✅ POST /upload route exists"
    else
        echo "   ❌ POST /upload route missing"
    fi
    
    if echo "$ROUTES" | grep -q "GET /jobs/{jobId}"; then
        echo "   ✅ GET /jobs/{jobId} route exists"
    else
        echo "   ❌ GET /jobs/{jobId} route missing"
    fi
else
    echo "❌ API Gateway not found: $API_ENDPOINT"
    exit 1
fi
echo ""

# Check Lambda Functions
echo "3. Checking Lambda Functions..."
LAMBDAS=(
    "music-transcription-upload-test"
    "music-transcription-process-audio-test"
    "music-transcription-get-job-status-test"
)

for LAMBDA in "${LAMBDAS[@]}"; do
    LAMBDA_ARN=$(aws lambda get-function --function-name $LAMBDA --query 'Configuration.FunctionArn' --output text 2>&1)
    if [ $? -eq 0 ]; then
        if echo "$LAMBDA_ARN" | grep -q "$EXPECTED_ACCOUNT"; then
            echo "✅ $LAMBDA (correct account)"
            
            # Check environment variables
            if [ "$LAMBDA" == "music-transcription-upload-test" ]; then
                JOBS_TABLE=$(aws lambda get-function-configuration --function-name $LAMBDA --query 'Environment.Variables.JOBS_TABLE' --output text)
                echo "   JOBS_TABLE: $JOBS_TABLE"
            fi
            
            if [ "$LAMBDA" == "music-transcription-process-audio-test" ]; then
                ECS_CLUSTER=$(aws lambda get-function-configuration --function-name $LAMBDA --query 'Environment.Variables.ECS_CLUSTER' --output text)
                ECS_TASK=$(aws lambda get-function-configuration --function-name $LAMBDA --query 'Environment.Variables.ECS_TASK_DEFINITION' --output text)
                JOBS_TABLE=$(aws lambda get-function-configuration --function-name $LAMBDA --query 'Environment.Variables.JOBS_TABLE' --output text)
                echo "   ECS_CLUSTER: $ECS_CLUSTER"
                echo "   ECS_TASK_DEFINITION: $ECS_TASK"
                echo "   JOBS_TABLE: $JOBS_TABLE"
            fi
        else
            echo "❌ $LAMBDA (wrong account: $LAMBDA_ARN)"
        fi
    else
        echo "❌ $LAMBDA not found"
    fi
done
echo ""

# Check S3 Buckets
echo "4. Checking S3 Buckets..."
BUCKETS=(
    "music-transcription-audio-test-090130568474"
    "chordscout-audio-temp-dev-090130568474"
    "chordscout-pdfs-dev-090130568474"
)

for BUCKET in "${BUCKETS[@]}"; do
    BUCKET_REGION=$(aws s3api get-bucket-location --bucket $BUCKET --query 'LocationConstraint' --output text 2>&1)
    if [ $? -eq 0 ]; then
        echo "✅ $BUCKET"
        
        # Check event notifications for upload bucket
        if [ "$BUCKET" == "music-transcription-audio-test-090130568474" ]; then
            NOTIFICATION=$(aws s3api get-bucket-notification-configuration --bucket $BUCKET --query 'LambdaFunctionConfigurations[0].LambdaFunctionArn' --output text 2>&1)
            if echo "$NOTIFICATION" | grep -q "music-transcription-process-audio-test"; then
                echo "   ✅ S3 event notification configured"
            else
                echo "   ⚠️  S3 event notification: $NOTIFICATION"
            fi
        fi
    else
        echo "❌ $BUCKET not found"
    fi
done
echo ""

# Check DynamoDB Tables
echo "5. Checking DynamoDB Tables..."
TABLES=(
    "MusicTranscription-Jobs-test"
    "ChordScout-Jobs-V2-dev"
)

for TABLE in "${TABLES[@]}"; do
    TABLE_ARN=$(aws dynamodb describe-table --table-name $TABLE --query 'Table.TableArn' --output text 2>&1)
    if [ $? -eq 0 ]; then
        if echo "$TABLE_ARN" | grep -q "$EXPECTED_ACCOUNT"; then
            echo "✅ $TABLE (correct account)"
            
            # Count items
            ITEM_COUNT=$(aws dynamodb scan --table-name $TABLE --select COUNT --query 'Count' --output text)
            echo "   Items: $ITEM_COUNT"
        else
            echo "❌ $TABLE (wrong account)"
        fi
    else
        echo "❌ $TABLE not found"
    fi
done
echo ""

# Check ECS Cluster and Task Definition
echo "6. Checking ECS Resources..."
CLUSTER="ChordScout-dev"
TASK_DEF="chordscout-chord-detector-dev"

CLUSTER_ARN=$(aws ecs describe-clusters --clusters $CLUSTER --query 'clusters[0].clusterArn' --output text 2>&1)
if [ $? -eq 0 ] && echo "$CLUSTER_ARN" | grep -q "$EXPECTED_ACCOUNT"; then
    echo "✅ ECS Cluster: $CLUSTER"
    
    # Check task definition
    TASK_DEF_ARN=$(aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.taskDefinitionArn' --output text 2>&1)
    if [ $? -eq 0 ]; then
        echo "✅ Task Definition: $TASK_DEF"
        
        # Check container name
        CONTAINER_NAME=$(aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.containerDefinitions[0].name' --output text)
        echo "   Container name: $CONTAINER_NAME"
        
        # Check image
        IMAGE=$(aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.containerDefinitions[0].image' --output text)
        echo "   Image: $IMAGE"
        
        # Check environment variables
        echo "   Environment variables:"
        aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.containerDefinitions[0].environment[*].[name,value]' --output text | while read name value; do
            echo "     $name=$value"
        done
    else
        echo "❌ Task Definition not found: $TASK_DEF"
    fi
else
    echo "❌ ECS Cluster not found: $CLUSTER"
fi
echo ""

# Check ECR Repository
echo "7. Checking ECR Repository..."
REPO_NAME="chordscout-chord-detector"
REPO_URI=$(aws ecr describe-repositories --repository-names $REPO_NAME --query 'repositories[0].repositoryUri' --output text 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ ECR Repository: $REPO_URI"
    
    # Check latest image
    IMAGE_DIGEST=$(aws ecr describe-images --repository-name $REPO_NAME --image-ids imageTag=latest --query 'imageDetails[0].imageDigest' --output text 2>&1)
    IMAGE_PUSHED=$(aws ecr describe-images --repository-name $REPO_NAME --image-ids imageTag=latest --query 'imageDetails[0].imagePushedAt' --output text 2>&1)
    echo "   Latest image digest: $IMAGE_DIGEST"
    echo "   Pushed at: $IMAGE_PUSHED"
else
    echo "❌ ECR Repository not found: $REPO_NAME"
fi
echo ""

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo ""
echo "Account: $CURRENT_ACCOUNT ✅"
echo "API Gateway: hfv1glzbxi ✅"
echo "Lambda Functions: 3 checked"
echo "S3 Buckets: 3 checked"
echo "DynamoDB Tables: 2 checked"
echo "ECS Resources: Cluster + Task Definition"
echo "ECR Repository: $REPO_NAME"
echo ""
echo "Next: Run functional test with actual file upload"
echo ""
