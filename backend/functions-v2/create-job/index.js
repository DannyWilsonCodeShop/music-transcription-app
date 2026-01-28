// Lambda: Create Job
// Creates a new transcription job in DynamoDB and triggers Step Functions

const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, PutCommand } = require('@aws-sdk/lib-dynamodb');
const { SFNClient, StartExecutionCommand } = require('@aws-sdk/client-sfn');
const { v4: uuidv4 } = require('uuid');

const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);
const sfnClient = new SFNClient({});

const JOBS_TABLE = process.env.DYNAMODB_JOBS_TABLE;
const STATE_MACHINE_ARN = process.env.STEP_FUNCTION_ARN;

exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event, null, 2));
  
  try {
    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    const { youtubeUrl, userId } = body;
    
    if (!youtubeUrl) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'youtubeUrl is required' })
      };
    }
    
    // Extract video ID from URL
    const videoId = extractVideoId(youtubeUrl);
    if (!videoId) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Invalid YouTube URL' })
      };
    }
    
    const jobId = uuidv4();
    const timestamp = new Date().toISOString();
    
    // Create job record in DynamoDB
    const jobRecord = {
      jobId,
      userId: userId || 'anonymous',
      youtubeUrl,
      videoId,
      status: 'PENDING',
      progress: 0,
      createdAt: timestamp,
      updatedAt: timestamp
    };
    
    await docClient.send(new PutCommand({
      TableName: JOBS_TABLE,
      Item: jobRecord
    }));
    
    // Start Step Functions execution
    const executionInput = {
      jobId,
      youtubeUrl,
      videoId,
      userId: userId || 'anonymous'
    };
    
    const execution = await sfnClient.send(new StartExecutionCommand({
      stateMachineArn: STATE_MACHINE_ARN,
      name: `job-${jobId}`,
      input: JSON.stringify(executionInput)
    }));
    
    console.log('Started execution:', execution.executionArn);
    
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        jobId,
        status: 'PENDING',
        message: 'Job created successfully',
        executionArn: execution.executionArn
      })
    };
    
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: error.message })
    };
  }
};

function extractVideoId(url) {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/,
    /youtube\.com\/embed\/([^&\n?#]+)/,
    /youtube\.com\/v\/([^&\n?#]+)/
  ];
  
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match && match[1]) {
      return match[1];
    }
  }
  
  return null;
}
