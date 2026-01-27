const { SFNClient, StartExecutionCommand } = require('@aws-sdk/client-sfn');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand, PutCommand } = require('@aws-sdk/lib-dynamodb');

const sfnClient = new SFNClient({ region: 'us-east-1' });
const dynamoClient = DynamoDBDocumentClient.from(new DynamoDBClient({ region: 'us-east-1' }));

const STATE_MACHINE_ARN = process.env.STATE_MACHINE_ARN;
const JOBS_TABLE_NAME = process.env.JOBS_TABLE_NAME;

exports.handler = async (event) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Content-Type': 'application/json',
  };

  // Handle preflight
  if (event.httpMethod === 'OPTIONS' || event.requestContext?.http?.method === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: '',
    };
  }

  try {
    const path = event.path || event.rawPath || '';
    const method = event.httpMethod || event.requestContext?.http?.method || 'GET';

    // Start transcription
    if (path === '/transcription/start' && method === 'POST') {
      const body = JSON.parse(event.body || '{}');
      const { youtubeUrl, title } = body;

      if (!youtubeUrl) {
        return {
          statusCode: 400,
          headers,
          body: JSON.stringify({ error: 'youtubeUrl is required' }),
        };
      }

      const jobId = `job-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const now = new Date().toISOString();

      // Create initial job record in DynamoDB
      const putCommand = new PutCommand({
        TableName: JOBS_TABLE_NAME,
        Item: {
          id: jobId,
          youtubeUrl,
          title: title || 'YouTube Video',
          userId: 'anonymous',
          status: 'PENDING',
          currentStep: 'Initializing',
          progress: 0,
          createdAt: now,
          updatedAt: now,
        },
      });

      await dynamoClient.send(putCommand);

      // Start Step Functions execution
      const command = new StartExecutionCommand({
        stateMachineArn: STATE_MACHINE_ARN,
        name: jobId,
        input: JSON.stringify({
          jobId,
          youtubeUrl,
          title: title || 'YouTube Video',
          userId: 'anonymous',
        }),
      });

      await sfnClient.send(command);

      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({ jobId }),
      };
    }

    // Get job status
    if (path.startsWith('/transcription/status/') && method === 'GET') {
      const jobId = path.split('/').pop();

      const command = new GetCommand({
        TableName: JOBS_TABLE_NAME,
        Key: { id: jobId },
      });

      const response = await dynamoClient.send(command);

      if (!response.Item) {
        return {
          statusCode: 404,
          headers,
          body: JSON.stringify({ error: 'Job not found' }),
        };
      }

      return {
        statusCode: 200,
        headers,
        body: JSON.stringify(response.Item),
      };
    }

    return {
      statusCode: 404,
      headers,
      body: JSON.stringify({ error: 'Not found' }),
    };
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: error.message }),
    };
  }
};
