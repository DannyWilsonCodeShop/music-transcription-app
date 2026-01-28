"""
Lambda: YouTube Downloader - Phase 1 Implementation
Uses RapidAPI as primary method with robust fallback mechanisms
Based on NEW_ARCHITECTURE.md Phase 1 recommendations
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
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')
APIFY_API_TOKEN = os.environ.get('APIFY_API_TOKEN')

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
        
        # Try multiple methods in order of preference (Phase 1 strategy)
        methods = [
            ('RapidAPI', download_with_rapidapi),
            ('Apify_Free', download_with_apify_free),
            ('Direct_Extraction', download_with_direct_method)
        ]
        
        audio_path = None
        metadata = {}
        method_used = None
        last_error = None
        
        for method_name, method_func in methods:
            try:
                logger.info(f"🔄 Trying method: {method_name}")
                audio_path, metadata = method_func(youtube_url, job_id)
                
                if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:  # At least 1KB
                    method_used = method_name
                    logger.info(f"✅ Success with {method_name}")
                    break
                else:
                    logger.warning(f"❌ {method_name} returned empty/invalid result")
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"❌ {method_name} failed: {last_error}")
                continue
        
        if not audio_path or not os.path.exists(audio_path):
            raise Exception(f"All download methods failed. Last error: {last_error}")
        
        file_size = os.path.getsize(audio_path)
        logger.info(f"📁 Downloaded {file_size} bytes using {method_used}")
        
        # Determine file extension
        extension = audio_path.split('.')[-1] if '.' in audio_path else 'mp3'
        
        # Upload to S3
        s3_key = f'audio/{job_id}.{extension}'
        
        logger.info(f"☁️ Uploading to S3: {AUDIO_BUCKET}/{s3_key}")
        
        content_type = get_content_type(extension)
        
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
        logger.error(f"💥 Error: {str(e)}", exc_info=True)
        update_job_status(job_id, 'FAILED', 0, str(e))
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }

def download_with_rapidapi(youtube_url, job_id):
    """Primary method: RapidAPI YouTube MP3 (Phase 1 recommended)"""
    
    if not RAPIDAPI_KEY:
        raise Exception("RapidAPI key not configured")
    
    video_id = extract_video_id(youtube_url)
    logger.info(f"🔑 Using RapidAPI for video: {video_id}")
    
    # Make API request with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(
                "https://youtube-mp36.p.rapidapi.com/dl",
                params={"id": video_id},
                headers={
                    "x-rapidapi-key": RAPIDAPI_KEY,
                    "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'ok':
                    download_url = data.get('link')
                    if not download_url:
                        raise Exception("No download link in RapidAPI response")
                    
                    # Test and download the file
                    return download_audio_file(download_url, job_id, 'mp3', {
                        'title': data.get('title', 'Unknown'),
                        'duration': data.get('duration', 0)
                    })
                else:
                    raise Exception(f"RapidAPI error: {data.get('msg', 'Unknown error')}")
            else:
                raise Exception(f"RapidAPI request failed: {response.status_code}")
                
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"RapidAPI attempt {attempt + 1} failed: {str(e)}, retrying...")
                time.sleep(2)
            else:
                raise e

def download_with_apify_free(youtube_url, job_id):
    """Fallback method: Try free Apify actors"""
    
    if not APIFY_API_TOKEN:
        raise Exception("Apify token not configured")
    
    # Try different free actors
    free_actors = [
        'streamers~youtube-scraper',
        'apidojo~youtube-scraper',
        'streamers~youtube-video-downloader'
    ]
    
    for actor in free_actors:
        try:
            logger.info(f"🕷️ Trying Apify actor: {actor}")
            
            # Start actor run
            run_response = requests.post(
                f'https://api.apify.com/v2/acts/{actor}/runs',
                json={
                    'startUrls': [{'url': youtube_url}],
                    'maxItems': 1
                },
                params={'token': APIFY_API_TOKEN},
                timeout=10
            )
            
            if run_response.status_code == 201:
                run_data = run_response.json()
                run_id = run_data['data']['id']
                
                # Wait for completion (shorter timeout for fallback)
                for attempt in range(20):  # 1 minute max
                    time.sleep(3)
                    
                    status_response = requests.get(
                        f'https://api.apify.com/v2/acts/{actor}/runs/{run_id}',
                        params={'token': APIFY_API_TOKEN}
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data['data']['status']
                        
                        if status == 'SUCCEEDED':
                            # Try to extract download info
                            dataset_id = status_data['data']['defaultDatasetId']
                            dataset_response = requests.get(
                                f'https://api.apify.com/v2/datasets/{dataset_id}/items',
                                params={'token': APIFY_API_TOKEN}
                            )
                            
                            if dataset_response.status_code == 200:
                                items = dataset_response.json()
                                if items and len(items) > 0:
                                    # This would need to be customized per actor
                                    # For now, just return basic info
                                    video_data = items[0]
                                    logger.info(f"Got data from {actor}: {list(video_data.keys())}")
                                    
                                    # Most free actors don't provide direct download links
                                    # They provide metadata only
                                    raise Exception(f"Actor {actor} doesn't provide download links")
                        elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                            raise Exception(f"Actor {actor} failed with status: {status}")
                    
                raise Exception(f"Actor {actor} timed out")
            else:
                raise Exception(f"Failed to start actor {actor}: {run_response.status_code}")
                
        except Exception as e:
            logger.warning(f"Actor {actor} failed: {str(e)}")
            continue
    
    raise Exception("All free Apify actors failed")

def download_with_direct_method(youtube_url, job_id):
    """Last resort: Direct extraction method (simplified)"""
    
    logger.info("🔧 Trying direct extraction method")
    
    # This is a placeholder for a direct extraction method
    # In a real implementation, this could use:
    # - yt-dlp with cookies (if available)
    # - Direct YouTube API calls
    # - Other extraction libraries
    
    # For now, we'll simulate a method that sometimes works
    video_id = extract_video_id(youtube_url)
    
    # Try to get basic video info from YouTube's oEmbed API
    try:
        oembed_response = requests.get(
            f"https://www.youtube.com/oembed?url={youtube_url}&format=json",
            timeout=10
        )
        
        if oembed_response.status_code == 200:
            oembed_data = oembed_response.json()
            title = oembed_data.get('title', 'Unknown')
            
            # This method doesn't actually download audio
            # It's just a placeholder to show the structure
            raise Exception("Direct extraction not implemented - would need yt-dlp or similar")
        else:
            raise Exception("Could not get video info from YouTube")
            
    except Exception as e:
        raise Exception(f"Direct method failed: {str(e)}")

def download_audio_file(download_url, job_id, extension, metadata):
    """Download audio file from URL with validation"""
    
    logger.info(f"📥 Downloading from: {download_url[:100]}...")
    
    # Test the URL first
    head_response = requests.head(download_url, timeout=10)
    
    if head_response.status_code != 200:
        raise Exception(f"Download URL test failed: {head_response.status_code}")
    
    # Download the file
    download_response = requests.get(download_url, timeout=120, stream=True)
    
    if download_response.status_code != 200:
        raise Exception(f"Download failed: {download_response.status_code}")
    
    # Save to temp file
    audio_path = f'/tmp/{job_id}.{extension}'
    
    with open(audio_path, 'wb') as f:
        for chunk in download_response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Verify file size
    file_size = os.path.getsize(audio_path)
    if file_size < 1000:  # Less than 1KB is probably an error
        raise Exception(f"Downloaded file is too small: {file_size} bytes")
    
    logger.info(f"✅ Downloaded {file_size} bytes to {audio_path}")
    
    return audio_path, metadata

def get_content_type(extension):
    """Get content type for file extension"""
    content_types = {
        'mp3': 'audio/mpeg',
        'mp4': 'audio/mp4',
        'webm': 'audio/webm',
        'm4a': 'audio/mp4',
        'wav': 'audio/wav'
    }
    return content_types.get(extension.lower(), 'audio/mpeg')

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