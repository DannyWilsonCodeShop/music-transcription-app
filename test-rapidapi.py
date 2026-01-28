#!/usr/bin/env python3
"""
Test RapidAPI YouTube downloader with upgraded subscription
"""

import requests
import os
import json
from urllib.parse import urlparse, parse_qs

def extract_video_id(youtube_url):
    """Extract video ID from various YouTube URL formats"""
    parsed_url = urlparse(youtube_url)
    
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
        elif parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
    elif parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    
    return None

def test_rapidapi_service(video_id, api_key):
    """Test the primary RapidAPI service"""
    print(f"Testing primary API with video ID: {video_id}")
    
    url = "https://youtube-mp36.p.rapidapi.com/dl"
    
    querystring = {"id": video_id}
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Data: {json.dumps(data, indent=2)}")
            
            if data.get('status') == 'ok' and data.get('link'):
                print("✅ SUCCESS: Got download link!")
                return data['link']
            else:
                print("❌ FAILED: No download link in response")
                return None
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST FAILED: {e}")
        return None

def test_alternative_api(video_id, api_key):
    """Test alternative RapidAPI service"""
    print(f"\nTesting alternative API with video ID: {video_id}")
    
    url = "https://youtube-to-mp315.p.rapidapi.com/download"
    
    payload = {
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "format": "mp3",
        "quality": "128"
    }
    
    headers = {
        "content-type": "application/json",
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "youtube-to-mp315.p.rapidapi.com"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Data: {json.dumps(data, indent=2)}")
            
            if data.get('success') and data.get('download_url'):
                print("✅ SUCCESS: Got download link!")
                return data['download_url']
            else:
                print("❌ FAILED: No download link in response")
                return None
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST FAILED: {e}")
        return None

def main():
    # Test with a short, popular video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - short and reliable
    video_id = extract_video_id(test_url)
    
    print("🚀 Testing RapidAPI YouTube Downloader")
    print(f"Test URL: {test_url}")
    print(f"Video ID: {video_id}")
    
    # You'll need to set your RapidAPI key
    api_key = os.environ.get('RAPIDAPI_KEY')
    if not api_key:
        print("❌ ERROR: RAPIDAPI_KEY environment variable not set")
        print("Please set it with your upgraded subscription key:")
        print("export RAPIDAPI_KEY='your-key-here'")
        return
    
    print(f"Using API Key: {api_key[:10]}...")
    
    # Test primary service
    download_link = test_rapidapi_service(video_id, api_key)
    
    if not download_link:
        # Try alternative service
        download_link = test_alternative_api(video_id, api_key)
    
    if download_link:
        print(f"\n🎉 SUCCESS! Download link obtained:")
        print(f"Link: {download_link}")
        
        # Test if the link actually works
        print("\n🔍 Testing download link...")
        try:
            head_response = requests.head(download_link, timeout=10)
            print(f"Link Status: {head_response.status_code}")
            print(f"Content-Type: {head_response.headers.get('content-type', 'unknown')}")
            print(f"Content-Length: {head_response.headers.get('content-length', 'unknown')} bytes")
            
            if head_response.status_code == 200:
                print("✅ Download link is valid and ready!")
            else:
                print("⚠️  Download link returned non-200 status")
                
        except Exception as e:
            print(f"⚠️  Could not verify download link: {e}")
    else:
        print("\n❌ FAILED: Could not get download link from any API")
        print("This might indicate:")
        print("- API key issues")
        print("- Subscription limits")
        print("- Service unavailability")

if __name__ == "__main__":
    main()