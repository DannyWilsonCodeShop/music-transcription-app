import json
import boto3
import os
import uuid
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

AUDIO_BUCKET = os.environ['AUDIO_BUCKET']
JOBS_TABLE = os.environ['JOBS_TABLE']

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    
    # Parse body
    if 'body' in event:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
    else:
        body = event
    
    filename = body.get('filename', 'audio.mp3')
    content_type = body.get('contentType', 'audio/mpeg')
    user_id = body.get('userId', 'anonymous')
    analysis_options = body.get('analysisOptions', {
        'musicPart': 'bass',
        'includeLyrics': False,
        'includeKey': True,
        'includeTempo': True,
        'includeTimeSignature': True
    })
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # S3 key for upload
    s3_key = f"uploads/{job_id}/{filename}"
    
    # Generate presigned URL for upload
    # MUST include ContentType to match what browser sends
    presigned_url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': AUDIO_BUCKET,
            'Key': s3_key,
            'ContentType': content_type
        },
        ExpiresIn=3600
    )
    
    # Create job in DynamoDB
    table = dynamodb.Table(JOBS_TABLE)
    table.put_item(Item={
        'jobId': job_id,
        'userId': user_id,
        'status': 'UPLOADING',
        'progress': 0,
        's3Key': s3_key,
        'filename': filename,
        'contentType': content_type,
        'analysisOptions': analysis_options,
        'createdAt': datetime.utcnow().isoformat(),
        'updatedAt': datetime.utcnow().isoformat()
    })
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'jobId': job_id,
            'uploadUrl': presigned_url,
            's3Key': s3_key
        })
    }
