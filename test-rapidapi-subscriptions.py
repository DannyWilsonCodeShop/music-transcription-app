#!/usr/bin/env python3
"""
Test what RapidAPI subscriptions you currently have
"""

import requests
import json

def test_subscription_status(api_key):
    """Test various endpoints to see what you're subscribed to"""
    
    # Test different YouTube-related endpoints
    endpoints = [
        {
            "name": "YouTube MP3 Downloader (youtube-mp36)",
            "url": "https://youtube-mp36.p.rapidapi.com/dl",
            "params": {"id": "dQw4w9WgXcQ"},
            "host": "youtube-mp36.p.rapidapi.com"
        },
        {
            "name": "YouTube Video Downloader (youtube-video-download1)",
            "url": "https://youtube-video-download1.p.rapidapi.com/dl",
            "params": {"id": "dQw4w9WgXcQ"},
            "host": "youtube-video-download1.p.rapidapi.com"
        },
        {
            "name": "YouTube Search and Download",
            "url": "https://youtube-search-and-download.p.rapidapi.com/video",
            "params": {"id": "dQw4w9WgXcQ"},
            "host": "youtube-search-and-download.p.rapidapi.com"
        },
        {
            "name": "YouTube Downloader v9",
            "url": "https://youtube-downloader9.p.rapidapi.com/v2/video",
            "params": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            "host": "youtube-downloader9.p.rapidapi.com"
        },
        {
            "name": "YouTube Data API v3.1",
            "url": "https://youtube-v31.p.rapidapi.com/search",
            "params": {"q": "test", "part": "snippet", "maxResults": "1"},
            "host": "youtube-v31.p.rapidapi.com"
        }
    ]
    
    print("🔍 Testing your current RapidAPI subscriptions...")
    print(f"API Key: {api_key[:10]}...")
    print()
    
    for endpoint in endpoints:
        print(f"Testing: {endpoint['name']}")
        
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": endpoint['host']
        }
        
        try:
            response = requests.get(
                endpoint['url'], 
                headers=headers, 
                params=endpoint['params'],
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ SUBSCRIBED! Status: {response.status_code}")
                try:
                    data = response.json()
                    print(f"   Sample response: {str(data)[:100]}...")
                except:
                    print(f"   Response: {response.text[:100]}...")
                print()
                return endpoint  # Return the first working one
                
            elif response.status_code == 403:
                print(f"❌ Not subscribed (403)")
                
            elif response.status_code == 429:
                print(f"⚠️  Rate limited (429) - but you ARE subscribed!")
                print("   Try again in a few minutes")
                return endpoint
                
            else:
                print(f"❓ Status {response.status_code}: {response.text[:50]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    return None

def main():
    api_key = "252611e8d7mshdde3262a7e2137bp12792bjsn7ce487b8a3dc"
    
    working_endpoint = test_subscription_status(api_key)
    
    print("="*60)
    
    if working_endpoint:
        print("🎉 FOUND A WORKING API!")
        print(f"Name: {working_endpoint['name']}")
        print(f"Host: {working_endpoint['host']}")
        print(f"URL: {working_endpoint['url']}")
        print()
        print("✅ You can use this API in your Lambda function!")
        print("✅ Update the youtube-downloader-rapidapi.py to use this endpoint")
        
    else:
        print("❌ No working YouTube APIs found")
        print()
        print("Next steps:")
        print("1. Go to https://rapidapi.com/")
        print("2. Search for 'YouTube MP3' or 'YouTube download'")
        print("3. Subscribe to one with good ratings")
        print("4. Look for free tiers (usually 100-1000 requests/month)")
        print()
        print("Popular options:")
        print("- YouTube MP3 Downloader")
        print("- YouTube Video Downloader") 
        print("- YouTube to MP3 Converter")

if __name__ == "__main__":
    main()