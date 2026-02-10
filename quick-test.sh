#!/bin/bash
set -e

API="https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com"
FILE="./public/13_The_Girl_from_Ipanema__feat._Bebe[43060].mp3"

echo "Getting upload URL..."
RESP=$(curl -s -X POST "$API/upload" -H "Content-Type: application/json" -d '{"filename":"test.mp3","contentType":"audio/mpeg","userId":"test"}')
JOB_ID=$(echo "$RESP" | jq -r '.jobId')
URL=$(echo "$RESP" | jq -r '.uploadUrl')

echo "Job ID: $JOB_ID"
echo "Uploading..."
curl -s -X PUT "$URL" -H "Content-Type: audio/mpeg" --data-binary "@$FILE" > /dev/null
echo "Done! Monitor at: $API/jobs/$JOB_ID"
echo ""
echo "Checking status in 10 seconds..."
sleep 10
curl -s "$API/jobs/$JOB_ID" | jq '{status, progress, errorMessage}'
