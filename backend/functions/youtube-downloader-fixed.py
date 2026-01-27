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
    source_url = event.get('youtubeUrl') or event.get('sourceUrl')
    bucket = os.environ['BUCKET_NAME']
    
    output_key = f'audio/{job_id}.mp3'
    
    try:
        # Check if source is an S3 URL
        if source_url.startswith('s3://'):
            # Extract bucket and key from S3 URL
            s3_parts = source_url.replace('s3://', '').split('/', 1)
            source_bucket = s3_parts[0]
            source_key = s3_parts[1]
            
            print(f"Copying from S3: {source_bucket}/{source_key}")
            
            # Download from source S3 bucket
            temp_input = f'/tmp/{job_id}_input'
            s3.download_file(source_bucket, source_key, temp_input)
            
            # Convert to MP3 if needed (using ffmpeg from layer)
            output_path = f'/tmp/{job_id}.mp3'
            
            # Check if file is already MP3
            if source_key.lower().endswith('.mp3'):
                # Just copy it
                os.rename(temp_input, output_path)
            else:
                # Convert to MP3 using ffmpeg
                subprocess.run([
                    'ffmpeg', '-i', temp_input,
                    '-vn',  # No video
                    '-ar', '44100',  # Sample rate
                    '-ac', '2',  # Stereo
                    '-b:a', '192k',  # Bitrate
                    output_path
                ], check=True, capture_output=True, text=True)
                os.remove(temp_input)
            
            # Upload to destination bucket
            s3.upload_file(output_path, bucket, output_key)
            os.remove(output_path)
            
            return {
                'statusCode': 200,
                'body': {
                    'bucket': bucket,
                    'key': output_key
                }
            }
        else:
            # YouTube URL - use yt-dlp
            output_path = f'/tmp/{job_id}.mp3'
            
            # yt-dlp is a Python module in the layer
            subprocess.run([
                'python3', '-m', 'yt_dlp',
                '-x',
                '--audio-format', 'mp3',
                '-o', output_path,
                source_url
            ], check=True, capture_output=True, text=True)
            
            # Upload to S3
            s3.upload_file(output_path, bucket, output_key)
            
            # Clean up
            if os.path.exists(output_path):
                os.remove(output_path)
            
            return {
                'statusCode': 200,
                'body': {
                    'bucket': bucket,
                    'key': output_key
                }
            }
    except subprocess.CalledProcessError as e:
        print(f"Process error: {e.stderr}")
        return {
            'statusCode': 500,
            'body': {'error': f'Processing failed: {e.stderr}'}
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }
