import type { DynamoDBStreamHandler } from 'aws-lambda';
import { SFNClient, StartExecutionCommand } from '@aws-sdk/client-sfn';

const sfnClient = new SFNClient({ region: process.env.AWS_REGION || 'us-east-1' });
const STATE_MACHINE_ARN = process.env.STATE_MACHINE_ARN;

export const handler: DynamoDBStreamHandler = async (event) => {
  console.log('DynamoDB Stream event:', JSON.stringify(event, null, 2));
  
  for (const record of event.Records) {
    // Only process INSERT events with pending status
    if (record.eventName === 'INSERT' && record.dynamodb?.NewImage) {
      const newImage = record.dynamodb.NewImage;
      const status = newImage.status?.S;
      
      if (status === 'pending') {
        try {
          const jobId = newImage.id?.S;
          const audioUrl = newImage.audioUrl?.S;
          const youtubeUrl = newImage.youtubeUrl?.S;
          const title = newImage.title?.S || 'Untitled';
          const artist = newImage.artist?.S || 'Unknown Artist';
          
          console.log(`Starting transcription for job ${jobId}`);
          
          // Start Step Functions execution
          const executionInput = {
            jobId,
            audioUrl,
            youtubeUrl,
            title,
            artist,
          };
          
          const command = new StartExecutionCommand({
            stateMachineArn: STATE_MACHINE_ARN,
            name: jobId,
            input: JSON.stringify(executionInput),
          });
          
          const execution = await sfnClient.send(command);
          console.log('Step Functions execution started:', execution.executionArn);
        } catch (error) {
          console.error('Error starting Step Functions execution:', error);
        }
      }
    }
  }
};
