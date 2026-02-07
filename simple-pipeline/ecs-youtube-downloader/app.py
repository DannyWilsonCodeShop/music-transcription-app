#!/usr/bin/env python3
"""
ECS YouTube Downloader
Downloads audio from YouTube using yt-dlp and uploads to S3
"""

import os
import sys
import json
import boto3
import subprocess
import tempfile
from datetime import datetime

# Get environment variables
YOUTUBE_URL = os.environ.get('YOUTUBE_URL')
JOB_ID = os.environ.get('JOB_ID')
S3_BUCKET = os.environ.get('S3_BUCKET')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS clients
s3 = boto3.client('s3', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

def update_job(status, progress, extra_data=None):
    """Update job status in DynamoDB"""
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    item = {
        'jobId': JOB_ID,
        'status': status,
        'progress': progress,
        'updatedAt': datetime.utcnow().isoformat()
    }
    
    if extra_data:
        item.update(extra_data)
    
    table.put_item(Item=item)
    print(f"✅ Updated job {JOB_ID}: {status} ({progress}%)")

def download_audio():
    """Download audio from YouTube using yt-dlp"""
    print(f"🎵 Downloading audio from: {YOUTUBE_URL}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, f"{JOB_ID}.mp3")
        
        # yt-dlp command for best audio quality
        cmd = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',  # Best quality
            '--format', 'bestaudio',
            '--output', output_file,
            '--no-playlist',
            '--no-warnings',
            '--quiet',
            YOUTUBE_URL
        ]
        
        print(f"🔧 Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=240,
                check=True
            )
            
            print(f"✅ yt-dlp completed successfully")
            
            # Check if file exists
            if not os.path.exists(output_file):
                raise Exception(f"Audio file not created: {output_file}")
            
            # Get file info
            file_size = os.path.getsize(output_file)
            print(f"📦 File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            
            # Upload to S3
            s3_key = f"audio/{JOB_ID}.mp3"
            print(f"☁️  Uploading to S3: s3://{S3_BUCKET}/{s3_key}")
            
            with open(output_file, 'rb') as f:
                s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=s3_key,
                    Body=f,
                    ContentType='audio/mpeg',
                    Metadata={
                        'youtube-url': YOUTUBE_URL,
                        'job-id': JOB_ID
                    }
                )
            
            print(f"✅ Upload complete!")
            
            return {
                's3Bucket': S3_BUCKET,
                's3Key': s3_key,
                'fileSize': file_size
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("Download timed out after 4 minutes")
        except subprocess.CalledProcessError as e:
            raise Exception(f"yt-dlp failed: {e.stderr}")

def main():
    """Main execution"""
    print("="*60)
    print("🚀 ECS YouTube Downloader Starting")
    print("="*60)
    print(f"Job ID: {JOB_ID}")
    print(f"YouTube URL: {YOUTUBE_URL}")
    print(f"S3 Bucket: {S3_BUCKET}")
    print(f"DynamoDB Table: {DYNAMODB_TABLE}")
    print("="*60)
    
    # Validate inputs
    if not all([YOUTUBE_URL, JOB_ID, S3_BUCKET, DYNAMODB_TABLE]):
        print("❌ Missing required environment variables")
        sys.exit(1)
    
    try:
        # Update status to downloading
        update_job('DOWNLOADING', 10)
        
        # Download and upload
        result = download_audio()
        
        # Update status to complete
        update_job('COMPLETE', 100, result)
        
        print("="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(json.dumps(result, indent=2))
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        update_job('FAILED', 0, {'error': str(e)})
        sys.exit(1)

if __name__ == '__main__':
    main()
