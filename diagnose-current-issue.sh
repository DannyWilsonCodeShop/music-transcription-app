#!/bin/bash
# Quick diagnostic for current upload issue

export AWS_PROFILE=production

echo "========================================="
echo "Current Upload Diagnostic"
echo "========================================="
echo ""

# Check for recent uploads in last 30 minutes
echo "1. Recent uploads (last 30 min):"
aws logs tail /aws/lambda/music-transcription-upload-test --since 30m --format short | grep -E "(Event|jobId|ERROR)" | tail -10
echo ""

# Check for recent processing
echo "2. Recent processing (last 30 min):"
aws logs tail /aws/lambda/music-transcription-process-audio-test --since 30m --format short | grep -E "(Processing job|ECS task|ERROR)" | tail -10
echo ""

# Check running ECS tasks
echo "3. Running ECS tasks:"
TASKS=$(aws ecs list-tasks --cluster ChordScout-dev --query 'taskArns[]' --output text)
if [ -z "$TASKS" ]; then
    echo "No tasks currently running"
else
    for TASK in $TASKS; do
        echo "Task: $TASK"
        aws ecs describe-tasks --cluster ChordScout-dev --tasks "$TASK" \
            --query 'tasks[0].{Status:lastStatus,Container:containers[0].lastStatus}' --output json
    done
fi
echo ""

# Check most recent jobs (last hour)
echo "4. Recent jobs (last hour):"
CUTOFF=$(date -u -v-1H '+%Y-%m-%dT%H:%M:%S.000Z' 2>/dev/null || date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%S.000Z')
aws dynamodb scan --table-name ChordScout-Jobs-V2-dev \
    --filter-expression "createdAt > :date" \
    --expression-attribute-values "{\":date\":{\"S\":\"$CUTOFF\"}}" \
    --query 'Items[*].[jobId.S, status.S, progress.N, createdAt.S]' \
    --output table | head -20
echo ""

# Check S3 for recent uploads
echo "5. Recent S3 uploads (last 30 min):"
CUTOFF_EPOCH=$(date -u -v-30M '+%s' 2>/dev/null || date -u -d '30 minutes ago' '+%s')
aws s3api list-objects-v2 --bucket music-transcription-audio-test-090130568474 \
    --prefix uploads/ --query "Contents[?LastModified>=\`$(date -u -v-30M -Iseconds 2>/dev/null || date -u -d '30 minutes ago' -Iseconds)\`].[Key,LastModified,Size]" \
    --output table 2>/dev/null | head -20 || echo "No recent uploads found"
echo ""

echo "========================================="
echo "If you just uploaded a file, please provide:"
echo "1. The filename"
echo "2. What you see in the browser"
echo "3. Any error messages"
echo "========================================="
