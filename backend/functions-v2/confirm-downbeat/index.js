/**
 * Lambda Function: Confirm Downbeat
 * 
 * Saves user-confirmed downbeat and time signature to DynamoDB
 * Triggers chord detection with confirmed values
 */

const AWS = require('aws-sdk');

const dynamodb = new AWS.DynamoDB.DocumentClient();
const ecs = new AWS.ECS();

const JOBS_TABLE = process.env.JOBS_TABLE || 'ChordScout-Jobs-V2-dev';
const ECS_CLUSTER = process.env.ECS_CLUSTER;
const ECS_TASK_DEFINITION = process.env.ECS_TASK_DEFINITION;
const ECS_SUBNETS = process.env.ECS_SUBNETS ? process.env.ECS_SUBNETS.split(',') : [];
const ECS_SECURITY_GROUPS = process.env.ECS_SECURITY_GROUPS ? process.env.ECS_SECURITY_GROUPS.split(',') : [];

/**
 * Main Lambda handler
 */
exports.handler = async (event) => {
  console.log('Confirm Downbeat Lambda triggered');
  console.log('Event:', JSON.stringify(event, null, 2));

  try {
    // Parse request body
    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    const { jobId, downbeat, timeSignature } = body;

    if (!jobId || downbeat === undefined || !timeSignature) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          error: 'Missing required parameters: jobId, downbeat, timeSignature',
        }),
      };
    }

    console.log(`Confirming downbeat for job ${jobId}: ${downbeat}s, ${timeSignature}`);

    // Get job details
    const jobResult = await dynamodb.get({
      TableName: JOBS_TABLE,
      Key: { jobId },
    }).promise();

    if (!jobResult.Item) {
      return {
        statusCode: 404,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          error: 'Job not found',
        }),
      };
    }

    const job = jobResult.Item;

    // Update job with confirmed downbeat
    await dynamodb.update({
      TableName: JOBS_TABLE,
      Key: { jobId },
      UpdateExpression: 'SET confirmedDownbeat = :downbeat, confirmedTimeSignature = :ts, updatedAt = :now, #status = :status, progress = :progress',
      ExpressionAttributeNames: {
        '#status': 'status',
      },
      ExpressionAttributeValues: {
        ':downbeat': downbeat,
        ':ts': timeSignature,
        ':now': new Date().toISOString(),
        ':status': 'DETECTING_CHORDS',
        ':progress': 70,
      },
    }).promise();

    console.log('Downbeat confirmed and saved to DynamoDB');

    // Trigger ECS task for chord detection with confirmed downbeat
    if (ECS_CLUSTER && ECS_TASK_DEFINITION) {
      console.log('Triggering ECS task for chord detection...');
      
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
              name: 'chord-detector',
              environment: [
                { name: 'JOB_ID', value: jobId },
                { name: 'AUDIO_BUCKET', value: job.bucket || job.audioBucket },
                { name: 'AUDIO_KEY', value: job.key || job.audioKey },
                { name: 'CONFIRMED_DOWNBEAT', value: downbeat.toString() },
                { name: 'CONFIRMED_TIME_SIGNATURE', value: timeSignature },
                { name: 'JOBS_TABLE', value: JOBS_TABLE },
              ],
            },
          ],
        },
      };

      const ecsResult = await ecs.runTask(ecsParams).promise();
      console.log('ECS task started:', ecsResult.tasks[0].taskArn);
    }

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        success: true,
        jobId,
        downbeat,
        timeSignature,
        message: 'Downbeat confirmed, chord detection started',
      }),
    };

  } catch (error) {
    console.error('Error confirming downbeat:', error);
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        error: 'Failed to confirm downbeat',
        message: error.message,
      }),
    };
  }
};
