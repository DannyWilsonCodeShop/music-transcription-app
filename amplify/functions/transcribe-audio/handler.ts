import type { APIGatewayProxyHandler } from 'aws-lambda';
import { SFNClient, StartExecutionCommand } from '@aws-sdk/client-sfn';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand } from '@aws-sdk/lib-dynamodb';

const sfnClient = new SFNClient({ region: process.env.AWS_REGION || 'us-east-1' });
const dynamoClient = DynamoDBDocumentClient.from(new DynamoDBClient({}));

const STATE_MACHINE_ARN = process.env.STATE_MACHINE_ARN;
const JOBS_TABLE = process.env.JOBS_TABLE_NAME;

export const handler: APIGatewayProxyHandler = async (event) => {
  console.log('Transcription request:', JSON.stringify(event, null, 2));
  
  try {
    const body = JSON.parse(event.body || '{}');
    const { audioUrl, youtubeUrl, title, artist } = body;
    
    // Generate job ID
    const jobId = `job-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Create job record in DynamoDB
    await dynamoClient.send(new PutCommand({
      TableName: JOBS_TABLE,
      Item: {
        id: jobId,
        status: 'pending',
        audioUrl,
        youtubeUrl,
        title: title || 'Untitled',
        artist: artist || 'Unknown Artist',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }
    }));
    
    // Start Step Functions execution
    const executionInput = {
      jobId,
      audioUrl,
      youtubeUrl,
      title: title || 'Untitled',
      artist: artist || 'Unknown Artist',
    };
    
    const command = new StartExecutionCommand({
      stateMachineArn: STATE_MACHINE_ARN,
      name: jobId,
      input: JSON.stringify(executionInput),
    });
    
    const execution = await sfnClient.send(command);
    
    console.log('Step Functions execution started:', execution.executionArn);
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
      },
      body: JSON.stringify({
        message: 'Transcription job started',
        jobId,
        executionArn: execution.executionArn,
        status: 'pending'
      })
    };
  } catch (error) {
    console.error('Transcription error:', error);
    return {
      statusCode: 500,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
      },
      body: JSON.stringify({
        error: 'Failed to process transcription request',
        details: error instanceof Error ? error.message : 'Unknown error'
      })
    };
  }
};