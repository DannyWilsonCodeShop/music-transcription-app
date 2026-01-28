"""
ECS Task: Chord Detector
Runs as a Fargate task, processes audio and updates DynamoDB
"""

import json
import boto3
import os
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

JOBS_TABLE = os.environ['DYNAMODB_JOBS_TABLE']

def main():
    """Main entry point for ECS task"""
    
    # Get parameters from environment (passed from Lambda)
    job_id = os.environ.get('JOB_ID')
    bucket = os.environ.get('BUCKET')
    key = os.environ.get('KEY')
    
    if not all([job_id, bucket, key]):
        logger.error("Missing required environment variables")
        sys.exit(1)
    
    logger.info(f"Processing job {job_id}: {bucket}/{key}")
    
    try:
        # Update status
        update_job_status(job_id, 'DETECTING_CHORDS', 70)
        
        # Download audio from S3
        audio_path = f'/tmp/{job_id}.mp3'
        logger.info(f"Downloading from S3: {bucket}/{key}")
        s3_client.download_file(bucket, key, audio_path)
        
        # Detect chords (using mock for now)
        logger.info("Running chord detection...")
        chords_data = detect_chords(audio_path)
        
        # Update job with chords
        table = dynamodb.Table(JOBS_TABLE)
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET chordsData = :chords, #status = :status, progress = :progress, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':chords': chords_data,
                ':status': 'CHORDS_DETECTED',
                ':progress': 85,
                ':updated': 'ecs-task'
            }
        )
        
        logger.info("Chord detection complete!")
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        update_job_status(job_id, 'FAILED', 0, str(e))
        sys.exit(1)

def detect_chords(audio_path):
    """
    Detect chords - currently using mock data
    Can be enhanced with real ML models later
    """
    
    # Mock chord progression (common I-V-vi-IV)
    return {
        'chords': [
            {'chord': 'C', 'start': 0, 'end': 4, 'duration': 4},
            {'chord': 'G', 'start': 4, 'end': 8, 'duration': 4},
            {'chord': 'Am', 'start': 8, 'end': 12, 'duration': 4},
            {'chord': 'F', 'start': 12, 'end': 16, 'duration': 4},
            {'chord': 'C', 'start': 16, 'end': 20, 'duration': 4},
            {'chord': 'G', 'start': 20, 'end': 24, 'duration': 4},
            {'chord': 'Am', 'start': 24, 'end': 28, 'duration': 4},
            {'chord': 'F', 'start': 28, 'end': 32, 'duration': 4}
        ],
        'key': 'C',
        'model': 'mock-ecs',
        'totalChords': 8
    }

def update_job_status(job_id, status, progress, error=None):
    """Update job status in DynamoDB"""
    try:
        table = dynamodb.Table(JOBS_TABLE)
        update_expr = 'SET #status = :status, progress = :progress, updatedAt = :updated'
        expr_values = {
            ':status': status,
            ':progress': progress,
            ':updated': 'ecs-task'
        }
        
        if error:
            update_expr += ', errorMessage = :error'
            expr_values[':error'] = error
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues=expr_values
        )
    except Exception as e:
        logger.error(f"Failed to update job status: {str(e)}")

if __name__ == '__main__':
    main()
