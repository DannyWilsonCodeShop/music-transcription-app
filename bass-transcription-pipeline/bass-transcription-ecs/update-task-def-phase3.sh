#!/bin/bash
# Update ECS task definition for Phase 3

set -e

export AWS_PROFILE=chordscout

TASK_FAMILY="chordscout-chord-detector-dev"
REGION="us-east-1"
SECRET_NAME="chordscout/genius-api-token"

echo "Fetching current task definition..."
aws ecs describe-task-definition \
    --task-definition "$TASK_FAMILY" \
    --region "$REGION" \
    --query 'taskDefinition' > /tmp/current-task-def.json

# Get secret ARN
SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" \
    --query 'ARN' \
    --output text)

echo "Secret ARN: $SECRET_ARN"

# Create new task definition with Python
python3 << 'PYTHON_SCRIPT'
import json

# Load current task definition
with open('/tmp/current-task-def.json', 'r') as f:
    task_def = json.load(f)

# Remove fields that can't be used in registration
for field in ['taskDefinitionArn', 'revision', 'status', 'requiresAttributes', 
              'compatibilities', 'registeredAt', 'registeredBy']:
    task_def.pop(field, None)

# Get the container definition
container = task_def['containerDefinitions'][0]

# Update environment variables
env_vars = container.get('environment', [])
env_dict = {e['name']: e for e in env_vars}

# Set ENABLE_LYRICS=true
env_dict['ENABLE_LYRICS'] = {'name': 'ENABLE_LYRICS', 'value': 'true'}

# Ensure ENABLE_SONG_ID=true
if 'ENABLE_SONG_ID' not in env_dict:
    env_dict['ENABLE_SONG_ID'] = {'name': 'ENABLE_SONG_ID', 'value': 'true'}

# Ensure ENABLE_MULTI_STEM=true (from Phase 2)
if 'ENABLE_MULTI_STEM' not in env_dict:
    env_dict['ENABLE_MULTI_STEM'] = {'name': 'ENABLE_MULTI_STEM', 'value': 'true'}

container['environment'] = list(env_dict.values())

# Add secret
import os
secret_arn = os.environ.get('SECRET_ARN')
secrets = container.get('secrets', [])
secret_dict = {s['name']: s for s in secrets}

secret_dict['GENIUS_ACCESS_TOKEN'] = {
    'name': 'GENIUS_ACCESS_TOKEN',
    'valueFrom': f'{secret_arn}:GENIUS_ACCESS_TOKEN::'
}

container['secrets'] = list(secret_dict.values())

# Save new task definition
with open('/tmp/new-task-def.json', 'w') as f:
    json.dump(task_def, f, indent=2)

print("✓ Task definition prepared")
PYTHON_SCRIPT

# Show changes
echo ""
echo "Environment Variables:"
jq -r '.containerDefinitions[0].environment[] | select(.name | test("ENABLE")) | "  \(.name) = \(.value)"' /tmp/new-task-def.json

echo ""
echo "Secrets:"
jq -r '.containerDefinitions[0].secrets[] | "  \(.name)"' /tmp/new-task-def.json

echo ""
read -p "Register this task definition? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Register new task definition
echo "Registering new task definition..."
NEW_REVISION=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/new-task-def.json \
    --region "$REGION" \
    --query 'taskDefinition.revision' \
    --output text)

echo "✓ New revision: $TASK_FAMILY:$NEW_REVISION"

# Grant IAM permissions
TASK_ROLE_ARN=$(jq -r '.taskRoleArn' /tmp/new-task-def.json)
TASK_ROLE_NAME=$(echo "$TASK_ROLE_ARN" | cut -d'/' -f2)

echo "Granting IAM permissions to role: $TASK_ROLE_NAME"

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

aws iam put-role-policy \
    --role-name "$TASK_ROLE_NAME" \
    --policy-name GeniusAPISecretAccess \
    --policy-document file:///tmp/secrets-policy.json

echo "✓ IAM policy attached"
echo ""
echo "Task 16.2 Complete!"
echo "New task definition: $TASK_FAMILY:$NEW_REVISION"
