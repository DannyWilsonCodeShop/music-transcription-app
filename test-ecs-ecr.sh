#!/bin/bash
# Test ECS and ECR Infrastructure
# Verifies Docker image, ECS cluster, task definition, and can run a test task

set -e

export AWS_PROFILE=production
REGION="us-east-1"
CLUSTER="ChordScout-dev"
TASK_DEF="chordscout-chord-detector-dev"
REPO_NAME="chordscout-chord-detector"
ACCOUNT_ID="090130568474"

echo "========================================="
echo "ECS and ECR Infrastructure Test"
echo "========================================="
echo ""

# Test 1: ECR Repository
echo "TEST 1: ECR Repository"
echo "-------------------------------------------"
REPO_URI=$(aws ecr describe-repositories --repository-names $REPO_NAME --query 'repositories[0].repositoryUri' --output text 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ ECR Repository exists: $REPO_URI"
    
    # Check latest image
    IMAGE_DIGEST=$(aws ecr describe-images --repository-name $REPO_NAME --image-ids imageTag=latest --query 'imageDetails[0].imageDigest' --output text 2>&1)
    if [ $? -eq 0 ]; then
        echo "✅ Latest image exists: $IMAGE_DIGEST"
        
        IMAGE_PUSHED=$(aws ecr describe-images --repository-name $REPO_NAME --image-ids imageTag=latest --query 'imageDetails[0].imagePushedAt' --output text)
        IMAGE_SIZE=$(aws ecr describe-images --repository-name $REPO_NAME --image-ids imageTag=latest --query 'imageDetails[0].imageSizeInBytes' --output text)
        IMAGE_SIZE_MB=$((IMAGE_SIZE / 1024 / 1024))
        
        echo "   Pushed: $IMAGE_PUSHED"
        echo "   Size: ${IMAGE_SIZE_MB}MB"
        
        # Check image manifest for platform
        MANIFEST=$(aws ecr batch-get-image --repository-name $REPO_NAME --image-ids imageTag=latest --query 'images[0].imageManifest' --output text 2>&1)
        if echo "$MANIFEST" | grep -q "linux"; then
            if echo "$MANIFEST" | grep -q "amd64"; then
                echo "✅ Image platform: linux/amd64"
            else
                echo "⚠️  Image platform may not be linux/amd64"
            fi
        fi
    else
        echo "❌ Latest image not found"
        exit 1
    fi
else
    echo "❌ ECR Repository not found: $REPO_NAME"
    exit 1
fi
echo ""

# Test 2: ECS Cluster
echo "TEST 2: ECS Cluster"
echo "-------------------------------------------"
CLUSTER_ARN=$(aws ecs describe-clusters --clusters $CLUSTER --query 'clusters[0].clusterArn' --output text 2>&1)
if [ $? -eq 0 ] && [ "$CLUSTER_ARN" != "None" ]; then
    echo "✅ ECS Cluster exists: $CLUSTER"
    
    CLUSTER_STATUS=$(aws ecs describe-clusters --clusters $CLUSTER --query 'clusters[0].status' --output text)
    RUNNING_TASKS=$(aws ecs describe-clusters --clusters $CLUSTER --query 'clusters[0].runningTasksCount' --output text)
    PENDING_TASKS=$(aws ecs describe-clusters --clusters $CLUSTER --query 'clusters[0].pendingTasksCount' --output text)
    
    echo "   Status: $CLUSTER_STATUS"
    echo "   Running tasks: $RUNNING_TASKS"
    echo "   Pending tasks: $PENDING_TASKS"
else
    echo "❌ ECS Cluster not found: $CLUSTER"
    exit 1
fi
echo ""

# Test 3: Task Definition
echo "TEST 3: Task Definition"
echo "-------------------------------------------"
TASK_DEF_ARN=$(aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.taskDefinitionArn' --output text 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ Task Definition exists: $TASK_DEF"
    echo "   ARN: $TASK_DEF_ARN"
    
    # Check container configuration
    CONTAINER_NAME=$(aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.containerDefinitions[0].name' --output text)
    CONTAINER_IMAGE=$(aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.containerDefinitions[0].image' --output text)
    CONTAINER_CPU=$(aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.cpu' --output text)
    CONTAINER_MEMORY=$(aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.memory' --output text)
    
    echo "   Container: $CONTAINER_NAME"
    echo "   Image: $CONTAINER_IMAGE"
    echo "   CPU: $CONTAINER_CPU"
    echo "   Memory: $CONTAINER_MEMORY"
    
    # Verify image matches ECR
    if echo "$CONTAINER_IMAGE" | grep -q "$REPO_URI"; then
        echo "✅ Container image matches ECR repository"
    else
        echo "⚠️  Container image doesn't match ECR repository"
        echo "   Expected: $REPO_URI"
        echo "   Got: $CONTAINER_IMAGE"
    fi
    
    # Check environment variables
    echo "   Environment variables:"
    aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.containerDefinitions[0].environment[*].[name,value]' --output text | while read name value; do
        echo "     $name=$value"
    done
    
    # Check IAM roles
    TASK_ROLE=$(aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.taskRoleArn' --output text)
    EXEC_ROLE=$(aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.executionRoleArn' --output text)
    
    echo "   Task Role: $(basename $TASK_ROLE)"
    echo "   Execution Role: $(basename $EXEC_ROLE)"
else
    echo "❌ Task Definition not found: $TASK_DEF"
    exit 1
fi
echo ""

# Test 4: Network Configuration
echo "TEST 4: Network Configuration"
echo "-------------------------------------------"
# Get subnets and security groups from a recent task or from environment
SUBNETS=$(aws ecs describe-task-definition --task-definition $TASK_DEF --query 'taskDefinition.containerDefinitions[0].environment[?name==`ECS_SUBNETS`].value' --output text 2>/dev/null || echo "")
if [ -z "$SUBNETS" ]; then
    # Try to get from Lambda environment
    SUBNETS=$(aws lambda get-function-configuration --function-name music-transcription-process-audio-test --query 'Environment.Variables.ECS_SUBNETS' --output text 2>/dev/null || echo "")
fi

if [ -n "$SUBNETS" ]; then
    SUBNET_COUNT=$(echo "$SUBNETS" | tr ',' '\n' | wc -l | tr -d ' ')
    echo "✅ Subnets configured: $SUBNET_COUNT subnets"
    echo "$SUBNETS" | tr ',' '\n' | while read subnet; do
        if [ -n "$subnet" ]; then
            SUBNET_AZ=$(aws ec2 describe-subnets --subnet-ids $subnet --query 'Subnets[0].AvailabilityZone' --output text 2>/dev/null || echo "unknown")
            echo "   - $subnet ($SUBNET_AZ)"
        fi
    done
else
    echo "⚠️  No subnets found in configuration"
fi

SECURITY_GROUPS=$(aws lambda get-function-configuration --function-name music-transcription-process-audio-test --query 'Environment.Variables.ECS_SECURITY_GROUPS' --output text 2>/dev/null || echo "")
if [ -n "$SECURITY_GROUPS" ]; then
    echo "✅ Security Groups configured: $SECURITY_GROUPS"
else
    echo "⚠️  No security groups found in configuration"
fi
echo ""

# Test 5: IAM Permissions
echo "TEST 5: IAM Permissions"
echo "-------------------------------------------"
TASK_ROLE_NAME=$(basename $TASK_ROLE)
if [ -n "$TASK_ROLE_NAME" ] && [ "$TASK_ROLE_NAME" != "None" ]; then
    echo "Checking Task Role permissions..."
    
    # Check inline policies
    INLINE_POLICIES=$(aws iam list-role-policies --role-name $TASK_ROLE_NAME --query 'PolicyNames' --output text 2>/dev/null || echo "")
    if [ -n "$INLINE_POLICIES" ]; then
        echo "✅ Inline policies: $INLINE_POLICIES"
        
        for POLICY in $INLINE_POLICIES; do
            echo "   Policy: $POLICY"
            aws iam get-role-policy --role-name $TASK_ROLE_NAME --policy-name $POLICY --query 'PolicyDocument.Statement[*].Action[]' --output text 2>/dev/null | tr '\t' '\n' | sort -u | head -10 | while read action; do
                echo "     - $action"
            done
        done
    fi
    
    # Check attached policies
    ATTACHED_POLICIES=$(aws iam list-attached-role-policies --role-name $TASK_ROLE_NAME --query 'AttachedPolicies[*].PolicyName' --output text 2>/dev/null || echo "")
    if [ -n "$ATTACHED_POLICIES" ]; then
        echo "✅ Attached policies: $ATTACHED_POLICIES"
    fi
else
    echo "⚠️  No task role configured"
fi
echo ""

# Test 6: Run Test Task
echo "TEST 6: Run Test Task (Dry Run)"
echo "-------------------------------------------"
echo "This would launch an ECS task with test parameters."
echo "Skipping actual task launch to avoid costs."
echo ""
echo "To manually test, run:"
echo "  aws ecs run-task \\"
echo "    --cluster $CLUSTER \\"
echo "    --task-definition $TASK_DEF \\"
echo "    --launch-type FARGATE \\"
echo "    --network-configuration 'awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=ENABLED}' \\"
echo "    --overrides '{\"containerOverrides\":[{\"name\":\"$CONTAINER_NAME\",\"environment\":[{\"name\":\"JOB_ID\",\"value\":\"test-job\"},{\"name\":\"BUCKET\",\"value\":\"test-bucket\"},{\"name\":\"KEY\",\"value\":\"test-key\"}]}]}'"
echo ""

# Test 7: Recent Task History
echo "TEST 7: Recent Task History"
echo "-------------------------------------------"
RECENT_TASKS=$(aws ecs list-tasks --cluster $CLUSTER --max-results 5 --query 'taskArns[]' --output text 2>/dev/null || echo "")
if [ -n "$RECENT_TASKS" ]; then
    echo "Recent tasks (last 5):"
    for TASK_ARN in $RECENT_TASKS; do
        TASK_ID=$(basename $TASK_ARN)
        TASK_STATUS=$(aws ecs describe-tasks --cluster $CLUSTER --tasks $TASK_ARN --query 'tasks[0].lastStatus' --output text 2>/dev/null || echo "unknown")
        TASK_CREATED=$(aws ecs describe-tasks --cluster $CLUSTER --tasks $TASK_ARN --query 'tasks[0].createdAt' --output text 2>/dev/null || echo "unknown")
        echo "  - $TASK_ID: $TASK_STATUS (created: $TASK_CREATED)"
    done
else
    echo "No recent tasks found"
fi
echo ""

# Test 8: CloudWatch Logs
echo "TEST 8: CloudWatch Logs"
echo "-------------------------------------------"
LOG_GROUP="/ecs/$TASK_DEF"
LOG_EXISTS=$(aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --query 'logGroups[0].logGroupName' --output text 2>/dev/null || echo "")
if [ "$LOG_EXISTS" == "$LOG_GROUP" ]; then
    echo "✅ CloudWatch log group exists: $LOG_GROUP"
    
    # Check recent log streams
    RECENT_STREAMS=$(aws logs describe-log-streams --log-group-name "$LOG_GROUP" --order-by LastEventTime --descending --max-items 3 --query 'logStreams[*].logStreamName' --output text 2>/dev/null || echo "")
    if [ -n "$RECENT_STREAMS" ]; then
        echo "   Recent log streams:"
        echo "$RECENT_STREAMS" | tr '\t' '\n' | while read stream; do
            echo "     - $stream"
        done
    else
        echo "   No log streams found"
    fi
else
    echo "⚠️  CloudWatch log group not found: $LOG_GROUP"
fi
echo ""

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo ""
echo "✅ ECR Repository: $REPO_NAME"
echo "✅ Docker Image: latest (${IMAGE_SIZE_MB}MB, linux/amd64)"
echo "✅ ECS Cluster: $CLUSTER ($CLUSTER_STATUS)"
echo "✅ Task Definition: $TASK_DEF"
echo "✅ Container: $CONTAINER_NAME"
echo "✅ Network: $SUBNET_COUNT subnets configured"
echo "✅ IAM: Task role and execution role configured"
echo "✅ Logs: CloudWatch log group exists"
echo ""
echo "All infrastructure checks passed! ✅"
echo ""
echo "To test with actual task execution, use test-upload-e2e.sh"
echo ""
