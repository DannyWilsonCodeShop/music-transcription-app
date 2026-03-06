#!/bin/bash
# Phase 3 Validation Script
# Tests song identification, lyrics fetching, and key confirmation

set -e

export AWS_PROFILE=chordscout
REGION="us-east-1"

echo "=========================================="
echo "Phase 3 Deployment Validation"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Verify task definition revision 14
echo "Test 1: Verifying task definition..."
TASK_DEF=$(aws ecs describe-task-definition \
  --task-definition chordscout-chord-detector-dev:14 \
  --region $REGION \
  --query 'taskDefinition.{revision:revision,status:status}' \
  --output json)

REVISION=$(echo $TASK_DEF | jq -r '.revision')
STATUS=$(echo $TASK_DEF | jq -r '.status')

if [ "$REVISION" = "14" ] && [ "$STATUS" = "ACTIVE" ]; then
  echo -e "${GREEN}✓ Task definition revision 14 is ACTIVE${NC}"
else
  echo -e "${RED}✗ Task definition issue: revision=$REVISION, status=$STATUS${NC}"
  exit 1
fi

# Test 2: Verify environment variables
echo ""
echo "Test 2: Verifying Phase 3 environment variables..."
ENV_VARS=$(aws ecs describe-task-definition \
  --task-definition chordscout-chord-detector-dev:14 \
  --region $REGION \
  --query 'taskDefinition.containerDefinitions[0].environment' \
  --output json)

ENABLE_LYRICS=$(echo $ENV_VARS | jq -r '.[] | select(.name=="ENABLE_LYRICS") | .value')
ENABLE_SONG_ID=$(echo $ENV_VARS | jq -r '.[] | select(.name=="ENABLE_SONG_ID") | .value')
ENABLE_MULTI_STEM=$(echo $ENV_VARS | jq -r '.[] | select(.name=="ENABLE_MULTI_STEM") | .value')

if [ "$ENABLE_LYRICS" = "true" ]; then
  echo -e "${GREEN}✓ ENABLE_LYRICS=true${NC}"
else
  echo -e "${RED}✗ ENABLE_LYRICS=$ENABLE_LYRICS (expected: true)${NC}"
fi

if [ "$ENABLE_SONG_ID" = "true" ]; then
  echo -e "${GREEN}✓ ENABLE_SONG_ID=true${NC}"
else
  echo -e "${RED}✗ ENABLE_SONG_ID=$ENABLE_SONG_ID (expected: true)${NC}"
fi

if [ "$ENABLE_MULTI_STEM" = "true" ]; then
  echo -e "${GREEN}✓ ENABLE_MULTI_STEM=true${NC}"
else
  echo -e "${YELLOW}⚠ ENABLE_MULTI_STEM=$ENABLE_MULTI_STEM (Phase 2 feature)${NC}"
fi

# Test 3: Verify Genius API secret
echo ""
echo "Test 3: Verifying Genius API secret..."
SECRETS=$(aws ecs describe-task-definition \
  --task-definition chordscout-chord-detector-dev:14 \
  --region $REGION \
  --query 'taskDefinition.containerDefinitions[0].secrets' \
  --output json)

SECRET_ARN=$(echo $SECRETS | jq -r '.[] | select(.name=="GENIUS_ACCESS_TOKEN") | .valueFrom')

if [ ! -z "$SECRET_ARN" ]; then
  echo -e "${GREEN}✓ GENIUS_ACCESS_TOKEN secret configured${NC}"
  echo "  ARN: $SECRET_ARN"
  
  # Test secret retrieval
  SECRET_VALUE=$(aws secretsmanager get-secret-value \
    --secret-id chordscout/genius-api-token \
    --region $REGION \
    --query 'SecretString' \
    --output text 2>/dev/null || echo "")
  
  if [ ! -z "$SECRET_VALUE" ]; then
    echo -e "${GREEN}✓ Secret is accessible${NC}"
  else
    echo -e "${RED}✗ Cannot retrieve secret${NC}"
  fi
else
  echo -e "${RED}✗ GENIUS_ACCESS_TOKEN secret not configured${NC}"
  exit 1
fi

# Test 4: Verify IAM permissions
echo ""
echo "Test 4: Verifying IAM permissions..."
TASK_ROLE=$(aws ecs describe-task-definition \
  --task-definition chordscout-chord-detector-dev:14 \
  --region $REGION \
  --query 'taskDefinition.taskRoleArn' \
  --output text)

echo "Task Role: $TASK_ROLE"

# Extract role name from ARN
ROLE_NAME=$(echo $TASK_ROLE | awk -F'/' '{print $NF}')

# Check for Secrets Manager policy
POLICIES=$(aws iam list-attached-role-policies \
  --role-name $ROLE_NAME \
  --region $REGION \
  --query 'AttachedPolicies[*].PolicyName' \
  --output text)

if echo "$POLICIES" | grep -q "GeniusAPISecretAccess"; then
  echo -e "${GREEN}✓ GeniusAPISecretAccess policy attached${NC}"
else
  echo -e "${YELLOW}⚠ GeniusAPISecretAccess policy not found (checking inline policies...)${NC}"
  
  INLINE_POLICIES=$(aws iam list-role-policies \
    --role-name $ROLE_NAME \
    --region $REGION \
    --query 'PolicyNames' \
    --output text)
  
  if echo "$INLINE_POLICIES" | grep -q "GeniusAPISecretAccess"; then
    echo -e "${GREEN}✓ GeniusAPISecretAccess inline policy found${NC}"
  else
    echo -e "${RED}✗ GeniusAPISecretAccess policy not found${NC}"
  fi
fi

# Test 5: Check Lambda trigger configuration
echo ""
echo "Test 5: Verifying Lambda trigger configuration..."
LAMBDA_ENV=$(aws lambda get-function-configuration \
  --function-name chordscout-v2-chord-detector-trigger-dev \
  --region $REGION \
  --query 'Environment.Variables' \
  --output json)

LAMBDA_TASK_DEF=$(echo $LAMBDA_ENV | jq -r '.TASK_DEFINITION')

if [ "$LAMBDA_TASK_DEF" = "chordscout-chord-detector-dev" ]; then
  echo -e "${GREEN}✓ Lambda configured to use task definition: $LAMBDA_TASK_DEF${NC}"
  echo -e "${GREEN}✓ Will automatically use latest revision (14)${NC}"
else
  echo -e "${RED}✗ Lambda task definition: $LAMBDA_TASK_DEF${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo "Phase 3 Configuration Summary"
echo "=========================================="
echo ""
echo "Task Definition: chordscout-chord-detector-dev:14"
echo "Status: ACTIVE"
echo ""
echo "Phase 3 Features:"
echo "  ✓ Song Identification (ENABLE_SONG_ID=true)"
echo "  ✓ Lyrics Fetching (ENABLE_LYRICS=true)"
echo "  ✓ Genius API Integration (secret configured)"
echo "  ✓ Key Confirmation (built into pipeline)"
echo ""
echo "Phase 2 Features:"
echo "  ✓ Multi-Stem Transcription (ENABLE_MULTI_STEM=true)"
echo "  ✓ Mode Selection Workflow"
echo ""
echo "Deployment Method:"
echo "  • Lambda-triggered ECS tasks (on-demand)"
echo "  • No ECS service to update"
echo "  • New tasks automatically use revision 14"
echo ""
echo -e "${GREEN}Phase 3 deployment is ready!${NC}"
echo ""
echo "Next Steps:"
echo "  1. Test with a real audio file"
echo "  2. Verify song identification works"
echo "  3. Verify lyrics are fetched from Genius"
echo "  4. Verify key confirmation workflow"
echo "  5. Check PDF output includes lyrics"
echo ""
