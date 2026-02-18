#!/usr/bin/env python3
"""
ECS Task: Downbeat Detector
Detects tempo, beats, and downbeat from audio file
"""

import os
import sys
import json
import boto3
from datetime import datetime

# Add simple-pipeline to path
sys.path.insert(0, '/app/simple-pipeline/chord-detection')

from downbeat_detection import detect_downbeats_complete

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def main():
    """Main entry point for downbeat detection"""
    
    # Get environment variables
    job_id = os.environ.get('JOB_ID')
    audio_bucket = os.environ.get('AUDIO_BUCKET')
    audio_key = os.environ.get('AUDIO_KEY')
    jobs_table_name = os.environ.get('JOBS_TABLE', 'ChordScout-Jobs-V2-dev')
    
    print(f"Starting downbeat detection for job: {job_id}")
    print(f"Audio: s3://{audio_bucket}/{audio_key}")
    
    if not all([job_id, audio_bucket, audio_key]):
        print("ERROR: Missing required environment variables")
        sys.exit(1)
    
    jobs_table = dynamodb.Table(jobs_table_name)
    
    try:
        # Download audio file
        audio_path = f'/tmp/{job_id}-audio.m4a'
        print(f"Downloading audio to {audio_path}...")
        s3.download_file(audio_bucket, audio_key, audio_path)
        print("Audio downloaded successfully")
        
        # Detect downbeat
        print("Detecting downbeat...")
        result = detect_downbeats_complete(audio_path)
        
        print(f"Downbeat detection complete:")
        print(f"  Tempo: {result['tempo']} BPM")
        print(f"  Time Signature: {result['time_signature']}")
        print(f"  Detected Downbeat: {result['first_downbeat']}s")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Total Beats: {len(result['beat_times'])}")
        print(f"  Total Measures: {len(result['downbeats'])}")
        
        # Update DynamoDB with results
        print("Updating DynamoDB...")
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='''
                SET downbeatData = :data,
                    downbeatStatus = :status,
                    updatedAt = :now
            ''',
            ExpressionAttributeValues={
                ':data': {
                    'tempo': float(result['tempo']),
                    'timeSignature': result['time_signature'],
                    'detectedDownbeat': float(result['first_downbeat']),
                    'confidence': float(result['confidence']),
                    'beatTimes': [float(t) for t in result['beat_times']],
                    'downbeats': [float(t) for t in result['downbeats']],
                    'totalBeats': len(result['beat_times']),
                    'totalMeasures': len(result['downbeats']),
                    'methodInfo': result.get('method_info', {}),
                },
                ':status': 'COMPLETED',
                ':now': datetime.utcnow().isoformat(),
            }
        )
        
        print("Downbeat detection completed successfully!")
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"ERROR: Downbeat detection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Update DynamoDB with error
        try:
            jobs_table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='''
                    SET downbeatStatus = :status,
                        errorMessage = :error,
                        updatedAt = :now
                ''',
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': str(e),
                    ':now': datetime.utcnow().isoformat(),
                }
            )
        except Exception as update_error:
            print(f"ERROR: Failed to update DynamoDB: {str(update_error)}")
        
        sys.exit(1)

if __name__ == '__main__':
    main()
