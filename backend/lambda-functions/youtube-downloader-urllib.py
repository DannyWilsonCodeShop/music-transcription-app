import json
import boto3
import os
import urllib.request
import urllib.parse
import urllib.error
from urllib.parse import urlparse, parse_qs

def lambda_handler(event, context):
    """
    YouTube downloader using RapidAPI service with urllib (no external dependencies)
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
                'bucket': os.environ.get('BUCKET_NAME', 'chordscout-audio-dev'),
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
    Try multiple approaches for better reliability
    """
    
    # Try YouTube MP3 Downloader 5 API first (the one you suggested)
    try:
        return try_youtube_mp3_downloader5(video_id)
    except Exception as e:
        print(f"YouTube MP3 Downloader 5 failed: {e}")
    
    # Try YouTube MP3 Downloader API (different service)
    try:
        return try_youtube_mp3_downloader(video_id)
    except Exception as e:
        print(f"YouTube MP3 Downloader failed: {e}")
    
    # Try YouTube Video Downloader API
    try:
        return try_youtube_video_downloader(video_id)
    except Exception as e:
        print(f"YouTube Video Downloader failed: {e}")
    
    # Try YouTube to MP3 Converter API
    try:
        return try_youtube_to_mp3_converter(video_id)
    except Exception as e:
        print(f"YouTube to MP3 Converter failed: {e}")
    
    return None

def try_youtube_mp3_downloader5(video_id):
    """Try YouTube MP3 Audio Video Downloader API - the working one!"""
    url = f"https://youtube-mp3-audio-video-downloader.p.rapidapi.com/get_m4a_download_link/{video_id}"
    
    print(f"Making request to: {url}")
    print(f"Using API key: {os.environ.get('RAPIDAPI_KEY')[:10]}...")
    
    req = urllib.request.Request(url)
    req.add_header("x-rapidapi-key", os.environ.get('RAPIDAPI_KEY'))
    req.add_header("x-rapidapi-host", "youtube-mp3-audio-video-downloader.p.rapidapi.com")
    req.add_header("User-Agent", "Mozilla/5.0 (compatible; ChordScout/1.0)")
    
    print(f"Request headers: {dict(req.headers)}")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            print(f"Response status: {response.status}")
            print(f"Response headers: {dict(response.headers)}")
            data = json.loads(response.read().decode())
        
        print(f"YouTube MP3 Audio Video Downloader API Response: {data}")
        
        # Check for the download URL - try main file first, then reserved file
        download_url = data.get('file') or data.get('reserved_file')
        
        if download_url:
            # Clean up the URL (remove escape characters)
            download_url = download_url.replace('\\/', '/')
            print(f"Found download URL: {download_url}")
            return download_url
        else:
            print("No download URL found in response")
        
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print(f"Response body: {e.read().decode() if hasattr(e, 'read') else 'No body'}")
        raise
    except Exception as e:
        print(f"Other error: {e}")
        raise
    
    return None

def try_youtube_mp3_downloader(video_id):
    """Try YouTube MP3 Downloader API"""
    base_url = "https://youtube-mp36.p.rapidapi.com/dl"
    params = urllib.parse.urlencode({"id": video_id})
    url = f"{base_url}?{params}"
    
    req = urllib.request.Request(url)
    req.add_header("x-rapidapi-key", os.environ.get('RAPIDAPI_KEY'))
    req.add_header("x-rapidapi-host", "youtube-mp36.p.rapidapi.com")
    
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode())
    
    print(f"YouTube MP3 API Response: {data}")
    
    if data.get('status') == 'ok' and data.get('link'):
        return data['link']
    
    return None

def try_youtube_video_downloader(video_id):
    """Try YouTube Video Downloader API"""
    base_url = "https://youtube-video-downloader-info.p.rapidapi.com/youtube"
    params = urllib.parse.urlencode({"url": f"https://www.youtube.com/watch?v={video_id}"})
    url = f"{base_url}?{params}"
    
    req = urllib.request.Request(url)
    req.add_header("x-rapidapi-key", os.environ.get('RAPIDAPI_KEY'))
    req.add_header("x-rapidapi-host", "youtube-video-downloader-info.p.rapidapi.com")
    
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode())
    
    print(f"YouTube Video Downloader API Response: {data}")
    
    # Look for audio formats
    if data.get('formats'):
        for fmt in data['formats']:
            if fmt.get('mimeType', '').startswith('audio/') and fmt.get('url'):
                return fmt['url']
    
    return None

def try_youtube_to_mp3_converter(video_id):
    """Try YouTube to MP3 Converter API"""
    base_url = "https://youtube-to-mp315.p.rapidapi.com/download"
    
    payload = json.dumps({
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "format": "mp3",
        "quality": "128"
    }).encode('utf-8')
    
    req = urllib.request.Request(base_url, data=payload, method='POST')
    req.add_header("content-type", "application/json")
    req.add_header("x-rapidapi-key", os.environ.get('RAPIDAPI_KEY'))
    req.add_header("x-rapidapi-host", "youtube-to-mp315.p.rapidapi.com")
    
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode())
    
    print(f"YouTube to MP3 Converter API Response: {data}")
    
    if data.get('success') and data.get('download_url'):
        return data['download_url']
    
    return None

def upload_to_s3(audio_url, job_id):
    """Download audio from URL and upload to S3"""
    
    s3_client = boto3.client('s3')
    bucket_name = os.environ.get('BUCKET_NAME', 'chordscout-audio-dev')
    
    # Download audio file
    try:
        with urllib.request.urlopen(audio_url, timeout=60) as response:
            audio_data = response.read()
    except urllib.error.URLError as e:
        print(f"Failed to download audio: {e}")
        raise
    
    # Determine file extension and content type from URL
    if '.m4a' in audio_url.lower():
        file_extension = 'm4a'
        content_type = 'audio/mp4'
    elif '.mp3' in audio_url.lower():
        file_extension = 'mp3'
        content_type = 'audio/mpeg'
    else:
        # Default to m4a since that's what our API returns
        file_extension = 'm4a'
        content_type = 'audio/mp4'
    
    # Generate S3 key with correct extension
    s3_key = f"audio/{job_id}.{file_extension}"
    
    # Upload to S3
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=audio_data,
        ContentType=content_type
    )
    
    print(f"Uploaded to S3: s3://{bucket_name}/{s3_key}")
    return s3_key