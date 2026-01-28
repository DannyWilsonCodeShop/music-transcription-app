import json
import boto3
import requests
import os
from urllib.parse import urlparse, parse_qs

def lambda_handler(event, context):
    """
    Simplified YouTube downloader using RapidAPI service
    Focuses on reliability and clear error reporting
    """
    
    try:
        # Extract YouTube URL from event
        youtube_url = event.get('youtubeUrl')
        job_id = event.get('jobId', 'unknown')
        
        if not youtube_url:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'No YouTube URL provided'
                }
            }
        
        # Extract video ID from URL
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'Invalid YouTube URL format'
                }
            }
        
        print(f"Processing video ID: {video_id}")
        
        # Try RapidAPI with retry logic
        audio_url = None
        max_retries = 3
        
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1}/{max_retries}")
            audio_url = download_with_rapidapi(video_id)
            
            if audio_url:
                print(f"Got download URL: {audio_url}")
                break
            else:
                print(f"Attempt {attempt + 1} failed, retrying...")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)  # Wait 2 seconds before retry
        
        if not audio_url:
            return {
                'statusCode': 500,
                'body': {
                    'error': 'Failed to get download link from RapidAPI after 3 attempts'
                }
            }
        
        # Try to download and upload to S3 with retry
        s3_key = None
        for attempt in range(2):  # 2 attempts for download
            try:
                print(f"Download attempt {attempt + 1}/2")
                s3_key = upload_to_s3(audio_url, job_id)
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"Download link expired (404), attempt {attempt + 1}/2")
                    if attempt == 0:
                        # Try to get a fresh download link
                        print("Getting fresh download link...")
                        audio_url = download_with_rapidapi(video_id)
                        if not audio_url:
                            raise Exception("Failed to get fresh download link")
                    else:
                        raise Exception("Download link consistently failing with 404")
                else:
                    raise e
        
        if not s3_key:
            return {
                'statusCode': 500,
                'body': {
                    'error': 'Failed to download and upload audio file'
                }
            }
        
        return {
            'statusCode': 200,
            'body': {
                'bucket': os.environ['BUCKET_NAME'],
                'key': s3_key,
                'message': 'Audio downloaded successfully'
            }
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': {
                'error': f'Processing failed: {str(e)}'
            }
        }

def extract_video_id(youtube_url):
    """Extract video ID from various YouTube URL formats"""
    parsed_url = urlparse(youtube_url)
    
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
        elif parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
    elif parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    
    return None

def download_with_rapidapi(video_id):
    """
    Download audio using RapidAPI YouTube service with better error handling
    """
    
    url = "https://youtube-mp36.p.rapidapi.com/dl"
    
    querystring = {"id": video_id}
    
    headers = {
        "x-rapidapi-key": os.environ.get('RAPIDAPI_KEY'),
        "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"
    }
    
    try:
        print(f"Calling RapidAPI for video {video_id}")
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        print(f"RapidAPI response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"RapidAPI response: {data}")
            
            # Extract download link from response
            if data.get('status') == 'ok' and data.get('link'):
                return data['link']
            else:
                print(f"API Error: {data}")
                return None
        elif response.status_code == 429:
            print("Rate limited by RapidAPI")
            return None
        elif response.status_code == 403:
            print("RapidAPI access forbidden - check subscription")
            return None
        else:
            print(f"RapidAPI error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"RapidAPI request failed: {e}")
        return None

def upload_to_s3(audio_url, job_id):
    """Download audio from URL and upload to S3 with better error handling"""
    
    s3_client = boto3.client('s3')
    bucket_name = os.environ['BUCKET_NAME']
    
    print(f"Downloading from: {audio_url}")
    
    # Download audio file with streaming
    response = requests.get(audio_url, stream=True, timeout=120)
    response.raise_for_status()
    
    # Check content type
    content_type = response.headers.get('content-type', 'audio/mpeg')
    print(f"Content type: {content_type}")
    
    # Generate S3 key
    s3_key = f"audio/{job_id}.mp3"
    
    # Upload to S3
    print(f"Uploading to S3: s3://{bucket_name}/{s3_key}")
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=response.content,
        ContentType='audio/mpeg'
    )
    
    print(f"Successfully uploaded to S3: s3://{bucket_name}/{s3_key}")
    return s3_key