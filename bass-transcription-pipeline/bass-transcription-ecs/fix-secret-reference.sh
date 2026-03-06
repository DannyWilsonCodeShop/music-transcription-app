#!/bin/bash
# Fix the Genius API secret reference format in task definition

set -e

export AWS_PROFILE=chordscout
REGION="us-east-1"
TASK_FAMILY="chordscout-chord-detector-dev"

echo "Fixing Genius API secret reference format..."
echo ""

# Get current task definition
echo "Fetching current task definition..."
TASK_DEF=$(aws ecs describe-task-definition \
  --task-definition $TASK_FAMILY \
  --region $REGION \
  --query 'taskDefinition' \
  --output json)

# Remove the JSON key selector from the secret ARN
# Change from: arn:...:secret:chordscout/genius-api-token-TIzd2O:GENIUS_ACCESS_TOKEN::
# To: arn:...:secret:chordscout/genius-api-token-TIzd2O
echo "Updating secret reference format..."
UPDATED_TASK_DEF=$(echo "$TASK_DEF" | jq '
  .containerDefinitions[0].secrets[0].valueFrom = "arn:aws:secretsmanager:us-east-1:090130568474:secret:chordscout/genius-api-token-TIzd2O" |
  del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)
')

# Register new task definition
echo "Registering new task definition..."
NEW_TASK_DEF=$(aws ecs register-task-definition \
  --region $REGION \
  --cli-input-json "$UPDATED_TASK_DEF" \
  --query 'taskDefinition.{family:family,revision:revision,status:status}' \
  --output json)

REVISION=$(echo $NEW_TASK_DEF | jq -r '.revision')
STATUS=$(echo $NEW_TASK_DEF | jq -r '.status')

echo ""
echo "✓ New task definition registered"
echo "  Family: $TASK_FAMILY"
echo "  Revision: $REVISION"
echo "  Status: $STATUS"
echo ""

# Verify the secret reference
echo "Verifying secret reference..."
SECRET_REF=$(aws ecs describe-task-definition \
  --task-definition $TASK_FAMILY:$REVISION \
  --region $REGION \
  --query 'taskDefinition.containerDefinitions[0].secrets[0].valueFrom' \
  --output text)

echo "  Secret ARN: $SECRET_REF"
echo ""

if [[ "$SECRET_REF" == *":GENIUS_ACCESS_TOKEN::"* ]]; then
  echo "✗ Secret reference still has JSON key selector"
  exit 1
else
  echo "✓ Secret reference format is correct"
fi

echo ""
echo "Task definition $TASK_FAMILY:$REVISION is ready to use"
