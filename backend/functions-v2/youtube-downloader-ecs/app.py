#!/usr/bin/env python3
"""
ECS YouTube Downloader
Downloads YouTube audio using yt-dlp and uploads to S3
"""

import os
import sys
import json
import tempfile
import boto3
from pathlib import Path
import yt_dlp
from botocore.exceptions import ClientError

# Environment variables
JOB_ID = os.environ.get('JOB_ID')
YOUTUBE_URL = os.environ.get('YOUTUBE_URL')
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET')
DYNAMODB_JOBS_TABLE = os.environ.get('DYNAMODB_JOBS_TABLE')

# AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def update_job_status(job_id, status, progress, error=None, **kwargs):
    """Update job status in DynamoDB"""
    try:
        table = dynamodb.Table(DYNAMODB_JOBS_TABLE)
        update_expr = 'SET #status = :status, progress = :progress, updatedAt = :updated'
        expr_values = {
            ':status': status,
            ':progress': progress,
            ':updated': boto3.dynamodb.types.TypeSerializer().serialize(
                {'S': str(boto3.session.Session().region_name)}
            )['S']
        }
        expr_names = {'#status': 'status'}
        
        if error:
            update_expr += ', errorMessage = :error'
            expr_values[':error'] = error
            
        # Add any additional fields
        for key, value in kwargs.items():
            update_expr += f', {key} = :{key}'
            expr_values[f':{key}'] = value
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
        print(f"Updated job {job_id}: {status} ({progress}%)")
        
    except Exception as e:
        print(f"Error updating job status: {e}")

def download_youtube_audio(url, output_dir):
    """Download YouTube audio using yt-dlp"""
    print(f"Downloading audio from: {url}")
    
    # yt-dlp options for best audio quality
    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'audioquality': '192',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract info first
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'Unknown')
        duration = info.get('duration', 0)
        
        print(f"Video info - Title: {title}, Duration: {duration}s")
        
        # Download the audio
        ydl.download([url])
        
        # Find the downloaded file
        for file in Path(output_dir).glob('*'):
            if file.is_file() and file.suffix in ['.mp3', '.m4a', '.webm']:
                return str(file), title, duration
                
    raise Exception("No audio file found after download")

def upload_to_s3(local_file, bucket, key):
    """Upload file to S3"""
    try:
        print(f"Uploading {local_file} to s3://{bucket}/{key}")
        s3_client.upload_file(local_file, bucket, key)
        print(f"Upload successful: s3://{bucket}/{key}")
        return f"s3://{bucket}/{key}"
    except ClientError as e:
        raise Exception(f"S3 upload failed: {e}")

def main():
    """Main execution function"""
    print("=== YouTube Downloader ECS Task Starting ===")
    print(f"Job ID: {JOB_ID}")
    print(f"YouTube URL: {YOUTUBE_URL}")
    print(f"Output Bucket: {OUTPUT_BUCKET}")
    
    if not all([JOB_ID, YOUTUBE_URL, OUTPUT_BUCKET, DYNAMODB_JOBS_TABLE]):
        error_msg = "Missing required environment variables"
        print(f"ERROR: {error_msg}")
        if JOB_ID:
            update_job_status(JOB_ID, 'FAILED', 0, error_msg)
        sys.exit(1)
    
    try:
        # Update status: Starting download
        update_job_status(JOB_ID, 'DOWNLOADING_AUDIO', 20)
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Using temp directory: {temp_dir}")
            
            # Download YouTube audio
            audio_file, title, duration = download_youtube_audio(YOUTUBE_URL, temp_dir)
            print(f"Downloaded: {audio_file}")
            
            # Update status: Uploading
            update_job_status(JOB_ID, 'UPLOADING_AUDIO', 40)
            
            # Upload to S3
            s3_key = f"audio/{JOB_ID}/youtube_audio.mp3"
            s3_url = upload_to_s3(audio_file, OUTPUT_BUCKET, s3_key)
            
            # Update status: Complete
            update_job_status(
                JOB_ID, 
                'AUDIO_READY', 
                50,
                audioUrl=s3_url,
                videoTitle=title,
                duration=duration
            )
            
            print("=== YouTube Download Complete ===")
            print(f"Audio URL: {s3_url}")
            print(f"Title: {title}")
            print(f"Duration: {duration}s")
            
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        update_job_status(JOB_ID, 'FAILED', 0, error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()