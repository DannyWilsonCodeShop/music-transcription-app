#!/bin/bash
# Increase ECS task memory for stem separation

set -e

export AWS_PROFILE=chordscout
REGION="us-east-1"
TASK_FAMILY="chordscout-chord-detector-dev"

# Fargate CPU/Memory combinations:
# 1024 (1 vCPU) = 2GB, 3GB, 4GB, 5GB, 6GB, 7GB, 8GB
# 2048 (2 vCPU) = 4GB-16GB
# 4096 (4 vCPU) = 8GB-30GB

NEW_CPU="2048"      # 2 vCPU
NEW_MEMORY="8192"   # 8 GB

echo "=========================================="
echo "Increasing ECS Task Memory"
echo "=========================================="
echo ""

# Get current task definition
echo "Fetching current task definition..."
TASK_DEF=$(aws ecs describe-task-definition \
  --task-definition $TASK_FAMILY \
  --region $REGION \
  --query 'taskDefinition' \
  --output json)

CURRENT_CPU=$(echo "$TASK_DEF" | jq -r '.cpu')
CURRENT_MEMORY=$(echo "$TASK_DEF" | jq -r '.memory')

echo "Current allocation:"
echo "  CPU: $CURRENT_CPU ($(($CURRENT_CPU / 1024)) vCPU)"
echo "  Memory: $CURRENT_MEMORY MB ($(($CURRENT_MEMORY / 1024)) GB)"
echo ""
echo "New allocation:"
echo "  CPU: $NEW_CPU ($(($NEW_CPU / 1024)) vCPU)"
echo "  Memory: $NEW_MEMORY MB ($(($NEW_MEMORY / 1024)) GB)"
echo ""

# Update CPU and memory
UPDATED_TASK_DEF=$(echo "$TASK_DEF" | jq \
  --arg cpu "$NEW_CPU" \
  --arg mem "$NEW_MEMORY" '
  .cpu = $cpu |
  .memory = $mem |
  del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)
')

# Register new task definition
echo "Registering new task definition..."
NEW_TASK_DEF=$(aws ecs register-task-definition \
  --region $REGION \
  --cli-input-json "$UPDATED_TASK_DEF" \
  --query 'taskDefinition.{family:family,revision:revision,cpu:cpu,memory:memory}' \
  --output json)

REVISION=$(echo $NEW_TASK_DEF | jq -r '.revision')

echo ""
echo "✓ New task definition registered"
echo "  Family: $TASK_FAMILY"
echo "  Revision: $REVISION"
echo "  CPU: $NEW_CPU ($(($NEW_CPU / 1024)) vCPU)"
echo "  Memory: $NEW_MEMORY MB ($(($NEW_MEMORY / 1024)) GB)"
echo ""
echo "=========================================="
echo "✓ Memory Increased"
echo "=========================================="
echo ""
echo "Reason: Demucs stem separation requires more memory"
echo "Previous: 1 vCPU, 4 GB RAM"
echo "New: 2 vCPU, 8 GB RAM"
echo ""
echo "Next step: Run Phase 3 test again"
echo ""
