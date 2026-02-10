#!/bin/bash
# Add ECS permissions to Lambda role

set -e

export AWS_PROFILE=production
REGION="us-east-1"
ROLE_NAME="MusicTranscription-Lambda-test"

echo "Adding ECS permissions to Lambda role..."

# Create policy document
cat > /tmp/ecs-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:RunTask",
        "ecs:DescribeTasks",
        "ecs:StopTask"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "iam:PassedToService": "ecs-tasks.amazonaws.com"
        }
      }
    }
  ]
}
EOF

# Put inline policy
aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name ECSTaskExecution \
  --policy-document file:///tmp/ecs-policy.json \
  --profile $AWS_PROFILE

echo "✅ ECS permissions added to $ROLE_NAME"

# Clean up
rm /tmp/ecs-policy.json
