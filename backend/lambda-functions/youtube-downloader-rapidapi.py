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
        
        # Try RapidAPI first, fallback to urllib method
        audio_url = download_with_rapidapi(video_id)
        
        if not audio_url:
            print("RapidAPI failed, trying urllib fallback...")
            audio_url = download_with_urllib_fallback(video_id)
        
        if not audio_url:
            return {
                'statusCode': 500,
                'body': {
                    'error': 'Failed to extract audio from YouTube video using both RapidAPI and fallback methods'
                }
            }
        
        # Download and upload to S3 (handle both HTTP URLs and S3 paths)
        if audio_url.startswith('s3://'):
            # Already uploaded by fallback method
            s3_key = audio_url.split('/', 3)[3]  # Extract key from s3://bucket/key
        else:
            # Try to download from HTTP URL and upload
            try:
                s3_key = upload_to_s3(audio_url, job_id)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"RapidAPI download link failed (404), trying fallback method...")
                    audio_url = download_with_urllib_fallback(video_id)
                    if audio_url and audio_url.startswith('s3://'):
                        s3_key = audio_url.split('/', 3)[3]  # Extract key from s3://bucket/key
                    else:
                        raise Exception("Both RapidAPI and fallback methods failed")
                else:
                    raise e
        
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

def download_with_urllib_fallback(video_id):
    """
    Fallback method using urllib and cookies when RapidAPI fails
    """
    import subprocess
    import tempfile
    import os
    
    try:
        # Use yt-dlp with cookies if available
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Check if cookies file exists in Lambda environment
        cookies_path = "/tmp/cookies.txt"
        
        # Copy cookies file from deployment package to /tmp if it exists
        if os.path.exists("cookies.txt"):
            import shutil
            shutil.copy("cookies.txt", cookies_path)
            print("Cookies file copied to /tmp")
        
        # Create temp directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "audio.%(ext)s")
            
            # Build yt-dlp command
            cmd = [
                "yt-dlp",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "128K",
                "--output", output_path,
                youtube_url
            ]
            
            # Add cookies if available
            if os.path.exists(cookies_path):
                cmd.extend(["--cookies", cookies_path])
            
            # Run yt-dlp
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Find the downloaded file
                for file in os.listdir(temp_dir):
                    if file.startswith("audio."):
                        file_path = os.path.join(temp_dir, file)
                        
                        # Upload directly to S3 from file
                        s3_client = boto3.client('s3')
                        bucket_name = os.environ['BUCKET_NAME']
                        s3_key = f"audio/{video_id}.mp3"
                        
                        with open(file_path, 'rb') as f:
                            s3_client.put_object(
                                Bucket=bucket_name,
                                Key=s3_key,
                                Body=f.read(),
                                ContentType='audio/mpeg'
                            )
                        
                        print(f"Fallback method: Uploaded to S3: s3://{bucket_name}/{s3_key}")
                        return f"s3://{bucket_name}/{s3_key}"  # Return S3 path instead of HTTP URL
            
            print(f"yt-dlp failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"Fallback method failed: {e}")
        return None