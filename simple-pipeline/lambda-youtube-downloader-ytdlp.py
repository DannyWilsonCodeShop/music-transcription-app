import json
import boto3
import os
import subprocess
import tempfile
from datetime import datetime
from urllib.parse import urlparse, parse_qs

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

AUDIO_BUCKET = os.environ['AUDIO_BUCKET']
JOBS_TABLE = os.environ['JOBS_TABLE']

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    
    # Parse body from API Gateway v2 format
    if 'body' in event:
        if isinstance(event['body'], str):
            body = json.loads(event['body'])
        else:
            body = event['body']
    else:
        body = event
    
    # Extract parameters
    youtube_url = body.get('youtubeUrl')
    job_id = body.get('jobId')
    
    if not youtube_url or not job_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Missing youtubeUrl or jobId'})
        }
    
    try:
        # Update job status
        update_job(job_id, 'DOWNLOADING', 10)
        
        # Extract video ID
        video_id = extract_video_id(youtube_url)
        if not video_id:
            raise Exception('Invalid YouTube URL')
        
        print(f"Video ID: {video_id}")
        
        # Download audio using yt-dlp
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, f"{job_id}.mp3")
            
            # Use yt-dlp to download audio
            cmd = [
                'yt-dlp',
                '-f', 'bestaudio',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '0',  # Best quality
                '-o', output_file,
                youtube_url
            ]
            
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
            
            if result.returncode != 0:
                print(f"yt-dlp stderr: {result.stderr}")
                raise Exception(f"yt-dlp failed: {result.stderr}")
            
            print(f"yt-dlp stdout: {result.stdout}")
            
            # Check if file exists
            if not os.path.exists(output_file):
                raise Exception(f"Audio file not created: {output_file}")
            
            # Get file size
            file_size = os.path.getsize(output_file)
            print(f"Downloaded {file_size} bytes")
            
            # Upload to S3
            s3_key = f"audio/{job_id}.mp3"
            with open(output_file, 'rb') as f:
                s3.put_object(
                    Bucket=AUDIO_BUCKET,
                    Key=s3_key,
                    Body=f,
                    ContentType='audio/mpeg'
                )
            
            print(f"Uploaded to s3://{AUDIO_BUCKET}/{s3_key}")
        
        # Update job with success
        update_job(job_id, 'COMPLETE', 100, {
            's3Bucket': AUDIO_BUCKET,
            's3Key': s3_key,
            'fileSize': file_size,
            'videoId': video_id
        })
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'jobId': job_id,
                'status': 'COMPLETE',
                's3Bucket': AUDIO_BUCKET,
                's3Key': s3_key,
                'fileSize': file_size
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        update_job(job_id, 'FAILED', 0, {'error': str(e)})
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def extract_video_id(youtube_url):
    parsed = urlparse(youtube_url)
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
    elif parsed.hostname == 'youtu.be':
        return parsed.path[1:]
    return None

def update_job(job_id, status, progress, extra_data=None):
    table = dynamodb.Table(JOBS_TABLE)
    
    item = {
        'jobId': job_id,
        'status': status,
        'progress': progress,
        'updatedAt': datetime.utcnow().isoformat()
    }
    
    if extra_data:
        item.update(extra_data)
    
    table.put_item(Item=item)
    print(f"Updated job {job_id}: {status} ({progress}%)")
