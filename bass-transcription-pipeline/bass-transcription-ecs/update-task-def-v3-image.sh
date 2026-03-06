#!/bin/bash
# Update task definition to use the new v3.0 Docker image

set -e

export AWS_PROFILE=chordscout
REGION="us-east-1"
TASK_FAMILY="chordscout-chord-detector-dev"
NEW_IMAGE="090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector-v3-dev:latest"

echo "=========================================="
echo "Updating Task Definition with v3.0 Image"
echo "=========================================="
echo ""

# Get current task definition
echo "Fetching current task definition..."
TASK_DEF=$(aws ecs describe-task-definition \
  --task-definition $TASK_FAMILY \
  --region $REGION \
  --query 'taskDefinition' \
  --output json)

# Update the image
echo "Updating Docker image..."
echo "  Old image: $(echo "$TASK_DEF" | jq -r '.containerDefinitions[0].image')"
echo "  New image: $NEW_IMAGE"

UPDATED_TASK_DEF=$(echo "$TASK_DEF" | jq --arg img "$NEW_IMAGE" '
  .containerDefinitions[0].image = $img |
  del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)
')

# Register new task definition
echo ""
echo "Registering new task definition..."
NEW_TASK_DEF=$(aws ecs register-task-definition \
  --region $REGION \
  --cli-input-json "$UPDATED_TASK_DEF" \
  --query 'taskDefinition.{family:family,revision:revision,status:status,image:containerDefinitions[0].image}' \
  --output json)

REVISION=$(echo $NEW_TASK_DEF | jq -r '.revision')
STATUS=$(echo $NEW_TASK_DEF | jq -r '.status')

echo ""
echo "✓ New task definition registered"
echo "  Family: $TASK_FAMILY"
echo "  Revision: $REVISION"
echo "  Status: $STATUS"
echo ""

# Verify the image
echo "Verifying image in new task definition..."
VERIFY_IMAGE=$(aws ecs describe-task-definition \
  --task-definition $TASK_FAMILY:$REVISION \
  --region $REGION \
  --query 'taskDefinition.containerDefinitions[0].image' \
  --output text)

if [ "$VERIFY_IMAGE" = "$NEW_IMAGE" ]; then
  echo "✓ Image verified: $VERIFY_IMAGE"
else
  echo "✗ Image mismatch!"
  echo "  Expected: $NEW_IMAGE"
  echo "  Got: $VERIFY_IMAGE"
  exit 1
fi

echo ""
echo "=========================================="
echo "✓ Task Definition Updated"
echo "=========================================="
echo ""
echo "Task Definition: $TASK_FAMILY:$REVISION"
echo "Image: $NEW_IMAGE"
echo ""
echo "The Lambda trigger will automatically use this new revision"
echo "for all new ECS tasks."
echo ""
echo "Next step: Run Phase 3 test"
echo "  bash test-phase3-e2e.sh \"public/04 That_s What I Like.m4a\""
echo ""
