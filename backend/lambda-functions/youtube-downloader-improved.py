"""
Improved YouTube Downloader Lambda Function
Combines RapidAPI with robust fallback mechanisms
"""

import json
import boto3
import os
import logging
import requests
import subprocess
import time
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

AUDIO_BUCKET = os.environ['S3_AUDIO_BUCKET']
JOBS_TABLE = os.environ['DYNAMODB_JOBS_TABLE']
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')

def lambda_handler(event, context):
    """Download YouTube audio with multiple fallback methods"""
    
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        job_id = event['jobId']
        youtube_url = event['youtubeUrl']
        video_id = event.get('videoId', extract_video_id(youtube_url))
        
        # Update job status
        update_job_status(job_id, 'DOWNLOADING', 10)
        
        logger.info(f"Downloading audio from {youtube_url}")
        
        # Try multiple methods in order of preference
        methods = [
            ('RapidAPI', download_with_rapidapi),
            ('yt-dlp', download_with_ytdlp),
            ('fallback', download_with_fallback)
        ]
        
        audio_path = None
        metadata = {}
        method_used = None
        
        for method_name, method_func in methods:
            try:
                logger.info(f"Trying method: {method_name}")
                audio_path, metadata = method_func(youtube_url, job_id)
                
                if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                    method_used = method_name
                    logger.info(f"✅ Success with {method_name}")
                    break
                else:
                    logger.warning(f"❌ {method_name} returned empty result")
                    
            except Exception as e:
                logger.warning(f"❌ {method_name} failed: {str(e)}")
                continue
        
        if not audio_path or not os.path.exists(audio_path):
            raise Exception("All download methods failed")
        
        file_size = os.path.getsize(audio_path)
        logger.info(f"Downloaded {file_size} bytes using {method_used}")
        
        # Determine file extension
        extension = audio_path.split('.')[-1]
        
        # Upload to S3
        s3_key = f'audio/{job_id}.{extension}'
        
        logger.info(f"Uploading to S3: {AUDIO_BUCKET}/{s3_key}")
        
        content_type = 'audio/webm' if extension == 'webm' else f'audio/{extension}'
        
        s3_client.upload_file(
            audio_path,
            AUDIO_BUCKET,
            s3_key,
            ExtraArgs={'ContentType': content_type}
        )
        
        video_title = metadata.get('title', f'Video {video_id}')
        duration = metadata.get('duration', 0)
        
        # Update job with success
        table = dynamodb.Table(JOBS_TABLE)
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET audioS3Key = :key, videoTitle = :title, #duration = :duration, #status = :status, progress = :progress, downloadMethod = :method, updatedAt = :updated',
            ExpressionAttributeNames={
                '#status': 'status',
                '#duration': 'duration'
            },
            ExpressionAttributeValues={
                ':key': s3_key,
                ':title': video_title,
                ':duration': duration,
                ':status': 'DOWNLOADED',
                ':progress': 25,
                ':method': method_used,
                ':updated': context.aws_request_id
            }
        )
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return {
            'statusCode': 200,
            'body': {
                'jobId': job_id,
                'bucket': AUDIO_BUCKET,
                'key': s3_key,
                'videoTitle': video_title,
                'duration': duration,
                'fileSize': file_size,
                'method': method_used
            }
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        update_job_status(job_id, 'FAILED', 0, str(e))
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }

def download_with_rapidapi(youtube_url, job_id):
    """Download using RapidAPI with improved error handling"""
    
    if not RAPIDAPI_KEY:
        raise Exception("RapidAPI key not configured")
    
    video_id = extract_video_id(youtube_url)
    
    # Make API request
    response = requests.get(
        "https://youtube-mp36.p.rapidapi.com/dl",
        params={"id": video_id},
        headers={
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"
        },
        timeout=30
    )
    
    if response.status_code != 200:
        raise Exception(f"RapidAPI request failed: {response.status_code}")
    
    data = response.json()
    
    if data.get('status') != 'ok':
        raise Exception(f"RapidAPI error: {data.get('msg', 'Unknown error')}")
    
    download_url = data.get('link')
    if not download_url:
        raise Exception("No download link in RapidAPI response")
    
    # Test download link with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Test with HEAD request first
            head_response = requests.head(download_url, timeout=10)
            
            if head_response.status_code == 200:
                # Download the file
                download_response = requests.get(download_url, timeout=120, stream=True)
                
                if download_response.status_code == 200:
                    audio_path = f'/tmp/{job_id}.mp3'
                    
                    with open(audio_path, 'wb') as f:
                        for chunk in download_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Verify file size
                    if os.path.getsize(audio_path) > 1000:  # At least 1KB
                        metadata = {
                            'title': data.get('title', 'Unknown'),
                            'duration': data.get('duration', 0)
                        }
                        return audio_path, metadata
                    else:
                        raise Exception("Downloaded file is too small")
                else:
                    raise Exception(f"Download failed: {download_response.status_code}")
            else:
                raise Exception(f"Download link test failed: {head_response.status_code}")
                
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"RapidAPI attempt {attempt + 1} failed: {str(e)}, retrying...")
                time.sleep(2)
            else:
                raise e

def download_with_ytdlp(youtube_url, job_id):
    """Download using yt-dlp as fallback"""
    
    audio_path = f'/tmp/{job_id}.%(ext)s'
    
    # yt-dlp command
    cmd = [
        'yt-dlp',
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', '0',
        '--output', audio_path,
        '--no-playlist',
        '--cookies', '/tmp/cookies.txt',  # If cookies are available
        youtube_url
    ]
    
    # Remove cookies option if file doesn't exist
    if not os.path.exists('/tmp/cookies.txt'):
        cmd = [c for c in cmd if c != '--cookies' and c != '/tmp/cookies.txt']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"yt-dlp failed: {result.stderr}")
        
        # Find the actual output file
        import glob
        possible_files = glob.glob(f'/tmp/{job_id}.*')
        
        if not possible_files:
            raise Exception("yt-dlp output file not found")
        
        actual_path = possible_files[0]
        
        # Get metadata from yt-dlp output
        metadata = {'title': 'Unknown', 'duration': 0}
        
        # Try to extract title from yt-dlp output
        if '[download]' in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Destination:' in line:
                    # Extract title from filename
                    filename = line.split('Destination:')[-1].strip()
                    metadata['title'] = os.path.basename(filename).split('.')[0]
                    break
        
        return actual_path, metadata
        
    except subprocess.TimeoutExpired:
        raise Exception("yt-dlp timed out after 5 minutes")

def download_with_fallback(youtube_url, job_id):
    """Last resort fallback method"""
    
    # This could implement other methods like:
    # - Different YouTube APIs
    # - Alternative scraping methods
    # - Mock data for testing
    
    raise Exception("No fallback method implemented")

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    parsed = urlparse(url)
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed.path == '/watch':
            return parse_qs(parsed.query)['v'][0]
    elif parsed.hostname in ['youtu.be']:
        return parsed.path[1:]
    return None

def update_job_status(job_id, status, progress, error=None):
    """Update job status in DynamoDB"""
    try:
        table = dynamodb.Table(JOBS_TABLE)
        update_expr = 'SET #status = :status, progress = :progress, updatedAt = :updated'
        expr_values = {
            ':status': status,
            ':progress': progress,
            ':updated': str(os.urandom(16).hex())
        }
        
        if error:
            update_expr += ', errorMessage = :error'
            expr_values[':error'] = str(error)[:500]
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues=expr_values
        )
    except Exception as e:
        logger.error(f"Failed to update job status: {str(e)}")