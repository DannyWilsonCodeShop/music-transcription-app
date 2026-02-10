import json
import boto3
import os
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

JOBS_TABLE = os.environ['JOBS_TABLE']

def lambda_handler(event, context):
    """
    Triggered by S3 upload event.
    Processes uploaded audio file for chord detection.
    """
    print(f"Event: {json.dumps(event)}")
    
    # Parse S3 event
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        # Extract job ID from key: uploads/{jobId}/filename.mp3
        parts = key.split('/')
        if len(parts) < 3 or parts[0] != 'uploads':
            print(f"Skipping non-upload key: {key}")
            continue
        
        job_id = parts[1]
        
        print(f"Processing job: {job_id}")
        
        # Update job status to PROCESSING
        table = dynamodb.Table(JOBS_TABLE)
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, progress = :progress, updatedAt = :updatedAt',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'PROCESSING',
                ':progress': 10,
                ':updatedAt': datetime.utcnow().isoformat()
            }
        )
        
        # TODO: Trigger actual processing (ECS task, Step Function, etc.)
        # For now, just mark as complete
        print(f"Job {job_id} marked as PROCESSING")
        
        # Simulate completion for testing
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, progress = :progress, updatedAt = :updatedAt',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'COMPLETED',
                ':progress': 100,
                ':updatedAt': datetime.utcnow().isoformat()
            }
        )
        
        print(f"Job {job_id} completed")
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Processing complete'})
    }
