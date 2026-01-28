#!/usr/bin/env python3
"""
Debug RapidAPI issues - test multiple services
"""

import requests
import json

def test_multiple_apis(api_key):
    """Test multiple YouTube download APIs"""
    
    video_id = "dQw4w9WgXcQ"  # Rick Roll
    
    # Test different APIs
    apis = [
        {
            "name": "YouTube MP3 Downloader",
            "url": "https://youtube-mp36.p.rapidapi.com/dl",
            "method": "GET",
            "params": {"id": video_id},
            "headers": {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"
            }
        },
        {
            "name": "YouTube to MP3 v2",
            "url": "https://youtube-to-mp315.p.rapidapi.com/download",
            "method": "POST",
            "json": {
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "format": "mp3",
                "quality": "128"
            },
            "headers": {
                "content-type": "application/json",
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "youtube-to-mp315.p.rapidapi.com"
            }
        },
        {
            "name": "YouTube Video Downloader",
            "url": "https://youtube-video-download1.p.rapidapi.com/dl",
            "method": "GET",
            "params": {"id": video_id},
            "headers": {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "youtube-video-download1.p.rapidapi.com"
            }
        },
        {
            "name": "YouTube Media Downloader",
            "url": "https://youtube-media-downloader.p.rapidapi.com/v2/video/details",
            "method": "GET",
            "params": {"videoId": video_id},
            "headers": {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "youtube-media-downloader.p.rapidapi.com"
            }
        }
    ]
    
    for api in apis:
        print(f"\n🧪 Testing: {api['name']}")
        print(f"URL: {api['url']}")
        
        try:
            if api['method'] == 'GET':
                response = requests.get(
                    api['url'], 
                    headers=api['headers'], 
                    params=api.get('params', {}),
                    timeout=30
                )
            else:
                response = requests.post(
                    api['url'], 
                    headers=api['headers'], 
                    json=api.get('json', {}),
                    timeout=30
                )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print("✅ SUCCESS!")
                    print(json.dumps(data, indent=2)[:500] + "..." if len(str(data)) > 500 else json.dumps(data, indent=2))
                except:
                    print("✅ SUCCESS! (Non-JSON response)")
                    print(response.text[:200] + "..." if len(response.text) > 200 else response.text)
                    
            elif response.status_code == 403:
                print("❌ 403 Forbidden - Not subscribed to this API")
                
            elif response.status_code == 429:
                print("⚠️  429 Rate Limited - API key works but hit limits")
                
            else:
                print(f"❌ {response.status_code}")
                print(response.text[:200])
                
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    api_key = "252611e8d7mshdde3262a7e2137bp12792bjsn7ce487b8a3dc"
    
    print("🔍 Testing multiple RapidAPI YouTube services...")
    print(f"API Key: {api_key[:10]}...")
    
    test_multiple_apis(api_key)
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print("- If you see 403 errors, you need to subscribe to that specific API")
    print("- If you see 200 responses, that API is working!")
    print("- If you see 429 errors, your key works but you hit rate limits")
    print("\nNext steps:")
    print("1. Find an API that returns 200")
    print("2. Update the Lambda function to use that API")
    print("3. Deploy and test the full workflow")

if __name__ == "__main__":
    main()