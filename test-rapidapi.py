#!/usr/bin/env python3
"""
Test RapidAPI YouTube MP3 credentials
"""

import requests
import json
import os
import time

# Load API key from environment
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '')

if not RAPIDAPI_KEY:
    print("❌ Error: RAPIDAPI_KEY not set")
    exit(1)

print(f"🔑 Testing RapidAPI key: {RAPIDAPI_KEY[:10]}...")
print()

# Test with a short video
video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
print(f"📹 Testing with video ID: {video_id}")
print()

url = "https://youtube-mp36.p.rapidapi.com/dl"
querystring = {"id": video_id}
headers = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"
}

max_retries = 10
retry_delay = 1

for attempt in range(max_retries):
    try:
        print(f"🔄 Attempt {attempt + 1}/{max_retries}...")
        
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("❌ Error: API key is invalid or you're not subscribed to this API")
            print("   Please check:")
            print("   1. Your API key is correct")
            print("   2. You're subscribed to: https://rapidapi.com/ytjar/api/youtube-mp36")
            exit(1)
        
        response.raise_for_status()
        
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
        print()
        
        status = data.get('status')
        
        if status == 'ok':
            print("✅ Success! API credentials are working")
            print(f"   Title: {data.get('title', 'Unknown')}")
            print(f"   Download Link: {data.get('link', 'N/A')[:50]}...")
            print()
            print("🎉 RapidAPI is ready to use!")
            exit(0)
            
        elif status == 'processing':
            print(f"   ⏳ Video still processing, waiting {retry_delay}s...")
            time.sleep(retry_delay)
            continue
            
        elif status == 'fail':
            error_msg = data.get('msg', 'Unknown error')
            print(f"❌ API returned failure: {error_msg}")
            exit(1)
        
        else:
            print(f"❌ Unknown status: {status}")
            exit(1)
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {str(e)}")
        if attempt < max_retries - 1:
            print(f"   Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            continue
        print(f"❌ Failed after {max_retries} attempts")
        exit(1)

print(f"❌ Video processing timeout after {max_retries} attempts")
exit(1)
