import json
import boto3
import subprocess
import os
import sys

# Add layer path to Python path
sys.path.insert(0, '/opt/python')

s3 = boto3.client('s3')

def lambda_handler(event, context):
    job_id = event['jobId']
    youtube_url = event['youtubeUrl']
    bucket = os.environ['BUCKET_NAME']
    
    # Download audio using yt-dlp from layer
    output_path = f'/tmp/{job_id}.mp3'
    key = f'audio/{job_id}.mp3'
    
    try:
        # yt-dlp is a Python module in the layer
        subprocess.run([
            'python3', '-m', 'yt_dlp',
            '-x',
            '--audio-format', 'mp3',
            '-o', output_path,
            youtube_url
        ], check=True, capture_output=True, text=True)
        
        # Upload to S3
        s3.upload_file(output_path, bucket, key)
        
        # Clean up
        if os.path.exists(output_path):
            os.remove(output_path)
        
        return {
            'statusCode': 200,
            'body': {
                'bucket': bucket,
                'key': key
            }
        }
    except subprocess.CalledProcessError as e:
        print(f"yt-dlp error: {e.stderr}")
        return {
            'statusCode': 500,
            'body': {'error': f'yt-dlp failed: {e.stderr}'}
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }
