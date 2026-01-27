#!/bin/bash

# Script to set up YouTube cookies for yt-dlp
# This allows bypassing YouTube's bot detection

echo "=== YouTube Cookies Setup for ChordScout ==="
echo ""
echo "To fix YouTube bot detection, we need to export cookies from your browser."
echo ""
echo "OPTION 1: Export cookies using a browser extension"
echo "  1. Install 'Get cookies.txt LOCALLY' extension:"
echo "     - Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"
echo "     - Firefox: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/"
echo "  2. Go to youtube.com and make sure you're logged in"
echo "  3. Click the extension icon and export cookies"
echo "  4. Save the file as 'youtube-cookies.txt' in this directory"
echo ""
echo "OPTION 2: Use yt-dlp to extract cookies from your browser"
echo "  Run: yt-dlp --cookies-from-browser chrome --cookies youtube-cookies.txt https://www.youtube.com/watch?v=dQw4w9WgXcQ"
echo "  (Replace 'chrome' with 'firefox', 'edge', or 'safari' as needed)"
echo ""
echo "Once you have youtube-cookies.txt, run this script again to upload it to S3."
echo ""

# Check if cookies file exists
if [ ! -f "youtube-cookies.txt" ]; then
    echo "❌ youtube-cookies.txt not found in current directory"
    echo ""
    echo "Please create the file first using one of the methods above."
    exit 1
fi

echo "✓ Found youtube-cookies.txt"
echo ""

# Upload to S3
echo "Uploading cookies to S3..."
aws s3 cp youtube-cookies.txt s3://chordscout-audio-dev-090130568474/config/youtube-cookies.txt \
    --region us-east-1 \
    --profile chordscout

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Cookies uploaded successfully!"
    echo ""
    echo "YouTube downloads should now work without bot detection."
    echo "The Lambda function will automatically use these cookies."
    echo ""
    echo "⚠️  SECURITY NOTE:"
    echo "  - These cookies give access to your YouTube account"
    echo "  - Only use this on your own AWS account"
    echo "  - Cookies expire after some time and will need to be refreshed"
    echo ""
    echo "To remove cookies from S3:"
    echo "  aws s3 rm s3://chordscout-audio-dev-090130568474/config/youtube-cookies.txt --region us-east-1 --profile chordscout"
else
    echo ""
    echo "❌ Failed to upload cookies to S3"
    echo "Make sure you have AWS credentials configured for the chordscout profile"
fi
