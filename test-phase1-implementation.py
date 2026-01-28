#!/usr/bin/env python3
"""
Test Phase 1 Implementation - NEW_ARCHITECTURE.md
Tests the improved YouTube downloader with RapidAPI + fallbacks
"""

import requests
import json
import time
import boto3
from datetime import datetime

def test_rapidapi_direct():
    """Test RapidAPI directly (not through Lambda)"""
    
    print("🔑 Testing RapidAPI Direct Integration")
    print("-" * 40)
    
    rapidapi_key = "252611e8d7mshdde3262a7e2137bp12792bjsn7ce487b8a3dc"
    test_videos = [
        ("dQw4w9WgXcQ", "Rick Astley - Never Gonna Give You Up"),
        ("ZbZSe6N_BXs", "Short music video"),
        ("fJ9rUzIMcZQ", "Educational content")
    ]
    
    results = []
    
    for video_id, description in test_videos:
        print(f"\n🎵 Testing: {description} ({video_id})")
        
        try:
            response = requests.get(
                "https://youtube-mp36.p.rapidapi.com/dl",
                params={"id": video_id},
                headers={
                    "x-rapidapi-key": rapidapi_key,
                    "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'ok':
                    download_url = data.get('link')
                    title = data.get('title', 'Unknown')
                    duration = data.get('duration', 0)
                    
                    print(f"✅ API Success: {title}")
                    print(f"   Duration: {duration}s")
                    print(f"   Download URL: {download_url[:50]}...")
                    
                    # Test download link
                    try:
                        head_response = requests.head(download_url, timeout=10)
                        if head_response.status_code == 200:
                            print(f"✅ Download link valid")
                            results.append((video_id, True, "Success"))
                        else:
                            print(f"❌ Download link failed: {head_response.status_code}")
                            results.append((video_id, False, f"Download link {head_response.status_code}"))
                    except Exception as e:
                        print(f"❌ Download link test failed: {str(e)}")
                        results.append((video_id, False, f"Download test: {str(e)}"))
                        
                else:
                    error_msg = data.get('msg', 'Unknown error')
                    print(f"❌ API Error: {error_msg}")
                    results.append((video_id, False, f"API error: {error_msg}"))
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                results.append((video_id, False, f"HTTP {response.status_code}"))
                
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")
            results.append((video_id, False, f"Request: {str(e)}"))
        
        time.sleep(2)  # Rate limiting
    
    # Summary
    print(f"\n📊 RapidAPI Test Summary:")
    print("-" * 40)
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for video_id, success, message in results:
        status = "✅" if success else "❌"
        print(f"{status} {video_id}: {message}")
    
    print(f"\nSuccess Rate: {successful}/{total} ({successful/total*100:.1f}%)")
    
    return successful == total

def test_lambda_function():
    """Test the Lambda function end-to-end"""
    
    print("\n🚀 Testing Lambda Function")
    print("-" * 40)
    
    function_name = input("Enter Lambda function name (or press Enter for default): ").strip()
    if not function_name:
        function_name = 'youtube-downloader-dev'
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    test_cases = [
        {
            'name': 'Rick Astley (Popular)',
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'video_id': 'dQw4w9WgXcQ'
        },
        {
            'name': 'Short Video',
            'url': 'https://www.youtube.com/watch?v=ZbZSe6N_BXs',
            'video_id': 'ZbZSe6N_BXs'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🎵 Testing: {test_case['name']}")
        
        # Create test event
        test_event = {
            'jobId': f"test-{int(datetime.now().timestamp())}",
            'youtubeUrl': test_case['url'],
            'videoId': test_case['video_id']
        }
        
        try:
            print("   Invoking Lambda...")
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            # Parse response
            payload = json.loads(response['Payload'].read())
            
            if response['StatusCode'] == 200:
                if payload.get('statusCode') == 200:
                    body = payload.get('body', {})
                    method = body.get('method', 'Unknown')
                    file_size = body.get('fileSize', 0)
                    title = body.get('videoTitle', 'Unknown')
                    
                    print(f"✅ Success!")
                    print(f"   Method: {method}")
                    print(f"   Title: {title}")
                    print(f"   Size: {file_size:,} bytes")
                    
                    results.append((test_case['name'], True, method))
                else:
                    error = payload.get('body', {}).get('error', 'Unknown error')
                    print(f"❌ Function Error: {error}")
                    results.append((test_case['name'], False, f"Error: {error}"))
            else:
                print(f"❌ Lambda Error: {response['StatusCode']}")
                results.append((test_case['name'], False, f"Lambda {response['StatusCode']}"))
                
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            results.append((test_case['name'], False, f"Exception: {str(e)}"))
        
        time.sleep(5)  # Give Lambda time to process
    
    # Summary
    print(f"\n📊 Lambda Test Summary:")
    print("-" * 40)
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, message in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}: {message}")
    
    print(f"\nSuccess Rate: {successful}/{total} ({successful/total*100:.1f}%)")
    
    return successful == total

def test_cost_estimation():
    """Estimate costs for Phase 1 implementation"""
    
    print("\n💰 Cost Estimation - Phase 1")
    print("-" * 40)
    
    # Based on NEW_ARCHITECTURE.md estimates
    costs = {
        'RapidAPI per download': 0.005,
        'Lambda compute': 0.001,
        'S3 storage': 0.0001,
        'DynamoDB': 0.0001,
        'Total per song': 0.0062
    }
    
    volumes = [100, 1000, 10000]
    
    print("Cost breakdown per download:")
    for item, cost in costs.items():
        print(f"  {item}: ${cost:.4f}")
    
    print(f"\nProjected costs at different volumes:")
    for volume in volumes:
        total_cost = costs['Total per song'] * volume
        print(f"  {volume:,} downloads: ${total_cost:.2f}")
    
    print(f"\nComparison with alternatives:")
    print(f"  Current (yt-dlp only): ${0.001 * 1000:.2f} per 1000 (but unreliable)")
    print(f"  Phase 1 (RapidAPI): ${costs['Total per song'] * 1000:.2f} per 1000")
    print(f"  Phase 2 (ECS): ${0.059 * 1000:.2f} per 1000")

def check_environment():
    """Check if environment is properly configured"""
    
    print("\n🔧 Environment Check")
    print("-" * 40)
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Account: {identity['Account']}")
        print(f"✅ AWS User: {identity['Arn'].split('/')[-1]}")
    except Exception as e:
        print(f"❌ AWS credentials issue: {str(e)}")
        return False
    
    # Check if Lambda function exists
    function_name = 'youtube-downloader-dev'
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        response = lambda_client.get_function(FunctionName=function_name)
        print(f"✅ Lambda function exists: {function_name}")
        print(f"   Runtime: {response['Configuration']['Runtime']}")
        print(f"   Last Modified: {response['Configuration']['LastModified']}")
    except Exception as e:
        print(f"⚠️  Lambda function not found: {function_name}")
        print(f"   You may need to deploy it first")
    
    # Check DynamoDB table
    table_name = 'chordscout-jobs-dev'
    try:
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        response = dynamodb.describe_table(TableName=table_name)
        print(f"✅ DynamoDB table exists: {table_name}")
    except Exception as e:
        print(f"⚠️  DynamoDB table not found: {table_name}")
    
    # Check S3 bucket
    bucket_name = 'chordscout-audio-temp-dev-090130568474'
    try:
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket exists: {bucket_name}")
    except Exception as e:
        print(f"⚠️  S3 bucket not found: {bucket_name}")
    
    return True

def main():
    """Main test function"""
    
    print("🧪 Phase 1 Implementation Testing")
    print("=" * 60)
    print("Testing the NEW_ARCHITECTURE.md Phase 1 strategy:")
    print("- RapidAPI as primary method")
    print("- Fallback mechanisms")
    print("- Cost estimation")
    print("- Environment validation")
    print()
    
    # Environment check
    if not check_environment():
        print("❌ Environment issues detected. Please fix before continuing.")
        return
    
    # Test RapidAPI directly
    rapidapi_success = test_rapidapi_direct()
    
    # Test Lambda function
    lambda_success = test_lambda_function()
    
    # Cost estimation
    test_cost_estimation()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 FINAL SUMMARY")
    print("=" * 60)
    
    if rapidapi_success and lambda_success:
        print("✅ Phase 1 implementation is working!")
        print("✅ Ready for production deployment")
        print()
        print("Next steps:")
        print("1. Deploy to production environment")
        print("2. Monitor success rates and costs")
        print("3. Consider Phase 2 (ECS) if needed")
    elif rapidapi_success:
        print("⚠️  RapidAPI works but Lambda has issues")
        print("🔧 Check Lambda function deployment")
    else:
        print("❌ RapidAPI integration has issues")
        print("🔧 Check API keys and subscription status")
    
    print(f"\n📊 Overall Status:")
    print(f"   RapidAPI: {'✅' if rapidapi_success else '❌'}")
    print(f"   Lambda: {'✅' if lambda_success else '❌'}")

if __name__ == "__main__":
    main()