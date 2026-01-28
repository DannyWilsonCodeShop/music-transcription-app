#!/usr/bin/env python3
"""
Test YouTube cookies with yt-dlp
"""

import yt_dlp
import os

# Test with a popular music video
TEST_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
COOKIES_PATH = "public/cookies.txt"

def test_cookies():
    """Test if cookies work with yt-dlp"""
    
    print(f"Testing YouTube cookies from: {COOKIES_PATH}")
    print(f"Test URL: {TEST_URL}")
    print("-" * 60)
    
    if not os.path.exists(COOKIES_PATH):
        print(f"ERROR: Cookies file not found at {COOKIES_PATH}")
        return False
    
    # yt-dlp options - just extract info, don't download
    ydl_opts = {
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'cookiefile': COOKIES_PATH,
        'skip_download': True,  # Don't actually download, just test access
        'nocheckcertificate': True,  # Skip SSL verification for local testing
    }
    
    try:
        print("\nAttempting to extract video info with cookies...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(TEST_URL, download=False)
            
            print("\n✅ SUCCESS! Cookies are working!")
            print(f"\nVideo Info:")
            print(f"  Title: {info.get('title', 'Unknown')}")
            print(f"  Duration: {info.get('duration', 0)} seconds")
            print(f"  Uploader: {info.get('uploader', 'Unknown')}")
            print(f"  View Count: {info.get('view_count', 'Unknown')}")
            
            # Check available formats
            formats = info.get('formats', [])
            audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            print(f"\n  Available audio-only formats: {len(audio_formats)}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ FAILED! Error: {str(e)}")
        print("\nThis could mean:")
        print("  1. Cookies are expired or invalid")
        print("  2. YouTube is blocking the request")
        print("  3. Network/connection issue")
        return False

if __name__ == "__main__":
    success = test_cookies()
    exit(0 if success else 1)
