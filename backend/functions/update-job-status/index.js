const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, PutCommand, UpdateCommand } = require('@aws-sdk/lib-dynamodb');

const dynamoClient = DynamoDBDocumentClient.from(new DynamoDBClient({ region: 'us-east-1' }));
const TABLE_NAME = process.env.JOBS_TABLE_NAME;

exports.handler = async (event) => {
  const { jobId, status, step, progress, error, result } = event;
  
  const timestamp = new Date().toISOString();
  
  try {
    // If this is the initial creation
    if (status === 'PENDING') {
      await dynamoClient.send(new PutCommand({
        TableName: TABLE_NAME,
        Item: {
          id: jobId,
          userId: event.userId || 'anonymous',
          youtubeUrl: event.youtubeUrl,
          title: event.title || 'YouTube Video',
          status: 'PENDING',
          currentStep: 'Initializing',
          progress: 0,
          createdAt: timestamp,
          updatedAt: timestamp,
        },
      }));
    } else {
      // Update existing job
      const updateExpression = [];
      const expressionAttributeValues = {};
      const expressionAttributeNames = {};
      
      updateExpression.push('#status = :status');
      expressionAttributeValues[':status'] = status;
      expressionAttributeNames['#status'] = 'status';
      
      updateExpression.push('updatedAt = :updatedAt');
      expressionAttributeValues[':updatedAt'] = timestamp;
      
      if (step) {
        updateExpression.push('currentStep = :step');
        expressionAttributeValues[':step'] = step;
      }
      
      if (progress !== undefined) {
        updateExpression.push('progress = :progress');
        expressionAttributeValues[':progress'] = progress;
      }
      
      if (error) {
        updateExpression.push('#error = :error');
        expressionAttributeValues[':error'] = error;
        expressionAttributeNames['#error'] = 'error';
      }
      
      if (result) {
        if (result.lyrics) {
          updateExpression.push('lyrics = :lyrics');
          expressionAttributeValues[':lyrics'] = result.lyrics;
        }
        if (result.chords) {
          updateExpression.push('chords = :chords');
          expressionAttributeValues[':chords'] = result.chords;
        }
        if (result.sheetMusicUrl) {
          updateExpression.push('sheetMusicUrl = :sheetMusicUrl');
          expressionAttributeValues[':sheetMusicUrl'] = result.sheetMusicUrl;
        }
      }
      
      await dynamoClient.send(new UpdateCommand({
        TableName: TABLE_NAME,
        Key: { id: jobId },
        UpdateExpression: `SET ${updateExpression.join(', ')}`,
        ExpressionAttributeValues: expressionAttributeValues,
        ExpressionAttributeNames: Object.keys(expressionAttributeNames).length > 0 ? expressionAttributeNames : undefined,
      }));
    }
    
    return {
      statusCode: 200,
      body: { success: true, jobId, status, step, progress },
    };
  } catch (error) {
    console.error('Error updating job status:', error);
    throw error;
  }
};
