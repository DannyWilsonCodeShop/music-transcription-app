#!/usr/bin/env python3
"""
Test Apify YouTube Video Downloader Integration
Tests the new Apify-based approach for YouTube downloads
"""

import requests
import time
import json
import os
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    parsed = urlparse(url)
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed.path == '/watch':
            return parse_qs(parsed.query)['v'][0]
    elif parsed.hostname in ['youtu.be']:
        return parsed.path[1:]
    return None

def test_apify_download(youtube_url, apify_token):
    """Test Apify YouTube Video Downloader"""
    
    print(f"🚀 Testing Apify with: {youtube_url}")
    print(f"Video ID: {extract_video_id(youtube_url)}")
    
    # Start Apify actor run
    print("\n📡 Starting Apify actor...")
    run_response = requests.post(
        'https://api.apify.com/v2/acts/streamers~youtube-video-downloader/runs',
        json={
            'videos': [youtube_url],
            'maxItems': 1
        },
        params={'token': apify_token}
    )
    
    if run_response.status_code != 201:
        print(f"❌ Failed to start Apify actor: {run_response.status_code}")
        print(f"Response: {run_response.text}")
        return False
    
    run_data = run_response.json()
    run_id = run_data['data']['id']
    
    print(f"✅ Apify run started: {run_id}")
    
    # Wait for run to complete
    print("\n⏳ Waiting for completion...")
    max_attempts = 60  # 3 minutes max
    
    for attempt in range(max_attempts):
        time.sleep(3)
        
        status_response = requests.get(
            f'https://api.apify.com/v2/acts/streamers~youtube-video-downloader/runs/{run_id}',
            params={'token': apify_token}
        )
        
        if status_response.status_code != 200:
            print(f"❌ Failed to get run status: {status_response.text}")
            return False
        
        status_data = status_response.json()
        status = status_data['data']['status']
        
        print(f"Status: {status} (attempt {attempt + 1}/{max_attempts})")
        
        if status == 'SUCCEEDED':
            print("✅ Apify run completed successfully!")
            break
        elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
            print(f"❌ Apify run failed with status: {status}")
            return False
    else:
        print("❌ Apify run timed out after 3 minutes")
        return False
    
    # Get dataset items
    print("\n📊 Retrieving video data...")
    dataset_id = status_data['data']['defaultDatasetId']
    dataset_response = requests.get(
        f'https://api.apify.com/v2/datasets/{dataset_id}/items',
        params={'token': apify_token}
    )
    
    if dataset_response.status_code != 200:
        print(f"❌ Failed to get dataset: {dataset_response.text}")
        return False
    
    items = dataset_response.json()
    
    if not items or len(items) == 0:
        print("❌ No video data returned from Apify")
        return False
    
    video_data = items[0]
    
    print(f"✅ Video data retrieved!")
    print(f"Available keys: {list(video_data.keys())}")
    
    # Extract metadata
    metadata = {
        'title': video_data.get('title', video_data.get('name', 'Unknown')),
        'duration': video_data.get('duration', video_data.get('lengthSeconds', 0)),
        'uploader': video_data.get('author', video_data.get('channelName', 'Unknown'))
    }
    
    print(f"\n📋 Video Metadata:")
    print(f"Title: {metadata['title']}")
    print(f"Duration: {metadata['duration']} seconds")
    print(f"Uploader: {metadata['uploader']}")
    
    # Check download links
    download_links = video_data.get('downloadLinks', {})
    
    if not download_links:
        print("❌ No download links found")
        print(f"Available data keys: {list(video_data.keys())}")
        return False
    
    print(f"\n🔗 Available download formats:")
    for quality, url in download_links.items():
        print(f"  {quality}: {url[:100]}...")
    
    # Try to find best audio format
    audio_url = None
    extension = 'webm'
    
    # Look for audio formats in order of preference
    for quality in ['audio_high', 'audio_medium', 'audio_low', 'audio']:
        if quality in download_links:
            audio_url = download_links[quality]
            print(f"✅ Selected audio format: {quality}")
            break
    
    # Fallback to video formats
    if not audio_url:
        for quality in ['360p', '480p', '720p']:
            if quality in download_links:
                audio_url = download_links[quality]
                extension = 'mp4'
                print(f"✅ Selected video format: {quality}")
                break
    
    if not audio_url:
        # Last resort
        audio_url = list(download_links.values())[0]
        extension = 'mp4'
        print(f"✅ Selected first available format")
    
    # Test download link
    print(f"\n🔍 Testing download link...")
    head_response = requests.head(audio_url, timeout=10)
    
    if head_response.status_code == 200:
        content_length = head_response.headers.get('content-length', 'Unknown')
        content_type = head_response.headers.get('content-type', 'Unknown')
        
        print(f"✅ Download link is valid!")
        print(f"Content-Length: {content_length} bytes")
        print(f"Content-Type: {content_type}")
        
        # Test small download
        print(f"\n📥 Testing small download (first 1KB)...")
        partial_response = requests.get(audio_url, headers={'Range': 'bytes=0-1023'}, timeout=10)
        
        if partial_response.status_code in [200, 206]:
            print(f"✅ Partial download successful: {len(partial_response.content)} bytes")
            return True
        else:
            print(f"❌ Partial download failed: {partial_response.status_code}")
            return False
    else:
        print(f"❌ Download link failed: {head_response.status_code}")
        return False

def main():
    """Main test function"""
    
    # Get Apify token
    apify_token = input("Enter your Apify API token: ").strip()
    
    if not apify_token:
        print("❌ Apify token is required")
        return
    
    # Test videos
    test_videos = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (classic test)
        "https://www.youtube.com/watch?v=ZbZSe6N_BXs",  # Short music video
        "https://youtu.be/fJ9rUzIMcZQ"                  # Short URL format
    ]
    
    print("🧪 Testing Apify YouTube Video Downloader Integration\n")
    
    results = []
    
    for i, video_url in enumerate(test_videos, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(test_videos)}")
        print(f"{'='*60}")
        
        try:
            success = test_apify_download(video_url, apify_token)
            results.append((video_url, success))
            
            if success:
                print(f"✅ Test {i} PASSED")
            else:
                print(f"❌ Test {i} FAILED")
                
        except Exception as e:
            print(f"❌ Test {i} ERROR: {str(e)}")
            results.append((video_url, False))
        
        if i < len(test_videos):
            print("\n⏸️  Waiting 5 seconds before next test...")
            time.sleep(5)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for i, (url, success) in enumerate(results, 1):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"Test {i}: {status} - {extract_video_id(url)}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Apify integration is working perfectly.")
    elif passed > 0:
        print("⚠️  Partial success. Apify works but may have reliability issues.")
    else:
        print("❌ All tests failed. Apify integration needs troubleshooting.")

if __name__ == "__main__":
    main()