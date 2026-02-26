// Lambda: Get Job Status
// API endpoint for frontend to poll job status

const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand } = require('@aws-sdk/lib-dynamodb');

const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);

const JOBS_TABLE = process.env.DYNAMODB_JOBS_TABLE;

exports.handler = async (event) => {
  const timestamp = new Date().toISOString();
  console.log('=' .repeat(80));
  console.log(`[${timestamp}] 📊 GET JOB STATUS REQUEST`);
  console.log('=' .repeat(80));
  console.log('Event:', JSON.stringify(event, null, 2));
  
  try {
    const jobId = event.pathParameters?.jobId || event.jobId;
    
    if (!jobId) {
      console.error('[ERROR] Missing jobId in request');
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({ error: 'jobId is required' })
      };
    }
    
    console.log(`[INFO] Fetching job: ${jobId}`);
    
    // Get job from DynamoDB
    const result = await docClient.send(new GetCommand({
      TableName: JOBS_TABLE,
      Key: { jobId }
    }));
    
    if (!result.Item) {
      console.warn(`[WARN] Job not found: ${jobId}`);
      return {
        statusCode: 404,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({ error: 'Job not found' })
      };
    }
    
    const job = result.Item;
    
    console.log(`[INFO] Job found: ${jobId}`);
    console.log(`  Status: ${job.status}`);
    console.log(`  Progress: ${job.progress || 0}%`);
    console.log(`  Title: ${job.videoTitle || 'N/A'}`);
    console.log(`  Has PDF: ${job.pdfUrl ? 'Yes' : 'No'}`);
    console.log(`  Has Chords: ${job.chordsData ? 'Yes' : 'No'}`);
    console.log(`  Has Lyrics: ${job.lyricsData ? 'Yes' : 'No'}`);
    console.log(`  Error: ${job.errorMessage || 'None'}`);
    console.log(`  Created: ${job.createdAt}`);
    console.log(`  Updated: ${job.updatedAt}`);
    
    const response = {
      jobId: job.jobId,
      status: job.status,
      progress: job.progress || 0,
      videoTitle: job.videoTitle,
      youtubeUrl: job.youtubeUrl,
      pdfUrl: job.pdfUrl,
      chordsData: job.chordsData,
      lyricsData: job.lyricsData,
      error: job.errorMessage,
      createdAt: job.createdAt,
      updatedAt: job.updatedAt,
      completedAt: job.completedAt
    };
    
    console.log('✓ Returning job status to client');
    console.log('=' .repeat(80));
    
    // Return job status with all data
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify(response)
    };
    
  } catch (error) {
    console.error('=' .repeat(80));
    console.error('❌ GET JOB STATUS FAILED');
    console.error('=' .repeat(80));
    console.error('Error:', error);
    console.error('Stack:', error.stack);
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ error: error.message })
    };
  }
};
