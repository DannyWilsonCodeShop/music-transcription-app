#!/bin/bash

# Simple diagnostic - just get the raw data and save it

AWS_PROFILE=production
REGION=us-east-1
JOBS_TABLE="ChordScout-Jobs-V2-dev"

echo "Getting most recent completed job..."

# Get all completed jobs, sorted by date
aws dynamodb scan \
    --table-name "$JOBS_TABLE" \
    --filter-expression "#s = :status" \
    --expression-attribute-names '{"#s":"status"}' \
    --expression-attribute-values '{":status":{"S":"COMPLETED"}}' \
    --profile "$AWS_PROFILE" \
    --region "$REGION" \
    --output json > all-completed-jobs.json

echo "✓ Saved to all-completed-jobs.json"
echo ""
echo "Now let's get the most recent one..."

# Extract the most recent job ID
JOB_ID=$(cat all-completed-jobs.json | jq -r '.Items | sort_by(.createdAt.S) | .[-1].jobId.S')

echo "Most recent job: $JOB_ID"
echo ""

# Get that specific job
aws dynamodb get-item \
    --table-name "$JOBS_TABLE" \
    --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
    --profile "$AWS_PROFILE" \
    --region "$REGION" \
    --output json > "job-$JOB_ID.json"

echo "✓ Saved full job to: job-$JOB_ID.json"
echo ""

# Extract just the chords for easier viewing
cat "job-$JOB_ID.json" | jq '.Item.chordsData.M.chords.L[0:10]' > "first-10-chords-$JOB_ID.json"

echo "✓ Saved first 10 chords to: first-10-chords-$JOB_ID.json"
echo ""
echo "To view the chord symbols, run:"
echo "  cat first-10-chords-$JOB_ID.json | jq -r '.[].M.chord.S'"
