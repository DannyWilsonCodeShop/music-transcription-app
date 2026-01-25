import { SFNClient, StartExecutionCommand, DescribeExecutionCommand } from '@aws-sdk/client-sfn';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand, QueryCommand } from '@aws-sdk/lib-dynamodb';
import { fromCognitoIdentityPool } from '@aws-sdk/credential-providers';

// AWS Configuration
const AWS_REGION = 'us-east-1';
const STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-Transcription-dev';
const JOBS_TABLE_NAME = 'ChordScout-TranscriptionJobs-dev';
const IDENTITY_POOL_ID = 'us-east-1:781b986b-cc62-418d-8b14-70292d1f773e';

// Initialize AWS clients with Cognito credentials
const credentials = fromCognitoIdentityPool({
  clientConfig: { region: AWS_REGION },
  identityPoolId: IDENTITY_POOL_ID,
});

const sfnClient = new SFNClient({ 
  region: AWS_REGION,
  credentials,
});

const dynamoClient = DynamoDBDocumentClient.from(
  new DynamoDBClient({ 
    region: AWS_REGION,
    credentials,
  })
);

export interface TranscriptionJob {
  id: string;
  youtubeUrl?: string;
  title: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  createdAt: string;
  updatedAt?: string;
  lyrics?: string;
  chords?: any;
  sheetMusicUrl?: string;
  error?: string;
}

/**
 * Start a new transcription job
 */
export async function startTranscription(
  youtubeUrl: string,
  title: string
): Promise<string> {
  const jobId = `job-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  try {
    const input = {
      jobId,
      youtubeUrl,
      title,
      userId: 'anonymous', // TODO: Replace with actual user ID from Cognito
    };
    
    console.log('Starting transcription with input:', input);
    console.log('State Machine ARN:', STATE_MACHINE_ARN);
    
    const command = new StartExecutionCommand({
      stateMachineArn: STATE_MACHINE_ARN,
      name: jobId,
      input: JSON.stringify(input),
    });
    
    const response = await sfnClient.send(command);
    console.log('Transcription started successfully:', response);
    return jobId;
  } catch (error) {
    console.error('Error starting transcription:', error);
    console.error('Error details:', JSON.stringify(error, null, 2));
    throw new Error('Failed to start transcription. Please try again.');
  }
}

/**
 * Get the status of a transcription job
 */
export async function getJobStatus(jobId: string): Promise<TranscriptionJob | null> {
  try {
    const command = new GetCommand({
      TableName: JOBS_TABLE_NAME,
      Key: { id: jobId },
    });
    
    const response = await dynamoClient.send(command);
    
    if (!response.Item) {
      return null;
    }
    
    return response.Item as TranscriptionJob;
  } catch (error) {
    console.error('Error getting job status:', error);
    return null;
  }
}

/**
 * Get execution status from Step Functions
 */
export async function getExecutionStatus(executionArn: string) {
  try {
    const command = new DescribeExecutionCommand({
      executionArn,
    });
    
    const response = await sfnClient.send(command);
    return response;
  } catch (error) {
    console.error('Error getting execution status:', error);
    return null;
  }
}

/**
 * Poll for job completion
 */
export async function pollJobStatus(
  jobId: string,
  onUpdate: (job: TranscriptionJob) => void,
  maxAttempts: number = 60,
  intervalMs: number = 5000
): Promise<TranscriptionJob> {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    
    const poll = async () => {
      attempts++;
      
      const job = await getJobStatus(jobId);
      
      if (!job) {
        if (attempts >= maxAttempts) {
          reject(new Error('Job not found'));
          return;
        }
        setTimeout(poll, intervalMs);
        return;
      }
      
      onUpdate(job);
      
      if (job.status === 'COMPLETED') {
        resolve(job);
        return;
      }
      
      if (job.status === 'FAILED') {
        reject(new Error(job.error || 'Transcription failed'));
        return;
      }
      
      if (attempts >= maxAttempts) {
        reject(new Error('Transcription timeout'));
        return;
      }
      
      setTimeout(poll, intervalMs);
    };
    
    poll();
  });
}

/**
 * Get user's transcription history
 */
export async function getUserTranscriptions(userId: string): Promise<TranscriptionJob[]> {
  try {
    const command = new QueryCommand({
      TableName: JOBS_TABLE_NAME,
      IndexName: 'UserIdIndex',
      KeyConditionExpression: 'userId = :userId',
      ExpressionAttributeValues: {
        ':userId': userId,
      },
      ScanIndexForward: false, // Most recent first
      Limit: 50,
    });
    
    const response = await dynamoClient.send(command);
    return (response.Items || []) as TranscriptionJob[];
  } catch (error) {
    console.error('Error getting user transcriptions:', error);
    return [];
  }
}

/**
 * Mock function for testing without AWS credentials
 */
export async function mockStartTranscription(
  youtubeUrl: string,
  title: string
): Promise<string> {
  const jobId = `mock-job-${Date.now()}`;
  console.log('Mock transcription started:', { jobId, youtubeUrl, title });
  
  // Simulate async operation
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  return jobId;
}

/**
 * Mock function for testing
 */
export async function mockGetJobStatus(jobId: string): Promise<TranscriptionJob> {
  // Simulate different stages
  const elapsed = Date.now() - parseInt(jobId.split('-')[2] || '0');
  
  let status: TranscriptionJob['status'] = 'PENDING';
  if (elapsed > 5000) status = 'PROCESSING';
  if (elapsed > 15000) status = 'COMPLETED';
  
  return {
    id: jobId,
    title: 'Test Song',
    status,
    createdAt: new Date().toISOString(),
    lyrics: status === 'COMPLETED' ? 'Never gonna give you up\nNever gonna let you down' : undefined,
    chords: status === 'COMPLETED' ? {
      key: 'C',
      mode: 'major',
      chords: [
        { name: 'C', timestamp: 0, duration: 2, confidence: 0.9 },
        { name: 'G', timestamp: 2, duration: 2, confidence: 0.85 },
        { name: 'Am', timestamp: 4, duration: 2, confidence: 0.88 },
        { name: 'F', timestamp: 6, duration: 2, confidence: 0.92 },
      ]
    } : undefined,
  };
}
