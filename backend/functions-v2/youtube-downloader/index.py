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
    """Download audio using Apify YouTube Video Downloader"""
    
    logger.info(f"Starting Apify actor for {youtube_url}")
    
    # Start Apify actor run - using epctex youtube-video-downloader
    run_response = requests.post(
        'https://api.apify.com/v2/acts/epctex~youtube-video-downloader/runs',
        json={
            'startUrls': [youtube_url],
            'maxItems': 1,
            'proxy': {
                'useApifyProxy': True
            }
        },
        params={'token': APIFY_API_TOKEN}
    )
    
    if run_response.status_code != 201:
        raise Exception(f"Failed to start Apify actor: {run_response.text}")
    
    run_data = run_response.json()
    run_id = run_data['data']['id']
    
    logger.info(f"Apify run started: {run_id}")
    
    # Wait for run to complete (poll every 3 seconds, max 3 minutes)
    max_attempts = 60
    for attempt in range(max_attempts):
        time.sleep(3)
        
        status_response = requests.get(
            f'https://api.apify.com/v2/acts/epctex~youtube-video-downloader/runs/{run_id}',
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
        raise Exception("Apify run timed out after 3 minutes")
    
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
    
    logger.info(f"Video data keys: {list(video_data.keys())}")
    
    # Extract metadata
    metadata = {
        'title': video_data.get('title', video_data.get('name', 'Unknown')),
        'duration': video_data.get('duration', video_data.get('lengthSeconds', 0)),
        'uploader': video_data.get('author', video_data.get('channelName', 'Unknown'))
    }
    
    # Get audio download URL - epctex returns downloadLinks
    download_links = video_data.get('downloadLinks', {})
    
    # Try to find audio-only format
    audio_url = None
    extension = 'webm'
    
    # Look for audio formats in order of preference
    for quality in ['audio_high', 'audio_medium', 'audio_low', 'audio']:
        if quality in download_links:
            audio_url = download_links[quality]
            break
    
    # Fallback to video formats if no audio-only
    if not audio_url:
        for quality in ['360p', '480p', '720p']:
            if quality in download_links:
                audio_url = download_links[quality]
                extension = 'mp4'
                break
    
    if not audio_url:
        # Last resort - take any download link
        if download_links:
            audio_url = list(download_links.values())[0]
            extension = 'mp4'
        else:
            raise Exception(f"No download links found. Available keys: {list(video_data.keys())}")
    
    logger.info(f"Downloading audio from: {audio_url}")
    
    # Download audio file
    audio_response = requests.get(audio_url, stream=True, timeout=300)
    
    if audio_response.status_code != 200:
        raise Exception(f"Failed to download audio: {audio_response.status_code}")
    
    # Save to temp file
    audio_path = f'/tmp/{job_id}.{extension}'
    
    with open(audio_path, 'wb') as f:
        for chunk in audio_response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    file_size = os.path.getsize(audio_path)
    logger.info(f"Audio saved to: {audio_path} ({file_size} bytes)")
    
    if file_size == 0:
        raise Exception("Downloaded file is empty")
    
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
        table = dynamodb.Table(JOBS_TABLE)
        update_expr = 'SET #status = :status, progress = :progress, updatedAt = :updated'
        expr_values = {
            ':status': status,
            ':progress': progress,
            ':updated': str(os.urandom(16).hex())
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
