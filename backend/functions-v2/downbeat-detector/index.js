/**
 * Lambda Function: Downbeat Detector
 * 
 * Detects tempo, beats, and downbeat from audio file
 * Returns data needed for user confirmation UI
 */

const AWS = require('aws-sdk');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const s3 = new AWS.S3();
const dynamodb = new AWS.DynamoDB.DocumentClient();

const JOBS_TABLE = process.env.JOBS_TABLE || 'ChordScout-Jobs-V2-dev';

/**
 * Main Lambda handler
 */
exports.handler = async (event) => {
  console.log('Downbeat Detection Lambda triggered');
  console.log('Event:', JSON.stringify(event, null, 2));

  try {
    // Parse request body
    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    const { jobId, audioUrl, bucket, key } = body;

    if (!jobId || (!audioUrl && (!bucket || !key))) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          error: 'Missing required parameters: jobId and (audioUrl or bucket/key)',
        }),
      };
    }

    console.log(`Processing downbeat detection for job: ${jobId}`);

    // Download audio from S3
    const audioBucket = bucket || audioUrl.split('/')[2].split('.')[0];
    const audioKey = key || audioUrl.split('/').slice(3).join('/');
    
    const audioPath = `/tmp/${jobId}-audio.m4a`;
    console.log(`Downloading audio from s3://${audioBucket}/${audioKey}`);
    
    const audioFile = await s3.getObject({
      Bucket: audioBucket,
      Key: audioKey,
    }).promise();
    
    fs.writeFileSync(audioPath, audioFile.Body);
    console.log(`Audio downloaded to ${audioPath}`);

    // Run Python downbeat detection script
    const pythonScript = path.join(__dirname, 'detect_downbeat.py');
    const result = await runPythonScript(pythonScript, audioPath);

    console.log('Downbeat detection complete:', result);

    // Update job with downbeat data
    await dynamodb.update({
      TableName: JOBS_TABLE,
      Key: { jobId },
      UpdateExpression: 'SET downbeatData = :data, updatedAt = :now',
      ExpressionAttributeValues: {
        ':data': result,
        ':now': new Date().toISOString(),
      },
    }).promise();

    // Clean up
    if (fs.existsSync(audioPath)) {
      fs.unlinkSync(audioPath);
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
        ...result,
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

/**
 * Run Python script and return parsed JSON result
 */
function runPythonScript(scriptPath, audioPath) {
  return new Promise((resolve, reject) => {
    const python = spawn('python3', [scriptPath, audioPath]);
    
    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
      console.error('Python stderr:', data.toString());
    });

    python.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Python script exited with code ${code}: ${stderr}`));
        return;
      }

      try {
        // Parse JSON output from Python script
        const result = JSON.parse(stdout);
        resolve(result);
      } catch (error) {
        reject(new Error(`Failed to parse Python output: ${error.message}\nOutput: ${stdout}`));
      }
    });

    python.on('error', (error) => {
      reject(new Error(`Failed to start Python process: ${error.message}`));
    });
  });
}
