/**
 * Lambda Function: Downbeat Detector (ECS Trigger)
 * 
 * Triggers ECS task to detect tempo, beats, and downbeat from audio file
 * ECS task has all Python libraries (librosa, numpy, etc.) already installed
 */

const AWS = require('aws-sdk');

const dynamodb = new AWS.DynamoDB.DocumentClient();
const ecs = new AWS.ECS();

const JOBS_TABLE = process.env.JOBS_TABLE || 'ChordScout-Jobs-V2-dev';
const ECS_CLUSTER = process.env.ECS_CLUSTER || 'ChordScout-dev';
const ECS_TASK_DEFINITION = process.env.ECS_TASK_DEFINITION || 'chordscout-downbeat-detector-dev';
const ECS_SUBNETS = process.env.ECS_SUBNETS ? process.env.ECS_SUBNETS.split(',') : [];
const ECS_SECURITY_GROUPS = process.env.ECS_SECURITY_GROUPS ? process.env.ECS_SECURITY_GROUPS.split(',') : [];

/**
 * Main Lambda handler
 */
exports.handler = async (event) => {
  console.log('Downbeat Detection Lambda triggered');
  console.log('Event:', JSON.stringify(event, null, 2));

  try {
    // Parse request body
    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    const { jobId, bucket, key } = body;

    if (!jobId || (!bucket || !key)) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          error: 'Missing required parameters: jobId and bucket/key',
        }),
      };
    }

    console.log(`Triggering downbeat detection for job: ${jobId}`);

    // Update job status
    await dynamodb.update({
      TableName: JOBS_TABLE,
      Key: { jobId },
      UpdateExpression: 'SET #status = :status, downbeatStatus = :dbStatus, updatedAt = :now',
      ExpressionAttributeNames: {
        '#status': 'status',
      },
      ExpressionAttributeValues: {
        ':status': 'DETECTING_DOWNBEAT',
        ':dbStatus': 'PROCESSING',
        ':now': new Date().toISOString(),
      },
    }).promise();

    // Trigger ECS task for downbeat detection
    console.log('Starting ECS task for downbeat detection...');
    
    const ecsParams = {
      cluster: ECS_CLUSTER,
      taskDefinition: ECS_TASK_DEFINITION,
      launchType: 'FARGATE',
      networkConfiguration: {
        awsvpcConfiguration: {
          subnets: ECS_SUBNETS,
          securityGroups: ECS_SECURITY_GROUPS,
          assignPublicIp: 'ENABLED',
        },
      },
      overrides: {
        containerOverrides: [
          {
            name: 'downbeat-detector',
            environment: [
              { name: 'JOB_ID', value: jobId },
              { name: 'AUDIO_BUCKET', value: bucket },
              { name: 'AUDIO_KEY', value: key },
              { name: 'JOBS_TABLE', value: JOBS_TABLE },
              { name: 'TASK_TYPE', value: 'DOWNBEAT_DETECTION' },
            ],
          },
        ],
      },
    };

    const ecsResult = await ecs.runTask(ecsParams).promise();
    
    if (!ecsResult.tasks || ecsResult.tasks.length === 0) {
      throw new Error('Failed to start ECS task');
    }

    const taskArn = ecsResult.tasks[0].taskArn;
    console.log('ECS task started:', taskArn);

    return {
      statusCode: 202,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        success: true,
        jobId,
        message: 'Downbeat detection started',
        taskArn,
      }),
    };

  } catch (error) {
    console.error('Error in downbeat detection:', error);
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        error: 'Downbeat detection failed',
        message: error.message,
      }),
    };
  }
};
