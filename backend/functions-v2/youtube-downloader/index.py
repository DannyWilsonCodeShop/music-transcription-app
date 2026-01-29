"""
Lambda: YouTube Downloader using RapidAPI
Downloads audio from YouTube using a paid RapidAPI service
"""

import json
import boto3
import os
import logging
import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

AUDIO_BUCKET = os.environ['S3_AUDIO_BUCKET']
JOBS_TABLE = os.environ['DYNAMODB_JOBS_TABLE']
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '')

def lambda_handler(event, context):
    """Download YouTube audio using RapidAPI service"""
    
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        job_id = event['jobId']
        youtube_url = event['youtubeUrl']
        video_id = event.get('videoId', extract_video_id(youtube_url))
        
        if not RAPIDAPI_KEY:
            raise Exception("RAPIDAPI_KEY environment variable not set")
        
        # Update job status
        update_job_status(job_id, 'DOWNLOADING', 10)
        
        logger.info(f"Downloading audio from {youtube_url} using RapidAPI")
        
        # Download audio using RapidAPI
        audio_url, metadata = download_with_rapidapi(video_id, youtube_url)
        
        logger.info(f"Got audio URL: {audio_url}")
        
        # Download the audio file
        logger.info("Downloading audio file...")
        audio_response = requests.get(audio_url, stream=True, timeout=300, allow_redirects=True)
        
        # Check if we got a 404 - this means the link needs whitelisting
        if audio_response.status_code == 404:
            logger.warning("Got 404 - link may need whitelisting. Trying with different headers...")
            # Try with referer header
            audio_response = requests.get(
                audio_url, 
                stream=True, 
                timeout=300,
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://ytjar.info/'
                }
            )
        
        audio_response.raise_for_status()
        
        # Save to temp file
        temp_path = f'/tmp/{job_id}.mp3'
        with open(temp_path, 'wb') as f:
            for chunk in audio_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(temp_path)
        logger.info(f"Downloaded {file_size} bytes")
        
        # Upload to S3
        s3_key = f'audio/{job_id}.mp3'
        
        logger.info(f"Uploading to S3: {AUDIO_BUCKET}/{s3_key}")
        
        with open(temp_path, 'rb') as f:
            s3_client.put_object(
                Bucket=AUDIO_BUCKET,
                Key=s3_key,
                Body=f,
                ContentType='audio/mpeg'
            )
        
        logger.info("Upload complete")
        
        # Clean up temp file
        os.remove(temp_path)
        
        # Update job with download info
        update_job_status(job_id, 'DOWNLOADED', 20)
        
        return {
            'statusCode': 200,
            'body': {
                'jobId': job_id,
                's3Key': s3_key,
                'videoTitle': metadata.get('title', 'Unknown'),
                'duration': metadata.get('duration', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        update_job_status(job_id, 'FAILED', 0, str(e))
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }

def download_with_rapidapi(video_id, youtube_url):
    """
    Download audio using RapidAPI YouTube MP3 service
    Using: https://rapidapi.com/ytjar/api/youtube-mp36
    """
    
    # API endpoint
    url = "https://youtube-mp36.p.rapidapi.com/dl"
    
    querystring = {"id": video_id}
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"
    }
    
    max_retries = 10
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"RapidAPI request attempt {attempt + 1}/{max_retries}")
            
            response = requests.get(url, headers=headers, params=querystring, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"RapidAPI response: {json.dumps(data)}")
            
            status = data.get('status')
            
            if status == 'ok':
                # Success - got the MP3 link
                audio_url = data.get('link')
                if not audio_url:
                    raise Exception("No audio link in response")
                
                # Extract metadata
                metadata = {
                    'title': data.get('title', 'Unknown'),
                    'duration': 0  # RapidAPI doesn't provide duration
                }
                
                return audio_url, metadata
                
            elif status == 'processing':
                # Still processing - wait and retry
                logger.info(f"Video still processing, waiting {retry_delay}s...")
                time.sleep(retry_delay)
                continue
                
            elif status == 'fail':
                # Failed
                error_msg = data.get('msg', 'Unknown error')
                raise Exception(f"RapidAPI conversion failed: {error_msg}")
            
            else:
                raise Exception(f"Unknown status: {status}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise Exception(f"Failed to download after {max_retries} attempts: {str(e)}")
    
    raise Exception(f"Video processing timeout after {max_retries} attempts")

def extract_video_id(youtube_url):
    """Extract video ID from YouTube URL"""
    parsed = urlparse(youtube_url)
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        query = parse_qs(parsed.query)
        return query.get('v', [None])[0]
    elif parsed.hostname == 'youtu.be':
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
            ':updated': datetime.utcnow().isoformat() + 'Z'
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
