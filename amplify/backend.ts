import { defineBackend } from '@aws-amplify/backend';
import { auth } from './auth/resource';
import { data } from './data/resource';
import { storage } from './storage/resource';
import { transcribeAudio } from './functions/transcribe-audio/resource';
import { jobTrigger } from './functions/job-trigger/resource';
import { Policy, PolicyStatement } from 'aws-cdk-lib/aws-iam';
import { StartingPosition } from 'aws-cdk-lib/aws-lambda';
import { DynamoEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';

/**
 * Music Transcription App Backend
 * Provides AI-powered lyrics and chord transcription from audio files
 */
const backend = defineBackend({
  auth,
  data,
  storage,
  transcribeAudio,
  jobTrigger,
});

// Grant the transcribe function permissions to access DynamoDB and Step Functions
const transcribeFunction = backend.transcribeAudio.resources.lambda;
transcribeFunction.addToRolePolicy(
  new PolicyStatement({
    actions: ['dynamodb:PutItem', 'dynamodb:GetItem', 'dynamodb:UpdateItem'],
    resources: ['*'], // Will be restricted to specific table in production
  })
);
transcribeFunction.addToRolePolicy(
  new PolicyStatement({
    actions: ['states:StartExecution'],
    resources: ['*'], // Will be restricted to specific state machine in production
  })
);

// Grant the job trigger function permissions to start Step Functions
const jobTriggerFunction = backend.jobTrigger.resources.lambda;
jobTriggerFunction.addToRolePolicy(
  new PolicyStatement({
    actions: ['states:StartExecution'],
    resources: ['*'], // Will be restricted to specific state machine in production
  })
);

// Add DynamoDB Stream trigger to job trigger function
// Note: This requires the DynamoDB table to have streams enabled
// The stream ARN will need to be configured after deployment
const dataResources = backend.data.resources;
const jobsTable = dataResources.tables['TranscriptionJob'];

if (jobsTable) {
  jobTriggerFunction.addEventSource(
    new DynamoEventSource(jobsTable, {
      startingPosition: StartingPosition.LATEST,
      batchSize: 10,
      retryAttempts: 3,
    })
  );
}
