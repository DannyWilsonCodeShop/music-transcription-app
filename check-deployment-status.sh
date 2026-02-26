#!/bin/bash
# Check Current Deployment Status
# Shows which revision is deployed and what detection method is being used

echo "================================================================================"
echo "ChordScout Deployment Status Check"
echo "================================================================================"
echo ""

# Check Lambda trigger configuration
echo "1. Lambda Trigger Configuration"
echo "--------------------------------------------------------------------------------"
TASK_DEF=$(aws lambda get-function-configuration \
  --function-name chordscout-v2-chord-detector-trigger-dev \
  --region us-east-1 \
  --query 'Environment.Variables.TASK_DEFINITION' \
  --output text)

echo "Lambda Function: chordscout-v2-chord-detector-trigger-dev"
echo "Task Definition: $TASK_DEF"

# Extract revision number
REVISION=$(echo $TASK_DEF | grep -oE '[0-9]+$')
echo "Revision: $REVISION"
echo ""

# Check ECS task definition
echo "2. ECS Task Definition Details"
echo "--------------------------------------------------------------------------------"
IMAGE=$(aws ecs describe-task-definition \
  --task-definition chordscout-chord-detector-dev:$REVISION \
  --region us-east-1 \
  --query 'taskDefinition.containerDefinitions[0].image' \
  --output text)

echo "Docker Image: $IMAGE"
echo ""

# Check recent ECS task logs
echo "3. Recent CloudWatch Logs (Last 5 minutes)"
echo "--------------------------------------------------------------------------------"
echo "Checking for detection method used..."
echo ""

# Get recent log events
aws logs filter-log-events \
  --log-group-name /ecs/chordscout-chord-detector-dev \
  --region us-east-1 \
  --start-time $(($(date +%s) * 1000 - 300000)) \
  --filter-pattern "Using" \
  --query 'events[*].message' \
  --output text | head -5

echo ""
echo "4. Expected Configuration (Revision 9)"
echo "--------------------------------------------------------------------------------"
echo "✓ Task Definition: ...revision:9"
echo "✓ Docker Image: ...enhanced-v3"
echo "✓ Log Message: 'Using ENHANCED librosa chord detection (84 templates)'"
echo ""

if [ "$REVISION" = "9" ]; then
  echo "✓ Correct revision deployed!"
else
  echo "✗ Wrong revision! Expected 9, got $REVISION"
  echo ""
  echo "To fix, run:"
  echo "  aws lambda update-function-configuration \\"
  echo "    --function-name chordscout-v2-chord-detector-trigger-dev \\"
  echo "    --region us-east-1 \\"
  echo "    --environment \"Variables={\\"
  echo "      SUBNET_1=subnet-08bd4b3753627a89c,\\"
  echo "      ECS_CLUSTER=ChordScout-dev,\\"
  echo "      TASK_DEFINITION=arn:aws:ecs:us-east-1:463470937777:task-definition/chordscout-chord-detector-dev:9,\\"
  echo "      SUBNET_2=subnet-068f854900c3ee293,\\"
  echo "      DYNAMODB_JOBS_TABLE=ChordScout-Jobs-V2-dev\\"
  echo "    }\""
fi

echo ""
echo "================================================================================"
echo "To test the current deployment:"
echo "  1. Submit a job via your frontend"
echo "  2. Check CloudWatch logs: /ecs/chordscout-chord-detector-dev"
echo "  3. Look for: 'Using ENHANCED librosa chord detection (84 templates)'"
echo "  4. Download audio: node download-job-audio.js YOUR_JOB_ID"
echo "================================================================================"
