#!/bin/bash

# Test MSAF Integration - Submit job and check results
# This will show the MSAF segmentation results

API_URL="https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev"
TEST_VIDEO="https://www.youtube.com/watch?v=Q-RKhgsZu64"  # Like The Dew

echo "🎵 Testing MSAF Integration"
echo "================================"
echo ""

# Submit job
echo "1. Submitting job..."
RESPONSE=$(curl -s -X POST "$API_URL/jobs" \
  -H "Content-Type: application/json" \
  -d "{\"youtubeUrl\": \"$TEST_VIDEO\"}")

JOB_ID=$(echo $RESPONSE | jq -r '.jobId')

if [ "$JOB_ID" == "null" ] || [ -z "$JOB_ID" ]; then
  echo "❌ Failed to submit job"
  echo "Response: $RESPONSE"
  exit 1
fi

echo "✓ Job submitted: $JOB_ID"
echo ""

# Poll for completion
echo "2. Waiting for completion..."
echo "   (This may take 2-3 minutes)"
echo ""

MAX_ATTEMPTS=90  # 3 minutes
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  sleep 2
  ATTEMPT=$((ATTEMPT + 1))
  
  STATUS_RESPONSE=$(curl -s "$API_URL/jobs/$JOB_ID")
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  PROGRESS=$(echo $STATUS_RESPONSE | jq -r '.progress')
  
  echo -ne "\r   Status: $STATUS ($PROGRESS%)   "
  
  if [ "$STATUS" == "COMPLETE" ]; then
    echo ""
    echo ""
    echo "✅ Job completed!"
    echo ""
    break
  elif [ "$STATUS" == "FAILED" ]; then
    echo ""
    echo ""
    echo "❌ Job failed"
    ERROR=$(echo $STATUS_RESPONSE | jq -r '.errorMessage')
    echo "Error: $ERROR"
    exit 1
  fi
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
  echo ""
  echo "⏱️  Timeout waiting for completion"
  exit 1
fi

# Display results
echo "3. Results:"
echo "================================"
echo ""

# Key and tempo
KEY=$(echo $STATUS_RESPONSE | jq -r '.chordsData.key')
MODE=$(echo $STATUS_RESPONSE | jq -r '.chordsData.mode')
TEMPO=$(echo $STATUS_RESPONSE | jq -r '.chordsData.tempo')
DURATION=$(echo $STATUS_RESPONSE | jq -r '.chordsData.duration')
TOTAL_CHORDS=$(echo $STATUS_RESPONSE | jq -r '.chordsData.totalChords')
MODEL=$(echo $STATUS_RESPONSE | jq -r '.chordsData.model')

echo "🎹 Key: $KEY $MODE"
echo "🥁 Tempo: $TEMPO BPM"
echo "⏱️  Duration: ${DURATION}s"
echo "🎸 Total Chords: $TOTAL_CHORDS"
echo "🤖 Model: $MODEL"
echo ""

# MSAF Song Structure
echo "🎵 MSAF Song Structure:"
echo "--------------------------------"
STRUCTURE=$(echo $STATUS_RESPONSE | jq -r '.chordsData.songStructure[]? | "\(.label): \(.start)s - \(.end)s (\(.duration)s)"')

if [ -z "$STRUCTURE" ]; then
  echo "   No MSAF structure data (using pattern-based)"
else
  echo "$STRUCTURE"
fi
echo ""

# Pattern Analysis
echo "📊 Repeating Patterns (Nashville Numbers):"
echo "--------------------------------"
PATTERNS=$(echo $STATUS_RESPONSE | jq -r '.chordsData.patternAnalysis[]? | "Pattern \(.patternNumber): \(.progression | join(" → ")) (\(.nashvilleProgression | join(" → "))) - \(.occurrences) times"')

if [ -z "$PATTERNS" ]; then
  echo "   No patterns detected"
else
  echo "$PATTERNS" | head -5
fi
echo ""

# First 10 chords
echo "🎸 First 10 Chords:"
echo "--------------------------------"
echo $STATUS_RESPONSE | jq -r '.chordsData.chords[0:10][]? | "\(.chord) at \(.start)s"'
echo ""

# PDF URL
PDF_URL=$(echo $STATUS_RESPONSE | jq -r '.pdfUrl')
if [ "$PDF_URL" != "null" ] && [ -n "$PDF_URL" ]; then
  echo "📄 PDF: $PDF_URL"
  echo ""
fi

# Frontend URL
echo "🌐 View in frontend:"
echo "   http://localhost:5173"
echo "   (Job ID: $JOB_ID)"
echo ""

echo "================================"
echo "✅ Test complete!"
echo ""
echo "What to check:"
echo "1. MSAF structure shows A-B-A-C style labels"
echo "2. Nashville numbers (1, 2m, 5, etc.) in patterns"
echo "3. Reasonable chord count (40-80 for this song)"
echo "4. Key should be F major (or close)"
