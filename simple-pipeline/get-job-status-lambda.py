import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')

JOBS_TABLE = os.environ['JOBS_TABLE']

def lambda_handler(event, context):
    """
    GET /jobs/{jobId}
    Returns job status and results.
    """
    print(f"Event: {json.dumps(event)}")
    
    # Extract job ID from path
    job_id = event.get('pathParameters', {}).get('jobId')
    
    if not job_id:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Missing jobId'})
        }
    
    # Get job from DynamoDB
    table = dynamodb.Table(JOBS_TABLE)
    response = table.get_item(Key={'jobId': job_id})
    
    if 'Item' not in response:
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Job not found'})
        }
    
    job = response['Item']
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(job, default=str)
    }
