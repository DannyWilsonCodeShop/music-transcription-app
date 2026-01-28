#!/usr/bin/env python3
"""
Test alternative RapidAPI YouTube services for better stability
"""

import requests
import json

def test_alternative_services():
    """Test different RapidAPI YouTube services"""
    
    api_key = "252611e8d7mshdde3262a7e2137bp12792bjsn7ce487b8a3dc"
    video_id = "dQw4w9WgXcQ"  # Rick Roll
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Alternative RapidAPI services to try
    services = [
        {
            "name": "YouTube MP3 Downloader v2",
            "host": "youtube-mp3-downloader2.p.rapidapi.com",
            "url": "https://youtube-mp3-downloader2.p.rapidapi.com/ytmp3/ytmp3/",
            "method": "GET",
            "params": {"url": youtube_url}
        },
        {
            "name": "YouTube Video and Audio Downloader",
            "host": "youtube-video-and-audio-downloader.p.rapidapi.com", 
            "url": "https://youtube-video-and-audio-downloader.p.rapidapi.com/youtube",
            "method": "GET",
            "params": {"url": youtube_url, "format": "mp3"}
        },
        {
            "name": "YouTube MP3 Converter",
            "host": "youtube-mp3-converter1.p.rapidapi.com",
            "url": "https://youtube-mp3-converter1.p.rapidapi.com/mp3",
            "method": "GET", 
            "params": {"youtube": youtube_url}
        },
        {
            "name": "YouTube Downloader v8",
            "host": "youtube-downloader8.p.rapidapi.com",
            "url": "https://youtube-downloader8.p.rapidapi.com/v2/video",
            "method": "GET",
            "params": {"url": youtube_url}
        },
        {
            "name": "YouTube to MP3 API",
            "host": "youtube-to-mp3-api.p.rapidapi.com",
            "url": "https://youtube-to-mp3-api.p.rapidapi.com/download",
            "method": "POST",
            "json": {"url": youtube_url, "quality": "128"}
        }
    ]
    
    print("🔍 Testing Alternative RapidAPI YouTube Services")
    print("=" * 60)
    print(f"Video ID: {video_id}")
    print(f"API Key: {api_key[:10]}...")
    print()
    
    working_services = []
    
    for service in services:
        print(f"🧪 Testing: {service['name']}")
        print(f"Host: {service['host']}")
        
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": service['host']
        }
        
        try:
            if service['method'] == 'GET':
                response = requests.get(
                    service['url'],
                    headers=headers,
                    params=service.get('params', {}),
                    timeout=15
                )
            else:
                headers['content-type'] = 'application/json'
                response = requests.post(
                    service['url'],
                    headers=headers,
                    json=service.get('json', {}),
                    timeout=15
                )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print("✅ SUCCESS!")
                    print("Response preview:")
                    print(json.dumps(data, indent=2)[:300] + "...")
                    
                    # Look for download links in various response formats
                    download_link = None
                    if isinstance(data, dict):
                        # Common field names for download links
                        for field in ['link', 'download_url', 'url', 'mp3', 'audio_url', 'download_link']:
                            if field in data and data[field]:
                                download_link = data[field]
                                break
                        
                        # Check nested objects
                        if not download_link:
                            for key, value in data.items():
                                if isinstance(value, dict):
                                    for field in ['link', 'download_url', 'url', 'mp3']:
                                        if field in value and value[field]:
                                            download_link = value[field]
                                            break
                    
                    if download_link:
                        print(f"🎉 Found download link: {download_link}")
                        
                        # Test if the download link works
                        try:
                            head_response = requests.head(download_link, timeout=10)
                            print(f"Link test: {head_response.status_code}")
                            if head_response.status_code == 200:
                                print("✅ Download link is working!")
                                working_services.append({
                                    'name': service['name'],
                                    'host': service['host'],
                                    'url': service['url'],
                                    'method': service['method'],
                                    'download_link': download_link,
                                    'response': data
                                })
                            else:
                                print("⚠️  Download link returned non-200 status")
                        except Exception as e:
                            print(f"⚠️  Could not test download link: {e}")
                    else:
                        print("⚠️  No download link found in response")
                        
                except json.JSONDecodeError:
                    print("✅ SUCCESS! (Non-JSON response)")
                    print(f"Response: {response.text[:200]}...")
                    
            elif response.status_code == 403:
                print("❌ Not subscribed to this API")
            elif response.status_code == 429:
                print("⚠️  Rate limited (but API key works)")
            else:
                print(f"❌ {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("=" * 60)
    print("🎯 WORKING SERVICES SUMMARY")
    print("=" * 60)
    
    if working_services:
        print(f"✅ Found {len(working_services)} working service(s)!")
        for i, service in enumerate(working_services, 1):
            print(f"\n{i}. {service['name']}")
            print(f"   Host: {service['host']}")
            print(f"   Method: {service['method']}")
            print(f"   Download Link: {service['download_link'][:50]}...")
            
        print(f"\n🚀 RECOMMENDATION:")
        best_service = working_services[0]
        print(f"Use: {best_service['name']}")
        print(f"Host: {best_service['host']}")
        print(f"This service has working download links!")
        
        return working_services
    else:
        print("❌ No working services found")
        print("\nOptions:")
        print("1. Try premium RapidAPI subscriptions")
        print("2. Use your existing urllib method")
        print("3. Look for other YouTube download services")
        
        return []

if __name__ == "__main__":
    working_services = test_alternative_services()
    
    if working_services:
        print(f"\n📋 NEXT STEPS:")
        print("1. Update Lambda function to use working service")
        print("2. Deploy and test")
        print("3. Integrate with full workflow")
    else:
        print(f"\n📋 FALLBACK OPTIONS:")
        print("1. Deploy your working urllib method")
        print("2. Upgrade to premium RapidAPI services")
        print("3. Use hybrid approach (urllib + RapidAPI backup)")