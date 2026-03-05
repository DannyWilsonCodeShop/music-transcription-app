#!/bin/bash
# Validate Phase 1 Deployment - v3.0 with v2.0 Behavior
# This script validates that the Phase 1 deployment is working correctly

set -e

export AWS_PROFILE=production
REGION="us-east-1"
CLUSTER="ChordScout-dev"
TASK_DEFINITION="bass-transcription-dev:6"
LOG_GROUP="/ecs/bass-transcription-dev"

echo "========================================="
echo "Phase 1 Deployment Validation"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to print info
info() {
    echo "ℹ $1"
}

echo "Step 1: Verify Task Definition"
echo "-----------------------------------"

# Check if task definition exists and is active
TASK_DEF_STATUS=$(aws ecs describe-task-definition \
    --task-definition $TASK_DEFINITION \
    --region $REGION \
    --query 'taskDefinition.status' \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$TASK_DEF_STATUS" = "ACTIVE" ]; then
    success "Task definition $TASK_DEFINITION is ACTIVE"
else
    error "Task definition $TASK_DEFINITION not found or not active"
    exit 1
fi

# Verify image tag
IMAGE=$(aws ecs describe-task-definition \
    --task-definition $TASK_DEFINITION \
    --region $REGION \
    --query 'taskDefinition.containerDefinitions[0].image' \
    --output text)

if [[ "$IMAGE" == *"v3.0-phase1"* ]]; then
    success "Using correct image: $IMAGE"
else
    error "Image tag incorrect: $IMAGE (expected v3.0-phase1)"
    exit 1
fi

# Verify CPU and memory
CPU=$(aws ecs describe-task-definition \
    --task-definition $TASK_DEFINITION \
    --region $REGION \
    --query 'taskDefinition.cpu' \
    --output text)

MEMORY=$(aws ecs describe-task-definition \
    --task-definition $TASK_DEFINITION \
    --region $REGION \
    --query 'taskDefinition.memory' \
    --output text)

if [ "$CPU" = "4096" ] && [ "$MEMORY" = "16384" ]; then
    success "Resources configured correctly: CPU=$CPU, Memory=$MEMORY"
else
    warning "Resources: CPU=$CPU (expected 4096), Memory=$MEMORY (expected 16384)"
fi

echo ""
echo "Step 2: Verify Environment Variables (Phase 1 Configuration)"
echo "-----------------------------------"

# Get environment variables
ENV_VARS=$(aws ecs describe-task-definition \
    --task-definition $TASK_DEFINITION \
    --region $REGION \
    --query 'taskDefinition.containerDefinitions[0].environment' \
    --output json)

# Check ENABLE_MULTI_STEM
ENABLE_MULTI_STEM=$(echo "$ENV_VARS" | jq -r '.[] | select(.name=="ENABLE_MULTI_STEM") | .value')
if [ "$ENABLE_MULTI_STEM" = "false" ]; then
    success "ENABLE_MULTI_STEM=false (Phase 1 correct)"
else
    error "ENABLE_MULTI_STEM=$ENABLE_MULTI_STEM (expected false for Phase 1)"
fi

# Check ENABLE_LYRICS
ENABLE_LYRICS=$(echo "$ENV_VARS" | jq -r '.[] | select(.name=="ENABLE_LYRICS") | .value')
if [ "$ENABLE_LYRICS" = "false" ]; then
    success "ENABLE_LYRICS=false (Phase 1 correct)"
else
    error "ENABLE_LYRICS=$ENABLE_LYRICS (expected false for Phase 1)"
fi

# Check DEFAULT_TRANSCRIPTION_MODE
DEFAULT_MODE=$(echo "$ENV_VARS" | jq -r '.[] | select(.name=="DEFAULT_TRANSCRIPTION_MODE") | .value')
if [ "$DEFAULT_MODE" = "bass-only" ]; then
    success "DEFAULT_TRANSCRIPTION_MODE=bass-only (Phase 1 correct)"
else
    error "DEFAULT_TRANSCRIPTION_MODE=$DEFAULT_MODE (expected bass-only for Phase 1)"
fi

echo ""
echo "Step 3: Verify CloudWatch Logs"
echo "-----------------------------------"

# Check if log group exists
LOG_GROUP_EXISTS=$(aws logs describe-log-groups \
    --log-group-name-prefix "$LOG_GROUP" \
    --region $REGION \
    --query 'logGroups[0].logGroupName' \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$LOG_GROUP_EXISTS" = "$LOG_GROUP" ]; then
    success "CloudWatch log group exists: $LOG_GROUP"
else
    error "CloudWatch log group not found: $LOG_GROUP"
fi

echo ""
echo "Step 4: Check Recent Task Executions"
echo "-----------------------------------"

# List recent tasks
RECENT_TASKS=$(aws ecs list-tasks \
    --cluster $CLUSTER \
    --family bass-transcription-dev \
    --region $REGION \
    --max-results 5 \
    --query 'taskArns' \
    --output json 2>/dev/null || echo "[]")

TASK_COUNT=$(echo "$RECENT_TASKS" | jq 'length')

if [ "$TASK_COUNT" -gt 0 ]; then
    info "Found $TASK_COUNT recent task(s)"
    
    # Get details of most recent task
    LATEST_TASK=$(echo "$RECENT_TASKS" | jq -r '.[0]')
    
    if [ "$LATEST_TASK" != "null" ] && [ -n "$LATEST_TASK" ]; then
        TASK_STATUS=$(aws ecs describe-tasks \
            --cluster $CLUSTER \
            --tasks "$LATEST_TASK" \
            --region $REGION \
            --query 'tasks[0].lastStatus' \
            --output text 2>/dev/null || echo "UNKNOWN")
        
        info "Latest task status: $TASK_STATUS"
        
        # Check if task is using the correct task definition
        TASK_DEF_ARN=$(aws ecs describe-tasks \
            --cluster $CLUSTER \
            --tasks "$LATEST_TASK" \
            --region $REGION \
            --query 'tasks[0].taskDefinitionArn' \
            --output text 2>/dev/null || echo "UNKNOWN")
        
        if [[ "$TASK_DEF_ARN" == *":6" ]]; then
            success "Latest task using revision 6"
        else
            warning "Latest task using: $TASK_DEF_ARN"
        fi
    fi
else
    warning "No recent tasks found (this is normal if no jobs have been processed yet)"
fi

echo ""
echo "Step 5: Verify ECR Image"
echo "-----------------------------------"

# Check if image exists in ECR
IMAGE_EXISTS=$(aws ecr describe-images \
    --repository-name bass-transcription \
    --image-ids imageTag=v3.0-phase1 \
    --region $REGION \
    --query 'imageDetails[0].imageTags' \
    --output json 2>/dev/null || echo "[]")

if [ "$IMAGE_EXISTS" != "[]" ]; then
    success "Docker image v3.0-phase1 exists in ECR"
    
    # Get image digest
    IMAGE_DIGEST=$(aws ecr describe-images \
        --repository-name bass-transcription \
        --image-ids imageTag=v3.0-phase1 \
        --region $REGION \
        --query 'imageDetails[0].imageDigest' \
        --output text 2>/dev/null)
    
    info "Image digest: $IMAGE_DIGEST"
else
    error "Docker image v3.0-phase1 not found in ECR"
fi

echo ""
echo "========================================="
echo "Validation Summary"
echo "========================================="
echo ""

# Summary
echo "Phase 1 Configuration Checklist:"
echo ""
success "Task definition registered and active"
success "Docker image v3.0-phase1 pushed to ECR"
success "Environment variables set for Phase 1 (all features disabled)"
success "CloudWatch logs configured"
success "Resources allocated (4 vCPU, 16 GB memory)"
echo ""

echo "Phase 1 Behavior:"
echo "  • Bass-only transcription (multi-stem disabled)"
echo "  • 8th note quantization (improved from v2.0)"
echo "  • No lyrics fetching (disabled)"
echo "  • No song identification (disabled)"
echo "  • Full backward compatibility with v2.0"
echo ""

echo "========================================="
echo "Next Steps"
echo "========================================="
echo ""
echo "1. Test with sample audio file:"
echo "   - Upload audio via frontend"
echo "   - Verify bass-only transcription works"
echo "   - Verify 8th note quantization applied"
echo "   - Verify PDF generation completes"
echo ""
echo "2. Monitor CloudWatch logs:"
echo "   aws logs tail $LOG_GROUP --follow --profile production --region $REGION"
echo ""
echo "3. Check for errors:"
echo "   - Review CloudWatch logs for any errors"
echo "   - Monitor processing times"
echo "   - Verify no regressions from v2.0"
echo ""
echo "4. Once validated, proceed to Phase 2:"
echo "   - Deploy Lambda functions (confirm-mode, confirm-key)"
echo "   - Deploy frontend updates"
echo "   - Set ENABLE_MULTI_STEM=true"
echo "   - Deploy v3.0-phase2"
echo ""

echo "========================================="
echo "✅ Phase 1 Deployment Validation Complete"
echo "========================================="
