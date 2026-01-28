#!/usr/bin/env python3
"""
Find working YouTube APIs on RapidAPI
"""

import requests
import json

def test_popular_youtube_apis(api_key):
    """Test popular YouTube APIs that might be available"""
    
    video_id = "dQw4w9WgXcQ"
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Popular YouTube APIs on RapidAPI
    apis = [
        {
            "name": "YouTube v3.1",
            "url": "https://youtube-v31.p.rapidapi.com/search",
            "method": "GET",
            "params": {"q": "test", "part": "snippet", "maxResults": "1"},
            "headers": {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "youtube-v31.p.rapidapi.com"
            }
        },
        {
            "name": "YouTube Data API v3",
            "url": "https://youtube-data8.p.rapidapi.com/video/",
            "method": "GET",
            "params": {"id": video_id},
            "headers": {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "youtube-data8.p.rapidapi.com"
            }
        },
        {
            "name": "YouTube Search and Download",
            "url": "https://youtube-search-and-download.p.rapidapi.com/video",
            "method": "GET",
            "params": {"id": video_id},
            "headers": {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "youtube-search-and-download.p.rapidapi.com"
            }
        },
        {
            "name": "YouTube Downloader",
            "url": "https://youtube-downloader9.p.rapidapi.com/v2/video",
            "method": "GET",
            "params": {"url": youtube_url},
            "headers": {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "youtube-downloader9.p.rapidapi.com"
            }
        },
        {
            "name": "YouTube MP3 Converter",
            "url": "https://youtube-mp3-converter2.p.rapidapi.com/mp3/mp3",
            "method": "GET",
            "params": {"url": youtube_url},
            "headers": {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "youtube-mp3-converter2.p.rapidapi.com"
            }
        },
        {
            "name": "YouTube Video Info",
            "url": "https://youtube-video-info1.p.rapidapi.com/youtube",
            "method": "GET",
            "params": {"url": youtube_url},
            "headers": {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "youtube-video-info1.p.rapidapi.com"
            }
        }
    ]
    
    working_apis = []
    
    for api in apis:
        print(f"\n🧪 Testing: {api['name']}")
        
        try:
            if api['method'] == 'GET':
                response = requests.get(
                    api['url'], 
                    headers=api['headers'], 
                    params=api.get('params', {}),
                    timeout=15
                )
            else:
                response = requests.post(
                    api['url'], 
                    headers=api['headers'], 
                    json=api.get('json', {}),
                    timeout=15
                )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ WORKING!")
                try:
                    data = response.json()
                    print("Response preview:")
                    print(json.dumps(data, indent=2)[:300] + "...")
                    working_apis.append({
                        'name': api['name'],
                        'url': api['url'],
                        'host': api['headers']['x-rapidapi-host'],
                        'response': data
                    })
                except:
                    print("Response (non-JSON):")
                    print(response.text[:200] + "...")
                    
            elif response.status_code == 403:
                print("❌ Not subscribed")
                
            elif response.status_code == 429:
                print("⚠️  Rate limited (but key works)")
                
            else:
                print(f"❌ {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return working_apis

def main():
    api_key = "252611e8d7mshdde3262a7e2137bp12792bjsn7ce487b8a3dc"
    
    print("🔍 Searching for working YouTube APIs...")
    print(f"API Key: {api_key[:10]}...")
    
    working_apis = test_popular_youtube_apis(api_key)
    
    print("\n" + "="*60)
    print("WORKING APIs FOUND:")
    
    if working_apis:
        for api in working_apis:
            print(f"✅ {api['name']}")
            print(f"   Host: {api['host']}")
            print(f"   URL: {api['url']}")
            print()
    else:
        print("❌ No working APIs found")
        print("\nYou need to:")
        print("1. Go to RapidAPI.com")
        print("2. Search for 'YouTube download' or 'YouTube MP3'")
        print("3. Subscribe to a free/paid plan for one of these APIs:")
        print("   - YouTube MP3 Downloader")
        print("   - YouTube Video Downloader")
        print("   - YouTube to MP3 Converter")
        print("4. Come back and test again")

if __name__ == "__main__":
    main()