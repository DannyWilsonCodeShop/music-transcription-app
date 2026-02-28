import json
import boto3
import os
from datetime import datetime
from urllib.parse import unquote_plus

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
ecs = boto3.client('ecs')

JOBS_TABLE = os.environ.get('JOBS_TABLE', 'ChordScout-Jobs-V2-dev')
ECS_CLUSTER = os.environ.get('ECS_CLUSTER', 'ChordScout-dev')
ECS_TASK_DEFINITION = os.environ.get('ECS_TASK_DEFINITION', 'chordscout-chord-detector-dev')
ECS_SUBNETS = os.environ.get('ECS_SUBNETS', '').split(',')
ECS_SECURITY_GROUPS = os.environ.get('ECS_SECURITY_GROUPS', '').split(',')

def lambda_handler(event, context):
    """
    Triggered by S3 upload event.
    Launches ECS Fargate task for chord detection.
    """
    print(f"Event: {json.dumps(event)}")
    
    # Parse S3 event
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        size = record['s3']['object']['size']
        
        print(f"Processing: s3://{bucket}/{key} ({size} bytes)")
        
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
        
        print(f"Job {job_id} marked as PROCESSING")
        
        # Launch ECS Fargate task
        print("Launching ECS task...")
        print(f"Cluster: {ECS_CLUSTER}")
        print(f"Task Definition: {ECS_TASK_DEFINITION}")
        print(f"Subnets: {ECS_SUBNETS}")
        print(f"Security Groups: {ECS_SECURITY_GROUPS}")
        
        try:
            response = ecs.run_task(
                cluster=ECS_CLUSTER,
                taskDefinition=ECS_TASK_DEFINITION,
                launchType='FARGATE',
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': ECS_SUBNETS,
                        'securityGroups': ECS_SECURITY_GROUPS,
                        'assignPublicIp': 'ENABLED'
                    }
                },
                overrides={
                    'containerOverrides': [
                        {
                            'name': 'chord-detector',
                            'environment': [
                                {'name': 'JOB_ID', 'value': job_id},
                                {'name': 'BUCKET', 'value': bucket},
                                {'name': 'KEY', 'value': key}
                            ]
                        }
                    ]
                }
            )
            
            task_arn = response['tasks'][0]['taskArn']
            print(f"✅ ECS task launched: {task_arn}")
            
            # Update job with ECS task ARN
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET ecsTaskArn = :arn, updatedAt = :updatedAt',
                ExpressionAttributeValues={
                    ':arn': task_arn,
                    ':updatedAt': datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            print(f"ERROR launching ECS task: {str(e)}")
            # Update job status to FAILED
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET #status = :status, errorMessage = :error, updatedAt = :updatedAt',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': str(e),
                    ':updatedAt': datetime.utcnow().isoformat()
                }
            )
            raise
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Processing initiated'})
    }
