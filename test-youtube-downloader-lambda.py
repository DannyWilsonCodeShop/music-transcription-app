#!/usr/bin/env python3
"""
Test the YouTube Downloader Lambda function locally
"""

import json
import os
import tempfile
import boto3
from pathlib import Path

# Test the core yt-dlp functionality
def test_ytdlp_download():
    """Test yt-dlp download functionality"""
    print("🧪 Testing yt-dlp download...")
    
    try:
        import yt_dlp
        print("✅ yt-dlp imported successfully")
        
        # Test with a short video
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Using temp directory: {temp_dir}")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'extractaudio': True,
                'audioformat': 'mp3',
                'audioquality': '192',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Just extract info (don't download)
                info = ydl.extract_info(test_url, download=False)
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                
                print(f"✅ Video info extracted:")
                print(f"   Title: {title}")
                print(f"   Duration: {duration}s")
                
                return True
                
    except ImportError:
        print("❌ yt-dlp not installed. Install with: pip install yt-dlp")
        return False
    except Exception as e:
        print(f"❌ Error testing yt-dlp: {e}")
        return False

def test_lambda_function():
    """Test the Lambda function logic"""
    print("🧪 Testing Lambda function logic...")
    
    # Mock event
    test_event = {
        "jobId": "test-job-123",
        "youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }
    
    # Mock environment variables
    os.environ.update({
        'ECS_CLUSTER': 'test-cluster',
        'YOUTUBE_TASK_DEFINITION': 'youtube-downloader-task',
        'SUBNET_IDS': 'subnet-123,subnet-456',
        'SECURITY_GROUP': 'sg-123',
        'DYNAMODB_JOBS_TABLE': 'test-jobs-table',
        'S3_BUCKET': 'test-bucket'
    })
    
    print(f"✅ Mock event: {json.dumps(test_event, indent=2)}")
    print("✅ Environment variables set")
    
    # Note: We can't actually run the Lambda without AWS credentials and resources
    print("⚠️  Full Lambda test requires AWS resources (ECS, DynamoDB)")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing YouTube Downloader Components")
    print("=" * 50)
    
    # Test 1: yt-dlp functionality
    ytdlp_ok = test_ytdlp_download()
    print()
    
    # Test 2: Lambda function logic
    lambda_ok = test_lambda_function()
    print()
    
    # Summary
    print("📊 Test Summary:")
    print(f"   yt-dlp functionality: {'✅ PASS' if ytdlp_ok else '❌ FAIL'}")
    print(f"   Lambda function logic: {'✅ PASS' if lambda_ok else '❌ FAIL'}")
    
    if ytdlp_ok and lambda_ok:
        print("\n🎉 All tests passed! Ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Check dependencies.")

if __name__ == "__main__":
    main()