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
BASS_TASK_DEFINITION = os.environ.get('BASS_TASK_DEFINITION', 'bass-transcription-dev')
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
        
        # Get job data from DynamoDB to retrieve analysis options
        table = dynamodb.Table(JOBS_TABLE)
        job_response = table.get_item(Key={'jobId': job_id})
        job_data = job_response.get('Item', {})
        analysis_options = job_data.get('analysisOptions', {})
        music_part = analysis_options.get('musicPart', 'bass')
        
        print(f"Analysis options: {analysis_options}")
        print(f"Music part to analyze: {music_part}")
        
        # Update job status to PROCESSING
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, progress = :progress, statusMessage = :statusMessage, updatedAt = :updatedAt',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'PROCESSING',
                ':progress': 10,
                ':statusMessage': f'Warming up analysis container (this takes a few minutes)...',
                ':updatedAt': datetime.utcnow().isoformat()
            }
        )
        
        print(f"Job {job_id} marked as PROCESSING")
        
        # Choose task definition and container name based on music part
        if music_part == 'bass':
            task_definition = BASS_TASK_DEFINITION
            container_name = 'bass-transcription'
            print(f"Using BASS transcription pipeline")
        else:
            task_definition = ECS_TASK_DEFINITION
            container_name = 'chord-detector'
            print(f"Using CHORD detection pipeline")
        
        # Launch ECS Fargate task
        print("Launching ECS task...")
        print(f"Cluster: {ECS_CLUSTER}")
        print(f"Task Definition: {task_definition}")
        print(f"Container: {container_name}")
        print(f"Subnets: {ECS_SUBNETS}")
        print(f"Security Groups: {ECS_SECURITY_GROUPS}")
        
        try:
            response = ecs.run_task(
                cluster=ECS_CLUSTER,
                taskDefinition=task_definition,
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
                            'name': container_name,
                            'environment': [
                                {'name': 'JOB_ID', 'value': job_id},
                                {'name': 'AUDIO_BUCKET', 'value': bucket},
                                {'name': 'AUDIO_KEY', 'value': key}
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
