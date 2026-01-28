#!/usr/bin/env python3
"""
Simple RapidAPI test - just provide your key when prompted
"""

import requests
import json

def test_rapidapi():
    # Get API key from user
    api_key = input("Enter your RapidAPI key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return
    
    # Test with Rick Roll video (short and reliable)
    video_id = "dQw4w9WgXcQ"
    
    print(f"🚀 Testing RapidAPI with video ID: {video_id}")
    print(f"Using API Key: {api_key[:10]}...")
    
    # Test primary service
    url = "https://youtube-mp36.p.rapidapi.com/dl"
    
    querystring = {"id": video_id}
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"
    }
    
    try:
        print("📡 Making API request...")
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! Response:")
            print(json.dumps(data, indent=2))
            
            if data.get('status') == 'ok' and data.get('link'):
                print(f"\n🎉 Got download link: {data['link']}")
                
                # Test the download link
                print("🔍 Testing download link...")
                head_response = requests.head(data['link'], timeout=10)
                print(f"Link Status: {head_response.status_code}")
                
                if head_response.status_code == 200:
                    print("✅ Download link is working!")
                    print("🎯 RapidAPI upgrade is successful!")
                else:
                    print("⚠️  Download link returned non-200 status")
            else:
                print("❌ No download link in response")
                
        elif response.status_code == 429:
            print("❌ Rate limit exceeded - but this means API key is working!")
            print("Try again in a few minutes")
            
        elif response.status_code == 403:
            print("❌ Forbidden - check your API key and subscription")
            
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_rapidapi()