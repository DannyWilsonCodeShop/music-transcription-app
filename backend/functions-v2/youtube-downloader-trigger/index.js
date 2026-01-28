// Lambda: YouTube Downloader Trigger
// Triggers ECS Fargate task for YouTube audio downloading

const { ECSClient, RunTaskCommand } = require('@aws-sdk/client-ecs');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, UpdateCommand } = require('@aws-sdk/lib-dynamodb');

const ecsClient = new ECSClient({});
const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);

const CLUSTER_NAME = process.env.ECS_CLUSTER || process.env.ECS_CLUSTER_NAME;
const TASK_DEFINITION = process.env.YOUTUBE_TASK_DEFINITION || 'youtube-downloader-task';
const SUBNET_IDS = process.env.SUBNET_IDS?.split(',') || [process.env.SUBNET_1, process.env.SUBNET_2].filter(Boolean);
const SECURITY_GROUP = process.env.SECURITY_GROUP || 'sg-0f34e2bad6dda9b0f'; // Default VPC security group
const JOBS_TABLE = process.env.DYNAMODB_JOBS_TABLE;
const OUTPUT_BUCKET = process.env.S3_BUCKET;

exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event, null, 2));
  
  try {
    const { jobId, youtubeUrl } = event;
    
    if (!jobId || !youtubeUrl) {
      throw new Error('Missing required parameters: jobId or youtubeUrl');
    }
    
    // Update job status
    await updateJobStatus(jobId, 'STARTING_DOWNLOAD', 10);
    
    console.log('Starting ECS task for YouTube download...');
    
    // Run ECS task
    const runTaskParams = {
      cluster: CLUSTER_NAME,
      taskDefinition: TASK_DEFINITION,
      launchType: 'FARGATE',
      networkConfiguration: {
        awsvpcConfiguration: {
          subnets: SUBNET_IDS,
          securityGroups: [SECURITY_GROUP],
          assignPublicIp: 'ENABLED'
        }
      },
      overrides: {
        containerOverrides: [
          {
            name: 'youtube-downloader',
            environment: [
              { name: 'JOB_ID', value: jobId },
              { name: 'YOUTUBE_URL', value: youtubeUrl },
              { name: 'OUTPUT_BUCKET', value: OUTPUT_BUCKET },
              { name: 'DYNAMODB_JOBS_TABLE', value: JOBS_TABLE }
            ]
          }
        ]
      }
    };
    
    const runTaskResponse = await ecsClient.send(new RunTaskCommand(runTaskParams));
    
    if (!runTaskResponse.tasks || runTaskResponse.tasks.length === 0) {
      throw new Error('Failed to start ECS task');
    }
    
    const taskArn = runTaskResponse.tasks[0].taskArn;
    console.log('ECS task started:', taskArn);
    
    // Update job with task ARN
    await docClient.send(new UpdateCommand({
      TableName: JOBS_TABLE,
      Key: { jobId },
      UpdateExpression: 'SET youtubeTaskArn = :taskArn, updatedAt = :updated',
      ExpressionAttributeValues: {
        ':taskArn': taskArn,
        ':updated': new Date().toISOString()
      }
    }));
    
    return {
      statusCode: 200,
      body: {
        jobId,
        taskArn,
        message: 'YouTube download task started'
      }
    };
    
  } catch (error) {
    console.error('Error:', error);
    await updateJobStatus(event.jobId, 'FAILED', 0, error.message);
    
    return {
      statusCode: 500,
      body: { error: error.message }
    };
  }
};

async function updateJobStatus(jobId, status, progress, error = null) {
  const updateExpr = error
    ? 'SET #status = :status, progress = :progress, errorMessage = :error, updatedAt = :updated'
    : 'SET #status = :status, progress = :progress, updatedAt = :updated';
  
  const exprValues = {
    ':status': status,
    ':progress': progress,
    ':updated': new Date().toISOString()
  };
  
  if (error) {
    exprValues[':error'] = error;
  }
  
  await docClient.send(new UpdateCommand({
    TableName: JOBS_TABLE,
    Key: { jobId },
    UpdateExpression: updateExpr,
    ExpressionAttributeNames: { '#status': 'status' },
    ExpressionAttributeValues: exprValues
  }));
}