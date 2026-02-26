#!/bin/bash

# Test Data Quality Fixes
# Tests timestamp offset correction, tempo detection, and improved key detection

set -e

echo "========================================="
echo "Testing Data Quality Fixes"
echo "========================================="
echo ""

# YouTube URL (same as before)
YOUTUBE_URL="https://www.youtube.com/watch?v=Q-RKhgsZu64"
VIDEO_ID="Q-RKhgsZu64"

echo "1. Submitting new job..."
echo "   YouTube URL: $YOUTUBE_URL"
echo ""

# Submit job via API (you'll need to replace with actual API endpoint)
# For now, we'll just show how to check an existing job

echo "2. Checking previous job for comparison..."
JOB_ID="c3ab9fe9-b43d-408a-9a04-5aef7fcf59c9"

echo ""
echo "Previous Job Data (BEFORE fixes):"
echo "-----------------------------------"
aws dynamodb get-item \
  --table-name ChordScout-Jobs-V2-dev \
  --key "{\"jobId\": {\"S\": \"$JOB_ID\"}}" \
  --profile chordscout \
  --output json | jq '{
    jobId: .Item.jobId.S,
    status: .Item.status.S,
    videoTitle: .Item.videoTitle.S,
    firstWordStart: .Item.lyricsData.M.words.L[0].M.start.N,
    firstWord: .Item.lyricsData.M.words.L[0].M.word.S,
    tempo: .Item.chordsData.M.tempo,
    key: .Item.chordsData.M.key.S,
    mode: .Item.chordsData.M.mode,
    keyConfidence: .Item.chordsData.M.keyConfidence,
    totalChords: (.Item.chordsData.M.chords.L | length)
  }'

echo ""
echo "========================================="
echo "Expected Results AFTER Fixes:"
echo "========================================="
echo "✅ firstWordStart: ~16s (was 161.81s)"
echo "✅ tempo: Actual BPM (was null)"
echo "✅ key: Better detection (was G)"
echo "✅ mode: major or minor (was null)"
echo "✅ keyConfidence: 0.0-1.0 (was null)"
echo ""
echo "========================================="
echo "To test with a NEW job:"
echo "========================================="
echo "1. Go to the ChordScout frontend"
echo "2. Submit the same YouTube URL: $YOUTUBE_URL"
echo "3. Wait for job to complete (~4 minutes)"
echo "4. Check DynamoDB with this command:"
echo ""
echo "   aws dynamodb get-item \\"
echo "     --table-name ChordScout-Jobs-V2-dev \\"
echo "     --key '{\"jobId\": {\"S\": \"NEW_JOB_ID\"}}' \\"
echo "     --profile chordscout \\"
echo "     --output json | jq '.Item.lyricsData.M.words.L[0]'"
echo ""
echo "5. Verify:"
echo "   - First word starts at ~16s (not 161s)"
echo "   - Tempo is detected (not null)"
echo "   - Key has mode and confidence"
echo ""
