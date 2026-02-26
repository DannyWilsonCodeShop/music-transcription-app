#!/usr/bin/env python3
"""Test RapidAPI directly to diagnose the 403 error"""

import urllib.request
import json

RAPIDAPI_KEY = "252611e8d7mshdde3262a7e2137bp12792bjsn7ce487b8a3dc"
VIDEO_ID = "Q-RKhgsZu64"

# Try different endpoint variations
endpoints = [
    {
        "name": "Original endpoint",
        "url": f"https://youtube-mp3-audio-video-downloader.p.rapidapi.com/get_m4a_download_link/{VIDEO_ID}",
        "host": "youtube-mp3-audio-video-downloader.p.rapidapi.com"
    },
    {
        "name": "Alternative endpoint 1",
        "url": f"https://youtube-mp36.p.rapidapi.com/dl?id={VIDEO_ID}",
        "host": "youtube-mp36.p.rapidapi.com"
    },
    {
        "name": "Alternative endpoint 2",
        "url": f"https://youtube-mp3-download1.p.rapidapi.com/dl?id={VIDEO_ID}",
        "host": "youtube-mp3-download1.p.rapidapi.com"
    }
]

for endpoint in endpoints:
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint['name']}")
    print(f"URL: {endpoint['url']}")
    print(f"{'='*60}")
    
    try:
        req = urllib.request.Request(endpoint['url'])
        req.add_header("x-rapidapi-key", RAPIDAPI_KEY)
        req.add_header("x-rapidapi-host", endpoint['host'])
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"✅ SUCCESS!")
            print(f"Response: {json.dumps(data, indent=2)}")
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        try:
            error_body = e.read().decode()
            print(f"Error body: {error_body}")
        except:
            pass
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

print(f"\n{'='*60}")
print("Testing complete")
print(f"{'='*60}")
