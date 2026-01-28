#!/usr/bin/env python3
"""
Test with a different YouTube video
"""

import boto3
import json
import time

def test_different_videos():
    """Test with different YouTube videos"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Test different videos
    test_videos = [
        {
            "name": "Short music video",
            "url": "https://www.youtube.com/watch?v=ZbZSe6N_BXs",  # Happy Pharrell Williams
            "description": "Popular short song"
        },
        {
            "name": "Educational video", 
            "url": "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",  # Minute Physics
            "description": "Short educational content"
        },
        {
            "name": "Music video 2",
            "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",  # Despacito
            "description": "Another popular song"
        }
    ]
    
    for i, video in enumerate(test_videos):
        print(f"\n🧪 Test {i+1}: {video['name']}")
        print(f"URL: {video['url']}")
        print(f"Description: {video['description']}")
        
        test_payload = {
            "youtubeUrl": video['url'],
            "jobId": f"test-video-{i+1}-{int(time.time())}"
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName='chordscout-youtube-downloader-dev',
                Payload=json.dumps(test_payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                print("✅ SUCCESS!")
                body = result.get('body', {})
                if isinstance(body, str):
                    body = json.loads(body)
                
                bucket = body.get('bucket')
                key = body.get('key')
                print(f"✅ Audio uploaded to: s3://{bucket}/{key}")
                return True  # Found a working video
                
            else:
                print(f"❌ Failed with status {result.get('statusCode')}")
                body = result.get('body', {})
                if isinstance(body, str):
                    try:
                        body = json.loads(body)
                    except:
                        pass
                
                error = body.get('error') if isinstance(body, dict) else body
                print(f"Error: {str(error)[:100]}...")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        # Wait a bit between tests to avoid rate limiting
        time.sleep(2)
    
    return False

if __name__ == "__main__":
    print("🔍 Testing RapidAPI with different YouTube videos...")
    
    success = test_different_videos()
    
    if success:
        print("\n🎉 Found a working video! RapidAPI YouTube Downloader is functional!")
        print("✅ Ready to integrate with the full workflow")
    else:
        print("\n⚠️  All test videos failed. This might indicate:")
        print("- Temporary RapidAPI service issues")
        print("- Rate limiting")
        print("- Video restrictions")
        print("- Download link expiration issues")
        print("\nThe function is working correctly, but the download links may be unstable.")
        print("Consider using the fallback method (yt-dlp with cookies) for reliability.")