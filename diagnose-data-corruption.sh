#!/bin/bash

# Diagnostic script to inspect data corruption issues
# This will help us understand where the problem is occurring

set -e

AWS_PROFILE=production
REGION=us-east-1
JOBS_TABLE="ChordScout-Jobs-V2-dev"

echo "=========================================="
echo "Data Corruption Diagnostic Tool"
echo "=========================================="
echo ""

# Get the most recent job
echo "1. Fetching most recent job from DynamoDB..."
RECENT_JOB=$(aws dynamodb scan \
    --table-name "$JOBS_TABLE" \
    --profile "$AWS_PROFILE" \
    --region "$REGION" \
    --max-items 1 \
    --query 'Items | sort_by(@, &createdAt) | [-1]' \
    --output json)

JOB_ID=$(echo "$RECENT_JOB" | jq -r '.jobId.S // .jobId')

if [ "$JOB_ID" == "null" ] || [ -z "$JOB_ID" ]; then
    echo "❌ No jobs found in DynamoDB"
    exit 1
fi

echo "✓ Most recent job ID: $JOB_ID"
echo ""

# Get full job data
echo "2. Fetching complete job data..."
FULL_JOB=$(aws dynamodb get-item \
    --table-name "$JOBS_TABLE" \
    --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
    --profile "$AWS_PROFILE" \
    --region "$REGION" \
    --output json)

echo "✓ Job data retrieved"
echo ""

# Save raw data to file
echo "$FULL_JOB" > "diagnostic-raw-job-$JOB_ID.json"
echo "✓ Raw DynamoDB data saved to: diagnostic-raw-job-$JOB_ID.json"
echo ""

# Extract and display key information
echo "3. Analyzing job data..."
echo ""

STATUS=$(echo "$FULL_JOB" | jq -r '.Item.status.S // .Item.status')
PROGRESS=$(echo "$FULL_JOB" | jq -r '.Item.progress.N // .Item.progress // "0"')
FILENAME=$(echo "$FULL_JOB" | jq -r '.Item.filename.S // .Item.filename // "unknown"')

echo "Job Status:"
echo "  ID: $JOB_ID"
echo "  Filename: $FILENAME"
echo "  Status: $STATUS"
echo "  Progress: $PROGRESS%"
echo ""

# Check if chordsData exists
HAS_CHORDS=$(echo "$FULL_JOB" | jq -r '.Item.chordsData // "null"')

if [ "$HAS_CHORDS" == "null" ]; then
    echo "❌ No chordsData found in job"
    echo ""
    echo "This means the chord detection either:"
    echo "  1. Never ran"
    echo "  2. Failed before saving data"
    echo "  3. Saved data to wrong location"
    echo ""
    
    # Check for error message
    ERROR_MSG=$(echo "$FULL_JOB" | jq -r '.Item.errorMessage.S // .Item.errorMessage // "none"')
    if [ "$ERROR_MSG" != "none" ]; then
        echo "Error message: $ERROR_MSG"
    fi
    
    # Check ECS task ARN
    TASK_ARN=$(echo "$FULL_JOB" | jq -r '.Item.ecsTaskArn.S // .Item.ecsTaskArn // "none"')
    if [ "$TASK_ARN" != "none" ]; then
        echo ""
        echo "ECS Task ARN: $TASK_ARN"
        echo ""
        echo "To view ECS logs, run:"
        echo "  aws logs tail /ecs/chordscout-chord-detector-dev --since 2h --profile $AWS_PROFILE --region $REGION"
    fi
    
    exit 1
fi

echo "✓ chordsData found"
echo ""

# Extract chordsData structure
echo "4. Analyzing chordsData structure..."
echo ""

# Convert DynamoDB format to regular JSON
CHORDS_DATA=$(echo "$FULL_JOB" | jq '.Item.chordsData')

# Save chordsData to separate file
echo "$CHORDS_DATA" > "diagnostic-chords-data-$JOB_ID.json"
echo "✓ Chords data saved to: diagnostic-chords-data-$JOB_ID.json"
echo ""

# Analyze chord data structure
KEY=$(echo "$CHORDS_DATA" | jq -r '.M.key.S // .key // "unknown"')
MODE=$(echo "$CHORDS_DATA" | jq -r '.M.mode.S // .mode // "unknown"')
TEMPO=$(echo "$CHORDS_DATA" | jq -r '.M.tempo.N // .tempo // "unknown"')
TOTAL_CHORDS=$(echo "$CHORDS_DATA" | jq -r '.M.totalChords.N // .totalChords // "0"')

echo "Chord Detection Results:"
echo "  Key: $KEY"
echo "  Mode: $MODE"
echo "  Tempo: $TEMPO BPM"
echo "  Total Chords: $TOTAL_CHORDS"
echo ""

# Check first few chords
echo "5. Inspecting chord symbols..."
echo ""

# Try to extract first 5 chords
FIRST_CHORDS=$(echo "$CHORDS_DATA" | jq -r '
    if .M.chords.L then
        .M.chords.L[0:5] | map(.M.chord.S // .chord) | join(", ")
    elif .chords then
        .chords[0:5] | map(.chord) | join(", ")
    else
        "Could not extract chords"
    end
')

echo "First 5 chords: $FIRST_CHORDS"
echo ""

# Check for the corruption pattern
if [[ "$FIRST_CHORDS" == *"!'"* ]]; then
    echo "❌ CORRUPTION DETECTED: Chord symbols contain '!' characters"
    echo ""
    echo "This suggests the chord names are being incorrectly encoded or decoded."
    echo "Possible causes:"
    echo "  1. DynamoDB attribute type mismatch (storing as wrong type)"
    echo "  2. JSON serialization issue in Python (Decimal conversion)"
    echo "  3. Character encoding issue"
    echo ""
fi

# Check for lyrics
echo "6. Checking for lyrics data..."
echo ""

HAS_LYRICS=$(echo "$CHORDS_DATA" | jq -r '
    if .M.lyrics then
        "yes"
    elif .lyrics then
        "yes"
    else
        "no"
    end
')

if [ "$HAS_LYRICS" == "yes" ]; then
    LYRICS_TEXT=$(echo "$CHORDS_DATA" | jq -r '
        if .M.lyrics.M.text.S then
            .M.lyrics.M.text.S[0:100]
        elif .lyrics.text then
            .lyrics.text[0:100]
        else
            "Could not extract lyrics text"
        end
    ')
    
    WORD_COUNT=$(echo "$CHORDS_DATA" | jq -r '
        if .M.lyrics.M.words.L then
            .M.lyrics.M.words.L | length
        elif .lyrics.words then
            .lyrics.words | length
        else
            "0"
        end
    ')
    
    echo "✓ Lyrics found"
    echo "  Word count: $WORD_COUNT"
    echo "  First 100 chars: $LYRICS_TEXT"
else
    echo "❌ No lyrics data found"
    echo ""
    echo "Possible causes:"
    echo "  1. Whisper not available in ECS container"
    echo "  2. Lyrics extraction failed"
    echo "  3. Instrumental track (no vocals)"
    echo "  4. Data not saved to DynamoDB"
fi
echo ""

# Check for leadSheet
echo "7. Checking for lead sheet data..."
echo ""

HAS_LEADSHEET=$(echo "$CHORDS_DATA" | jq -r '
    if .M.leadSheet then
        "yes"
    elif .leadSheet then
        "yes"
    else
        "no"
    end
')

if [ "$HAS_LEADSHEET" == "yes" ]; then
    SECTION_COUNT=$(echo "$CHORDS_DATA" | jq -r '
        if .M.leadSheet.M.sections.L then
            .M.leadSheet.M.sections.L | length
        elif .leadSheet.sections then
            .leadSheet.sections | length
        else
            "0"
        end
    ')
    
    echo "✓ Lead sheet found"
    echo "  Sections: $SECTION_COUNT"
else
    echo "❌ No lead sheet data found"
    echo ""
    echo "This means lyrics-chord alignment did not run or failed."
fi
echo ""

# Summary
echo "=========================================="
echo "Diagnostic Summary"
echo "=========================================="
echo ""
echo "Files created:"
echo "  - diagnostic-raw-job-$JOB_ID.json (full DynamoDB item)"
echo "  - diagnostic-chords-data-$JOB_ID.json (chordsData only)"
echo ""
echo "Next steps:"
echo "  1. Review the JSON files to see exact data structure"
echo "  2. Check ECS logs for chord detection output"
echo "  3. Compare with expected format in code"
echo ""
echo "To view ECS logs:"
echo "  aws logs tail /ecs/chordscout-chord-detector-dev --since 2h --profile $AWS_PROFILE --region $REGION --follow"
