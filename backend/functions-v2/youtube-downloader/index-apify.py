"""
Lambda: YouTube Downloader with Apify
Downloads audio from YouTube using Apify YouTube Scraper and uploads to S3
"""

import json
import boto3
import os
import logging
import requests
import time
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

AUDIO_BUCKET = os.environ['S3_AUDIO_BUCKET']
JOBS_TABLE = os.environ['DYNAMODB_JOBS_TABLE']
APIFY_API_TOKEN = os.environ['APIFY_API_TOKEN']

def lambda_handler(event, context):
    """Download YouTube audio using Apify and upload to S3"""
    
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        job_id = event['jobId']
        youtube_url = event['youtubeUrl']
        video_id = event.get('videoId', extract_video_id(youtube_url))
        
        # Update job status
        update_job_status(job_id, 'DOWNLOADING', 10)
        
        logger.info(f"Downloading audio from {youtube_url} using Apify")
        
        # Use Apify to get video info and download URL
        audio_path, metadata = download_with_apify(youtube_url, job_id)
        
        file_size = os.path.getsize(audio_path)
        logger.info(f"Downloaded {file_size} bytes")
        
        # Determine file extension
        extension = audio_path.split('.')[-1]
        
        # Upload to S3
        s3_key = f'audio/{job_id}.{extension}'
        
        logger.info(f"Uploading to S3: {AUDIO_BUCKET}/{s3_key}")
        
        # Determine content type
        content_type = 'audio/webm' if extension == 'webm' else f'audio/{extension}'
        
        s3_client.upload_file(
            audio_path,
            AUDIO_BUCKET,
            s3_key,
            ExtraArgs={'ContentType': content_type}
        )
        
        video_title = metadata.get('title', f'Video {video_id}')
        duration = metadata.get('duration', 0)
        
        # Update job with audio info
        table = dynamodb.Table(JOBS_TABLE)
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET audioS3Key = :key, videoTitle = :title, #duration = :duration, #status = :status, progress = :progress, updatedAt = :updated',
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
                'fileSize': file_size
            }
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        update_job_status(job_id, 'FAILED', 0, str(e))
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }

def download_with_apify(youtube_url, job_id):
    """Download audio using Apify YouTube Scraper"""
    
    logger.info(f"Starting Apify actor for {youtube_url}")
    
    # Start Apify actor run
    run_response = requests.post(
        'https://api.apify.com/v2/acts/streamers~youtube-scraper/runs',
        json={
            'startUrls': [{'url': youtube_url}],
            'maxResults': 1,
            'downloadSubtitles': False,
            'downloadThumbnails': False,
        },
        params={'token': APIFY_API_TOKEN}
    )
    
    if run_response.status_code != 201:
        raise Exception(f"Failed to start Apify actor: {run_response.text}")
    
    run_data = run_response.json()
    run_id = run_data['data']['id']
    
    logger.info(f"Apify run started: {run_id}")
    
    # Wait for run to complete (poll every 2 seconds, max 2 minutes)
    max_attempts = 60
    for attempt in range(max_attempts):
        time.sleep(2)
        
        status_response = requests.get(
            f'https://api.apify.com/v2/acts/streamers~youtube-scraper/runs/{run_id}',
            params={'token': APIFY_API_TOKEN}
        )
        
        if status_response.status_code != 200:
            raise Exception(f"Failed to get run status: {status_response.text}")
        
        status_data = status_response.json()
        status = status_data['data']['status']
        
        logger.info(f"Apify run status: {status} (attempt {attempt + 1}/{max_attempts})")
        
        if status == 'SUCCEEDED':
            break
        elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
            raise Exception(f"Apify run failed with status: {status}")
    else:
        raise Exception("Apify run timed out after 2 minutes")
    
    # Get dataset items (video info)
    dataset_id = status_data['data']['defaultDatasetId']
    dataset_response = requests.get(
        f'https://api.apify.com/v2/datasets/{dataset_id}/items',
        params={'token': APIFY_API_TOKEN}
    )
    
    if dataset_response.status_code != 200:
        raise Exception(f"Failed to get dataset: {dataset_response.text}")
    
    items = dataset_response.json()
    
    if not items or len(items) == 0:
        raise Exception("No video data returned from Apify")
    
    video_data = items[0]
    
    logger.info(f"Video data: {json.dumps(video_data, indent=2)}")
    
    # Extract metadata
    metadata = {
        'title': video_data.get('title', 'Unknown'),
        'duration': video_data.get('duration', 0),
        'uploader': video_data.get('channelName', 'Unknown')
    }
    
    # Get audio download URL
    # Apify returns various formats, prefer audio-only
    formats = video_data.get('formats', [])
    
    # Find best audio format
    audio_format = None
    for fmt in formats:
        if fmt.get('mimeType', '').startswith('audio/'):
            audio_format = fmt
            break
    
    if not audio_format:
        # Fallback to any format with audio
        for fmt in formats:
            if 'audio' in fmt.get('mimeType', '').lower():
                audio_format = fmt
                break
    
    if not audio_format:
        raise Exception("No audio format found in video data")
    
    download_url = audio_format.get('url')
    if not download_url:
        raise Exception("No download URL found in audio format")
    
    logger.info(f"Downloading audio from: {download_url}")
    
    # Download audio file
    audio_response = requests.get(download_url, stream=True)
    
    if audio_response.status_code != 200:
        raise Exception(f"Failed to download audio: {audio_response.status_code}")
    
    # Determine file extension from mime type
    mime_type = audio_format.get('mimeType', 'audio/webm')
    extension = 'webm'
    if 'mp4' in mime_type or 'm4a' in mime_type:
        extension = 'm4a'
    elif 'mpeg' in mime_type or 'mp3' in mime_type:
        extension = 'mp3'
    elif 'ogg' in mime_type:
        extension = 'ogg'
    
    # Save to temp file
    audio_path = f'/tmp/{job_id}.{extension}'
    
    with open(audio_path, 'wb') as f:
        for chunk in audio_response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    logger.info(f"Audio saved to: {audio_path}")
    
    return audio_path, metadata

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
        from datetime import datetime
        table = dynamodb.Table(JOBS_TABLE)
        update_expr = 'SET #status = :status, progress = :progress, updatedAt = :updated'
        expr_values = {
            ':status': status,
            ':progress': progress,
            ':updated': datetime.utcnow().isoformat() + 'Z'
        }
        
        if error:
            update_expr += ', errorMessage = :error'
            expr_values[':error'] = str(error)[:500]  # Limit error message length
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues=expr_values
        )
    except Exception as e:
        logger.error(f"Failed to update job status: {str(e)}")
