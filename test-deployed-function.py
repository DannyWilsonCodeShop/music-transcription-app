#!/usr/bin/env python3
"""
Test the deployed RapidAPI Lambda function
"""

import boto3
import json
import time

def test_lambda_function():
    """Test the deployed Lambda function"""
    
    # Create Lambda client
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Test payload
    test_payload = {
        "youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "jobId": f"test-rapidapi-{int(time.time())}"
    }
    
    print("🧪 Testing deployed Lambda function...")
    print(f"Function: chordscout-youtube-downloader-dev")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    print()
    
    try:
        # Invoke the function
        response = lambda_client.invoke(
            FunctionName='chordscout-youtube-downloader-dev',
            Payload=json.dumps(test_payload)
        )
        
        # Read the response
        response_payload = response['Payload'].read()
        result = json.loads(response_payload)
        
        print("📋 Lambda Response:")
        print(json.dumps(result, indent=2))
        print()
        
        # Check the result
        if result.get('statusCode') == 200:
            print("🎉 SUCCESS! RapidAPI YouTube Downloader is working!")
            
            body = result.get('body', {})
            if isinstance(body, str):
                body = json.loads(body)
                
            bucket = body.get('bucket')
            key = body.get('key')
            
            if bucket and key:
                print(f"✅ Audio uploaded to: s3://{bucket}/{key}")
                print("✅ Ready for transcription!")
                
                # Test if file exists in S3
                s3_client = boto3.client('s3')
                try:
                    s3_client.head_object(Bucket=bucket, Key=key)
                    print("✅ File confirmed in S3!")
                except:
                    print("⚠️  File not found in S3 (might still be uploading)")
            else:
                print("⚠️  No S3 location in response")
                
        else:
            print("❌ Function returned an error:")
            print(f"Status Code: {result.get('statusCode')}")
            
            body = result.get('body', {})
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except:
                    pass
            
            error = body.get('error') if isinstance(body, dict) else body
            print(f"Error: {error}")
            
    except Exception as e:
        print(f"❌ Error invoking function: {e}")

if __name__ == "__main__":
    test_lambda_function()