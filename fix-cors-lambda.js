// Fixed API Proxy Lambda with proper CORS headers
const { SFNClient, StartExecutionCommand } = require('@aws-sdk/client-sfn');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand, PutCommand } = require('@aws-sdk/lib-dynamodb');
const { v4: uuidv4 } = require('uuid');

const sfnClient = new SFNClient({});
const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);

const STATE_MACHINE_ARN = process.env.STATE_MACHINE_ARN;
const JOBS_TABLE_NAME = process.env.JOBS_TABLE_NAME;

// CORS headers for all responses
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
  'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
  'Access-Control-Max-Age': '86400'
};

exports.handler = async (event) => {
  console.log('API Proxy Event:', JSON.stringify(event, null, 2));

  // Handle CORS preflight requests
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: CORS_HEADERS,
      body: JSON.stringify({ message: 'CORS preflight successful' })
    };
  }

  try {
    const path = event.path || event.rawPath;
    const method = event.httpMethod || event.requestContext?.http?.method;
    
    console.log(`Processing ${method} ${path}`);

    // Route requests
    if (path.includes('/jobs') && method === 'POST') {
      return await handleStartJob(event);
    } else if (path.includes('/jobs/') && method === 'GET') {
      return await handleGetJob(event);
    } else {
      return {
        statusCode: 404,
        headers: CORS_HEADERS,
        body: JSON.stringify({ error: 'Not found' })
      };
    }

  } catch (error) {
    console.error('API Proxy Error:', error);
    return {
      statusCode: 500,
      headers: CORS_HEADERS,
      body: JSON.stringify({ 
        error: 'Internal server error',
        message: error.message 
      })
    };
  }
};

async function handleStartJob(event) {
  try {
    const body = JSON.parse(event.body || '{}');
    const { youtubeUrl } = body;

    if (!youtubeUrl) {
      return {
        statusCode: 400,
        headers: CORS_HEADERS,
        body: JSON.stringify({ error: 'youtubeUrl is required' })
      };
    }

    const jobId = uuidv4();
    const now = new Date().toISOString();

    // Create job record in DynamoDB
    await docClient.send(new PutCommand({
      TableName: JOBS_TABLE_NAME,
      Item: {
        jobId,
        youtubeUrl,
        status: 'PENDING',
        progress: 0,
        createdAt: now,
        updatedAt: now
      }
    }));

    // Start Step Functions execution
    const executionInput = {
      jobId,
      youtubeUrl
    };

    await sfnClient.send(new StartExecutionCommand({
      stateMachineArn: STATE_MACHINE_ARN,
      name: `transcription-${jobId}`,
      input: JSON.stringify(executionInput)
    }));

    console.log(`Started transcription job: ${jobId}`);

    return {
      statusCode: 200,
      headers: CORS_HEADERS,
      body: JSON.stringify({ 
        jobId,
        status: 'PENDING',
        message: 'Transcription job started successfully'
      })
    };

  } catch (error) {
    console.error('Start Job Error:', error);
    return {
      statusCode: 500,
      headers: CORS_HEADERS,
      body: JSON.stringify({ 
        error: 'Failed to start transcription job',
        message: error.message 
      })
    };
  }
}

async function handleGetJob(event) {
  try {
    const pathParts = event.path.split('/');
    const jobId = pathParts[pathParts.length - 1];

    if (!jobId) {
      return {
        statusCode: 400,
        headers: CORS_HEADERS,
        body: JSON.stringify({ error: 'Job ID is required' })
      };
    }

    // Get job from DynamoDB
    const result = await docClient.send(new GetCommand({
      TableName: JOBS_TABLE_NAME,
      Key: { jobId }
    }));

    if (!result.Item) {
      return {
        statusCode: 404,
        headers: CORS_HEADERS,
        body: JSON.stringify({ error: 'Job not found' })
      };
    }

    return {
      statusCode: 200,
      headers: CORS_HEADERS,
      body: JSON.stringify(result.Item)
    };

  } catch (error) {
    console.error('Get Job Error:', error);
    return {
      statusCode: 500,
      headers: CORS_HEADERS,
      body: JSON.stringify({ 
        error: 'Failed to get job status',
        message: error.message 
      })
    };
  }
}