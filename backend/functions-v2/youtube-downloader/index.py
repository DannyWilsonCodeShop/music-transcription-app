"""
Lambda: YouTube Downloader with yt-dlp
Downloads audio from YouTube using yt-dlp and uploads to S3
Extracts audio-only MP3 for Deepgram compatibility
"""

import json
import boto3
import os
import logging
import yt_dlp
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

AUDIO_BUCKET = os.environ['S3_AUDIO_BUCKET']
JOBS_TABLE = os.environ['DYNAMODB_JOBS_TABLE']

def lambda_handler(event, context):
    """Download YouTube audio using yt-dlp and upload to S3"""
    
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        job_id = event['jobId']
        youtube_url = event['youtubeUrl']
        video_id = event.get('videoId', extract_video_id(youtube_url))
        
        # Update job status
        update_job_status(job_id, 'DOWNLOADING', 10)
        
        logger.info(f"Downloading audio from {youtube_url} using yt-dlp")
        
        # Download audio using yt-dlp
        audio_path, metadata = download_with_ytdlp(youtube_url, job_id)
        
        file_size = os.path.getsize(audio_path)
        logger.info(f"Downloaded {file_size} bytes")
        
        # Determine file extension from downloaded file
        extension = audio_path.split('.')[-1]
        
        # Upload to S3
        s3_key = f'audio/{job_id}.{extension}'
        
        logger.info(f"Uploading to S3: {AUDIO_BUCKET}/{s3_key}")
        
        # Determine content type
        content_types = {
            'mp3': 'audio/mpeg',
            'm4a': 'audio/mp4',
            'webm': 'audio/webm',
            'opus': 'audio/opus',
            'ogg': 'audio/ogg'
        }
        content_type = content_types.get(extension, 'audio/mpeg')
        
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

def download_with_ytdlp(youtube_url, job_id):
    """Download audio using yt-dlp (no post-processing, direct download)"""
    
    output_template = f'/tmp/{job_id}.%(ext)s'
    
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',  # Prefer M4A or MP3
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
    }
    
    logger.info(f"yt-dlp options: {json.dumps(ydl_opts, indent=2)}")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info
            logger.info("Extracting video info...")
            info = ydl.extract_info(youtube_url, download=True)
            
            # Get metadata
            metadata = {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown')
            }
            
            logger.info(f"Video info: {metadata}")
            
            # Find the downloaded file (could be .m4a, .webm, .opus, etc.)
            downloaded_file = ydl.prepare_filename(info)
            
            if not os.path.exists(downloaded_file):
                raise Exception(f"Audio file not found at {downloaded_file}")
            
            logger.info(f"Audio downloaded to: {downloaded_file}")
            
            return downloaded_file, metadata
            
    except Exception as e:
        logger.error(f"yt-dlp error: {str(e)}")
        raise Exception(f"Failed to download audio: {str(e)}")

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
