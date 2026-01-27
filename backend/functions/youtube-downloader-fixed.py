import json
import boto3
import subprocess
import os
import sys

# Add layer path to Python path
sys.path.insert(0, '/opt/python')

s3 = boto3.client('s3')

def get_youtube_cookies():
    """
    Get YouTube cookies from S3 if available.
    Cookies should be in Netscape format.
    """
    try:
        bucket = os.environ.get('BUCKET_NAME')
        cookies_key = 'config/youtube-cookies.txt'
        cookies_path = '/tmp/youtube-cookies.txt'
        
        # Try to download cookies from S3
        s3.download_file(bucket, cookies_key, cookies_path)
        print(f"Downloaded YouTube cookies from S3")
        return cookies_path
    except Exception as e:
        print(f"No cookies found or error downloading: {e}")
        return None

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
                    'key': output_key,
                    'success': True
                }
            }
        else:
            # YouTube URL - use yt-dlp
            output_path = f'/tmp/{job_id}.mp3'
            
            # Get cookies if available
            cookies_path = get_youtube_cookies()
            
            # Build yt-dlp command
            cmd = [
                'python3', '-m', 'yt_dlp',
                '-x',
                '--audio-format', 'mp3',
                '--quiet',  # Reduce output verbosity
                '--no-warnings',  # Suppress warnings
                '-o', output_path,
            ]
            
            # Add cookies if available
            if cookies_path and os.path.exists(cookies_path):
                cmd.extend(['--cookies', cookies_path])
                print("Using YouTube cookies for authentication")
            
            # Add URL
            cmd.append(source_url)
            
            # Run yt-dlp
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            # Only log first 500 chars to avoid large outputs
            stdout_preview = result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout
            print(f"yt-dlp completed successfully. Output preview: {stdout_preview}")
            
            # Upload to S3
            s3.upload_file(output_path, bucket, output_key)
            
            # Clean up
            if os.path.exists(output_path):
                os.remove(output_path)
            if cookies_path and os.path.exists(cookies_path):
                os.remove(cookies_path)
            
            return {
                'statusCode': 200,
                'body': {
                    'bucket': bucket,
                    'key': output_key,
                    'success': True
                }
            }
    except subprocess.CalledProcessError as e:
        error_msg = str(e.stderr)[:200] + "..." if len(str(e.stderr)) > 200 else str(e.stderr)
        print(f"Process error: {error_msg}")
        return {
            'statusCode': 500,
            'body': {'error': f'Processing failed: {error_msg}'}
        }
    except Exception as e:
        error_msg = str(e)[:200] + "..." if len(str(e)) > 200 else str(e)
        print(f"Error: {error_msg}")
        return {
            'statusCode': 500,
            'body': {'error': error_msg}
        }
