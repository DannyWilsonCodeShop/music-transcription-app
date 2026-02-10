import json
import boto3
import os
import urllib.request
import urllib.parse
from urllib.parse import urlparse, parse_qs
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

AUDIO_BUCKET = os.environ['AUDIO_BUCKET']
JOBS_TABLE = os.environ['JOBS_TABLE']
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '')

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
        
        # Download audio using RapidAPI
        audio_url = download_with_rapidapi(video_id)
        
        if not audio_url:
            raise Exception('Failed to get audio URL from RapidAPI')
        
        print(f"Audio URL: {audio_url}")
        
        # Download and upload to S3
        s3_key = f"audio/{job_id}.mp3"
        file_size = download_and_upload(audio_url, s3_key)
        
        # Update job with success
        update_job(job_id, 'COMPLETE', 100, {
            's3Bucket': AUDIO_BUCKET,
            's3Key': s3_key,
            'audioUrl': audio_url,
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

def download_with_rapidapi(video_id):
    if not RAPIDAPI_KEY:
        raise Exception('RAPIDAPI_KEY not configured')
    
    url = f"https://youtube-mp36.p.rapidapi.com/dl?id={video_id}"
    
    req = urllib.request.Request(url)
    req.add_header("x-rapidapi-key", RAPIDAPI_KEY)
    req.add_header("x-rapidapi-host", "youtube-mp36.p.rapidapi.com")
    
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode())
    
    print(f"RapidAPI Response: {data}")
    
    # The response format is: {"link": "...", "status": "ok", ...}
    if data.get('status') == 'ok':
        download_url = data.get('link')
        if download_url:
            return download_url.replace('\\/', '/')
    
    raise Exception(f"RapidAPI error: {data.get('msg', 'Unknown error')}")

def download_and_upload(audio_url, s3_key):
    print(f"Downloading from: {audio_url}")
    
    req = urllib.request.Request(audio_url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    with urllib.request.urlopen(req, timeout=120) as response:
        audio_data = response.read()
    
    file_size = len(audio_data)
    print(f"Downloaded {file_size} bytes")
    
    s3.put_object(
        Bucket=AUDIO_BUCKET,
        Key=s3_key,
        Body=audio_data,
        ContentType='audio/mpeg'
    )
    
    print(f"Uploaded to s3://{AUDIO_BUCKET}/{s3_key}")
    return file_size

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
