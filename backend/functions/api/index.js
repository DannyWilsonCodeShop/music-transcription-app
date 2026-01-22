const AWS = require('aws-sdk');
const { v4: uuidv4 } = require('uuid');

const dynamodb = new AWS.DynamoDB.DocumentClient();
const sqs = new AWS.SQS();
const s3 = new AWS.S3();

const TABLE_NAME = process.env.DYNAMODB_TABLE;
const QUEUE_URL = process.env.SQS_QUEUE_URL;
const BUCKET_NAME = process.env.S3_BUCKET;

exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event, null, 2));
  
  const { httpMethod, path, body } = event;
  
  try {
    switch (httpMethod) {
      case 'POST':
        if (path === '/transcribe/upload') {
          return await handleFileUpload(JSON.parse(body));
        } else if (path === '/transcribe/youtube') {
          return await handleYouTubeLink(JSON.parse(body));
        }
        break;
        
      case 'GET':
        if (path.startsWith('/transcribe/job/')) {
          const jobId = path.split('/').pop();
          return await getJobStatus(jobId);
        } else if (path === '/transcribe/jobs') {
          return await listJobs(event.queryStringParameters);
        }
        break;
        
      default:
        return response(405, { error: 'Method not allowed' });
    }
  } catch (error) {
    console.error('Error:', error);
    return response(500, { error: error.message });
  }
};

async function handleFileUpload(data) {
  const { fileName, fileType, userId } = data;
  const jobId = uuidv4();
  const s3Key = `uploads/${userId}/${jobId}/${fileName}`;
  
  // Generate presigned URL for upload
  const uploadUrl = s3.getSignedUrl('putObject', {
    Bucket: BUCKET_NAME,
    Key: s3Key,
    ContentType: fileType,
    Expires: 300 // 5 minutes
  });
  
  // Create job record
  const job = {
    id: jobId,
    userId,
    sourceType: 'file',
    fileName,
    s3Key,
    status: 'pending',
    createdAt: Date.now()
  };
  
  await dynamodb.put({
    TableName: TABLE_NAME,
    Item: job
  }).promise();
  
  // Queue processing job
  await sqs.sendMessage({
    QueueUrl: QUEUE_URL,
    MessageBody: JSON.stringify({ jobId, type: 'file' })
  }).promise();
  
  return response(200, { jobId, uploadUrl });
}

async function handleYouTubeLink(data) {
  const { youtubeUrl, userId } = data;
  const jobId = uuidv4();
  
  // Create job record
  const job = {
    id: jobId,
    userId,
    sourceType: 'youtube',
    youtubeUrl,
    status: 'pending',
    createdAt: Date.now()
  };
  
  await dynamodb.put({
    TableName: TABLE_NAME,
    Item: job
  }).promise();
  
  // Queue processing job
  await sqs.sendMessage({
    QueueUrl: QUEUE_URL,
    MessageBody: JSON.stringify({ jobId, type: 'youtube', youtubeUrl })
  }).promise();
  
  return response(200, { jobId });
}

async function getJobStatus(jobId) {
  const result = await dynamodb.get({
    TableName: TABLE_NAME,
    Key: { id: jobId }
  }).promise();
  
  if (!result.Item) {
    return response(404, { error: 'Job not found' });
  }
  
  return response(200, result.Item);
}

async function listJobs(params) {
  const { userId, limit = 20 } = params || {};
  
  const queryParams = {
    TableName: TABLE_NAME,
    IndexName: 'userIdIndex',
    KeyConditionExpression: 'userId = :userId',
    ExpressionAttributeValues: {
      ':userId': userId
    },
    Limit: parseInt(limit),
    ScanIndexForward: false
  };
  
  const result = await dynamodb.query(queryParams).promise();
  
  return response(200, {
    jobs: result.Items,
    lastKey: result.LastEvaluatedKey
  });
}

function response(statusCode, body) {
  return {
    statusCode,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': '*',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  };
}
