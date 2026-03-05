const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

const TABLE_NAME = process.env.DYNAMODB_TABLE || 'ChordScout-Jobs-V2-dev';

// Valid musical keys (12 major + 12 minor = 24 keys)
const VALID_KEYS = [
  // Major keys
  'C major', 'C# major', 'Db major', 'D major', 'D# major', 'Eb major',
  'E major', 'F major', 'F# major', 'Gb major', 'G major', 'G# major',
  'Ab major', 'A major', 'A# major', 'Bb major', 'B major', 'Cb major',
  // Minor keys
  'C minor', 'C# minor', 'Db minor', 'D minor', 'D# minor', 'Eb minor',
  'E minor', 'F minor', 'F# minor', 'Gb minor', 'G minor', 'G# minor',
  'Ab minor', 'A minor', 'A# minor', 'Bb minor', 'B minor', 'Cb minor'
];

exports.handler = async (event) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  try {
    // Parse jobId from path parameters
    const jobId = event.pathParameters?.jobId;
    if (!jobId) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        body: JSON.stringify({
          success: false,
          error: 'Missing jobId in path parameters'
        })
      };
    }
    
    // Parse request body
    let body;
    try {
      body = JSON.parse(event.body || '{}');
    } catch (parseError) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        body: JSON.stringify({
          success: false,
          error: 'Invalid JSON in request body'
        })
      };
    }
    
    const { confirmedKey } = body;
    
    // Validate confirmedKey
    if (!confirmedKey) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        body: JSON.stringify({
          success: false,
          error: 'Missing confirmedKey in request body'
        })
      };
    }
    
    // Validate key format
    if (!VALID_KEYS.includes(confirmedKey)) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        body: JSON.stringify({
          success: false,
          error: `Invalid key format. Must be one of the 24 standard keys (e.g., "C major", "A minor")`
        })
      };
    }
    
    // Check if job exists and get current data
    const getParams = {
      TableName: TABLE_NAME,
      Key: { jobId }
    };
    
    const getResult = await dynamodb.get(getParams).promise();
    
    if (!getResult.Item) {
      return {
        statusCode: 404,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        body: JSON.stringify({
          success: false,
          error: `Job not found: ${jobId}`
        })
      };
    }
    
    const detectedKey = getResult.Item.detectedKey || 'Unknown';
    
    // Update job with confirmed key
    const updateParams = {
      TableName: TABLE_NAME,
      Key: { jobId },
      UpdateExpression: 'SET confirmedKey = :key, updatedAt = :updatedAt',
      ExpressionAttributeValues: {
        ':key': confirmedKey,
        ':updatedAt': new Date().toISOString()
      },
      ReturnValues: 'ALL_NEW'
    };
    
    const updateResult = await dynamodb.update(updateParams).promise();
    
    console.log('Successfully updated job:', jobId, 'with confirmed key:', confirmedKey);
    
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
      },
      body: JSON.stringify({
        success: true,
        jobId,
        detectedKey,
        confirmedKey,
        message: 'Key confirmed'
      })
    };
    
  } catch (error) {
    console.error('Error confirming key:', error);
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
      },
      body: JSON.stringify({
        success: false,
        error: 'Internal server error',
        message: error.message
      })
    };
  }
};
