#!/bin/bash
# Configure Phase 3 Environment Variables for ChordScout v3.0
# This script updates the ECS task definition to enable lyrics and key confirmation

set -e

echo "============================================================"
echo "PHASE 3 ENVIRONMENT CONFIGURATION"
echo "============================================================"
echo ""

# Configuration
CORRECT_ACCOUNT="090130568474"
TASK_FAMILY="chordscout-chord-detector-dev"
REGION="us-east-1"
SECRET_NAME="chordscout/genius-api-token"

# Verify we're in the correct AWS account
echo "Step 1: Verifying AWS Account..."
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text)

if [ "$CURRENT_ACCOUNT" != "$CORRECT_ACCOUNT" ]; then
    echo "✗ ERROR: Wrong AWS account!"
    echo "  Current: $CURRENT_ACCOUNT"
    echo "  Expected: $CORRECT_ACCOUNT"
    echo ""
    echo "Please switch to the correct AWS profile:"
    echo "  export AWS_PROFILE=<profile-name-for-$CORRECT_ACCOUNT>"
    echo "  OR"
    echo "  aws configure --profile <profile-name>"
    exit 1
fi

echo "✓ Correct AWS account: $CURRENT_ACCOUNT"
echo ""

# Get the current task definition
echo "Step 2: Fetching current task definition..."
aws ecs describe-task-definition \
    --task-definition "$TASK_FAMILY" \
    --region "$REGION" \
    --query 'taskDefinition' > /tmp/task-def-current.json

if [ $? -ne 0 ]; then
    echo "✗ Failed to fetch task definition"
    exit 1
fi

CURRENT_REVISION=$(jq -r '.revision' /tmp/task-def-current.json)
echo "✓ Current revision: $CURRENT_REVISION"
echo ""

# Get the secret ARN
echo "Step 3: Getting Genius API secret ARN..."
SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" \
    --query 'ARN' \
    --output text 2>&1)

if [ $? -ne 0 ]; then
    echo "✗ Failed to get secret ARN"
    echo "  Error: $SECRET_ARN"
    echo ""
    echo "Please ensure the secret exists:"
    echo "  aws secretsmanager create-secret \\"
    echo "    --name $SECRET_NAME \\"
    echo "    --secret-string '{\"GENIUS_ACCESS_TOKEN\":\"your-token\"}' \\"
    echo "    --region $REGION"
    exit 1
fi

echo "✓ Secret ARN: $SECRET_ARN"
echo ""

# Extract and modify the task definition
echo "Step 4: Preparing new task definition..."

# Remove fields that can't be used in registration
jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' \
    /tmp/task-def-current.json > /tmp/task-def-base.json

# Update environment variables
jq --arg secret_arn "$SECRET_ARN" '
  .containerDefinitions[0].environment |= 
    (if . == null then [] else . end) |
    map(if .name == "ENABLE_LYRICS" then .value = "true" else . end) |
    if any(.name == "ENABLE_LYRICS") then . else . + [{"name": "ENABLE_LYRICS", "value": "true"}] end |
    if any(.name == "ENABLE_SONG_ID") then . else . + [{"name": "ENABLE_SONG_ID", "value": "true"}] end
' /tmp/task-def-base.json > /tmp/task-def-with-env.json

# Add secret reference
jq --arg secret_arn "$SECRET_ARN" '
  .containerDefinitions[0].secrets = 
    (if .containerDefinitions[0].secrets == null then [] else .containerDefinitions[0].secrets end) |
    if any(.name == "GENIUS_ACCESS_TOKEN") then
      map(if .name == "GENIUS_ACCESS_TOKEN" then .valueFrom = ($secret_arn + ":GENIUS_ACCESS_TOKEN::") else . end)
    else
      . + [{"name": "GENIUS_ACCESS_TOKEN", "valueFrom": ($secret_arn + ":GENIUS_ACCESS_TOKEN::")}]
    end
' /tmp/task-def-with-env.json > /tmp/task-def-new.json

echo "✓ Task definition prepared"
echo ""

# Show the changes
echo "Step 5: Review changes..."
echo ""
echo "Environment Variables:"
jq -r '.containerDefinitions[0].environment[] | select(.name | test("ENABLE_LYRICS|ENABLE_SONG_ID|ENABLE_MULTI_STEM")) | "  \(.name) = \(.value)"' /tmp/task-def-new.json
echo ""
echo "Secrets:"
jq -r '.containerDefinitions[0].secrets[]? | "  \(.name) = \(.valueFrom)"' /tmp/task-def-new.json
echo ""

# Ask for confirmation
read -p "Do you want to register this new task definition? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Register the new task definition
echo ""
echo "Step 6: Registering new task definition..."
NEW_REVISION=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/task-def-new.json \
    --region "$REGION" \
    --query 'taskDefinition.revision' \
    --output text)

if [ $? -ne 0 ]; then
    echo "✗ Failed to register task definition"
    exit 1
fi

echo "✓ New task definition registered: $TASK_FAMILY:$NEW_REVISION"
echo ""

# Grant IAM permissions
echo "Step 7: Granting IAM permissions..."

TASK_ROLE_ARN=$(jq -r '.taskRoleArn' /tmp/task-def-new.json)
TASK_ROLE_NAME=$(echo "$TASK_ROLE_ARN" | cut -d'/' -f2)

echo "Task Role: $TASK_ROLE_NAME"

# Create policy document
cat > /tmp/secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "$SECRET_ARN"
    }
  ]
}
EOF

# Attach policy
aws iam put-role-policy \
    --role-name "$TASK_ROLE_NAME" \
    --policy-name GeniusAPISecretAccess \
    --policy-document file:///tmp/secrets-policy.json \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo "✓ IAM policy attached to role: $TASK_ROLE_NAME"
else
    echo "⚠ Warning: Failed to attach IAM policy (may already exist)"
fi

echo ""

# Summary
echo "============================================================"
echo "CONFIGURATION COMPLETE"
echo "============================================================"
echo ""
echo "Summary:"
echo "  Account: $CURRENT_ACCOUNT"
echo "  Task Definition: $TASK_FAMILY:$NEW_REVISION"
echo "  ENABLE_LYRICS: true"
echo "  ENABLE_SONG_ID: true"
echo "  Secret: $SECRET_NAME"
echo ""
echo "Next Steps:"
echo "  1. Update ECS service to use new task definition (Task 16.3)"
echo "  2. Validate Phase 3 deployment (Task 16.4)"
echo ""
echo "To update the ECS service:"
echo "  aws ecs update-service \\"
echo "    --cluster chordscout-dev \\"
echo "    --service chordscout-chord-detector-dev \\"
echo "    --task-definition $TASK_FAMILY:$NEW_REVISION \\"
echo "    --region $REGION"
echo ""
