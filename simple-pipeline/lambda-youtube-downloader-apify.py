import json
import boto3
import os
import urllib.request
import urllib.parse
import time
from urllib.parse import urlparse, parse_qs
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

AUDIO_BUCKET = os.environ['AUDIO_BUCKET']
JOBS_TABLE = os.environ['JOBS_TABLE']
APIFY_API_TOKEN = os.environ.get('APIFY_API_TOKEN', '')

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
        
        # Download audio using Apify
        audio_url = download_with_apify(youtube_url)
        
        if not audio_url:
            raise Exception('Failed to get audio URL from Apify')
        
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

def download_with_apify(youtube_url):
    if not APIFY_API_TOKEN:
        raise Exception('APIFY_API_TOKEN not configured')
    
    # Start Apify actor
    actor_id = 'streamers/youtube-scraper'
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_API_TOKEN}"
    
    payload = json.dumps({
        "startUrls": [{"url": youtube_url}],
        "maxResults": 1,
        "downloadAudio": True
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload, method='POST')
    req.add_header('Content-Type', 'application/json')
    
    with urllib.request.urlopen(req, timeout=30) as response:
        run_data = json.loads(response.read().decode())
    
    run_id = run_data['data']['id']
    print(f"Apify run started: {run_id}")
    
    # Wait for completion (max 2 minutes)
    for i in range(24):  # 24 * 5 = 120 seconds
        time.sleep(5)
        
        status_url = f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}?token={APIFY_API_TOKEN}"
        req = urllib.request.Request(status_url)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            status_data = json.loads(response.read().decode())
        
        status = status_data['data']['status']
        print(f"Apify status: {status}")
        
        if status == 'SUCCEEDED':
            # Get dataset
            dataset_id = status_data['data']['defaultDatasetId']
            dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}"
            
            req = urllib.request.Request(dataset_url)
            with urllib.request.urlopen(req, timeout=10) as response:
                items = json.loads(response.read().decode())
            
            if items and len(items) > 0:
                # Look for audio URL in the result
                item = items[0]
                audio_url = item.get('audioUrl') or item.get('url')
                if audio_url:
                    return audio_url
            
            raise Exception('No audio URL found in Apify results')
        
        elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
            raise Exception(f'Apify run {status}')
    
    raise Exception('Apify run timed out')

def download_and_upload(audio_url, s3_key):
    print(f"Downloading from: {audio_url}")
    
    req = urllib.request.Request(audio_url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
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
