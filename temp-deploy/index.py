import json
import boto3
import requests
import os
from urllib.parse import urlparse, parse_qs

def lambda_handler(event, context):
    """
    YouTube downloader using RapidAPI service
    More reliable than yt-dlp for production use
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
        
        # Use RapidAPI YouTube service
        audio_url = download_with_rapidapi(video_id)
        
        if not audio_url:
            return {
                'statusCode': 500,
                'body': {
                    'error': 'Failed to extract audio from YouTube video'
                }
            }
        
        # Download and upload to S3
        s3_key = upload_to_s3(audio_url, job_id)
        
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
    Download audio using RapidAPI YouTube service
    Replace with your preferred RapidAPI service
    """
    
    # Example using YouTube MP3 Downloader API
    url = "https://youtube-mp36.p.rapidapi.com/dl"
    
    querystring = {"id": video_id}
    
    headers = {
        "x-rapidapi-key": os.environ.get('RAPIDAPI_KEY'),
        "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract download link from response
        if data.get('status') == 'ok' and data.get('link'):
            return data['link']
        else:
            print(f"API Error: {data}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"RapidAPI request failed: {e}")
        return None

def upload_to_s3(audio_url, job_id):
    """Download audio from URL and upload to S3"""
    
    s3_client = boto3.client('s3')
    bucket_name = os.environ['BUCKET_NAME']
    
    # Download audio file
    response = requests.get(audio_url, stream=True, timeout=60)
    response.raise_for_status()
    
    # Generate S3 key
    s3_key = f"audio/{job_id}.mp3"
    
    # Upload to S3
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=response.content,
        ContentType='audio/mpeg'
    )
    
    print(f"Uploaded to S3: s3://{bucket_name}/{s3_key}")
    return s3_key

# Alternative implementation using different RapidAPI service
def download_with_alternative_api(video_id):
    """
    Alternative RapidAPI service - YouTube to MP3
    """
    
    url = "https://youtube-to-mp315.p.rapidapi.com/download"
    
    payload = {
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "format": "mp3",
        "quality": "128"
    }
    
    headers = {
        "content-type": "application/json",
        "x-rapidapi-key": os.environ.get('RAPIDAPI_KEY'),
        "x-rapidapi-host": "youtube-to-mp315.p.rapidapi.com"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('success') and data.get('download_url'):
            return data['download_url']
        else:
            print(f"Alternative API Error: {data}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Alternative API request failed: {e}")
        return None