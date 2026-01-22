const AWS = require('aws-sdk');
const axios = require('axios');
const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs').promises;
const path = require('path');
const FormData = require('form-data');

const execAsync = promisify(exec);
const dynamodb = new AWS.DynamoDB.DocumentClient();
const s3 = new AWS.S3();
const secretsManager = new AWS.SecretsManager();

const TABLE_NAME = process.env.DYNAMODB_TABLE;
const BUCKET_NAME = process.env.S3_BUCKET;

let openaiApiKey;

exports.handler = async (event) => {
  console.log('Worker event:', JSON.stringify(event, null, 2));
  
  // Get OpenAI API key from Secrets Manager
  if (!openaiApiKey) {
    try {
      const secret = await secretsManager.getSecretValue({
        SecretId: process.env.OPENAI_SECRET_ARN
      }).promise();
      const secretData = JSON.parse(secret.SecretString);
      openaiApiKey = secretData.OPENAI_API_KEY;
    } catch (error) {
      console.error('Failed to get OpenAI API key:', error);
      throw error;
    }
  }
  
  for (const record of event.Records) {
    const message = JSON.parse(record.body);
    const { jobId, type, youtubeUrl } = message;
    
    try {
      await updateJobStatus(jobId, 'processing');
      
      let audioFilePath;
      
      if (type === 'youtube') {
        audioFilePath = await downloadYouTubeAudio(youtubeUrl, jobId);
      } else {
        audioFilePath = await downloadFromS3(jobId);
      }
      
      // Transcribe lyrics
      const lyrics = await transcribeLyrics(audioFilePath);
      
      // Detect chords (placeholder - implement actual chord detection)
      const chords = await detectChords(audioFilePath);
      
      // Save results to S3
      await saveResults(jobId, lyrics, chords);
      
      // Cleanup temp file
      await fs.unlink(audioFilePath).catch(err => 
        console.log('Cleanup error:', err)
      );
      
      await updateJobStatus(jobId, 'completed', { lyrics, chords });
      
    } catch (error) {
      console.error(`Error processing job ${jobId}:`, error);
      await updateJobStatus(jobId, 'failed', { 
        error: error.message 
      });
    }
  }
};

async function downloadYouTubeAudio(url, jobId) {
  const outputPath = `/tmp/${jobId}.mp3`;
  
  try {
    await execAsync(
      `yt-dlp -x --audio-format mp3 -o "${outputPath}" "${url}"`
    );
    return outputPath;
  } catch (error) {
    console.error('YouTube download error:', error);
    throw new Error('Failed to download YouTube audio');
  }
}

async function downloadFromS3(jobId) {
  const job = await dynamodb.get({
    TableName: TABLE_NAME,
    Key: { id: jobId }
  }).promise();
  
  const s3Key = job.Item.s3Key;
  const outputPath = `/tmp/${jobId}${path.extname(s3Key)}`;
  
  const s3Object = await s3.getObject({
    Bucket: BUCKET_NAME,
    Key: s3Key
  }).promise();
  
  await fs.writeFile(outputPath, s3Object.Body);
  
  return outputPath;
}

async function transcribeLyrics(audioFilePath) {
  try {
    const audioBuffer = await fs.readFile(audioFilePath);
    
    const formData = new FormData();
    formData.append('file', audioBuffer, {
      filename: 'audio.mp3',
      contentType: 'audio/mpeg'
    });
    formData.append('model', 'whisper-1');
    formData.append('response_format', 'verbose_json');
    
    const response = await axios.post(
      'https://api.openai.com/v1/audio/transcriptions',
      formData,
      {
        headers: {
          'Authorization': `Bearer ${openaiApiKey}`,
          ...formData.getHeaders()
        },
        maxContentLength: Infinity,
        maxBodyLength: Infinity
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('Transcription error:', error.response?.data || error);
    throw new Error('Failed to transcribe audio');
  }
}

async function detectChords(audioFilePath) {
  // Placeholder for chord detection
  // In production, integrate with a chord detection service or ML model
  return [
    { name: 'C', timestamp: 0 },
    { name: 'G', timestamp: 4 },
    { name: 'Am', timestamp: 8 },
    { name: 'F', timestamp: 12 }
  ];
}

async function saveResults(jobId, lyrics, chords) {
  const resultsKey = `results/${jobId}.json`;
  
  await s3.putObject({
    Bucket: BUCKET_NAME,
    Key: resultsKey,
    Body: JSON.stringify({ lyrics, chords }),
    ContentType: 'application/json'
  }).promise();
  
  return resultsKey;
}

async function updateJobStatus(jobId, status, data = {}) {
  const updateParams = {
    TableName: TABLE_NAME,
    Key: { id: jobId },
    UpdateExpression: 'SET #status = :status, updatedAt = :updatedAt',
    ExpressionAttributeNames: {
      '#status': 'status'
    },
    ExpressionAttributeValues: {
      ':status': status,
      ':updatedAt': Date.now()
    }
  };
  
  if (status === 'completed') {
    updateParams.UpdateExpression += ', lyrics = :lyrics, chords = :chords, completedAt = :completedAt';
    updateParams.ExpressionAttributeValues[':lyrics'] = data.lyrics;
    updateParams.ExpressionAttributeValues[':chords'] = data.chords;
    updateParams.ExpressionAttributeValues[':completedAt'] = Date.now();
  } else if (status === 'failed') {
    updateParams.UpdateExpression += ', errorMessage = :error';
    updateParams.ExpressionAttributeValues[':error'] = data.error;
  }
  
  await dynamodb.update(updateParams).promise();
}
