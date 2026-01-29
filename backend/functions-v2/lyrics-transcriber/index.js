// Lambda: Lyrics Transcriber
// Transcribes audio using Deepgram Nova-3 API

const { S3Client, GetObjectCommand } = require('@aws-sdk/client-s3');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, UpdateCommand } = require('@aws-sdk/lib-dynamodb');
const { createReadStream } = require('fs');
const { writeFile, unlink } = require('fs/promises');
const { exec } = require('child_process');
const { promisify } = require('util');
const fetch = require('node-fetch');
const ffmpegPath = require('ffmpeg-static');

const execAsync = promisify(exec);

const s3Client = new S3Client({});
const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);

const DEEPGRAM_API_KEY = process.env.DEEPGRAM_API_KEY;
const JOBS_TABLE = process.env.DYNAMODB_JOBS_TABLE;

exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event, null, 2));
  
  try {
    const { jobId, bucket, key } = event;
    
    // Update status
    await updateJobStatus(jobId, 'TRANSCRIBING', 40);
    
    // Download audio from S3
    const audioPath = `/tmp/${jobId}-audio`;
    const getCommand = new GetObjectCommand({ Bucket: bucket, Key: key });
    const response = await s3Client.send(getCommand);
    
    // Save to temp file
    const chunks = [];
    for await (const chunk of response.Body) {
      chunks.push(chunk);
    }
    const buffer = Buffer.concat(chunks);
    await writeFile(audioPath, buffer);
    
    console.log(`Audio downloaded: ${audioPath}, size: ${buffer.length} bytes`);
    
    // Always convert to MP3 for maximum Deepgram compatibility
    const mp3Path = `/tmp/${jobId}.mp3`;
    let finalAudioPath = audioPath;
    let contentType = 'audio/mpeg';
    
    try {
      // Use FFmpeg to convert any format to MP3 (extract audio only, no video)
      console.log(`Using FFmpeg at: ${ffmpegPath}`);
      console.log(`Converting audio to MP3...`);
      
      const { stdout, stderr } = await execAsync(
        `"${ffmpegPath}" -i "${audioPath}" -vn -acodec libmp3lame -ar 44100 -ab 128k -ac 2 "${mp3Path}" 2>&1`
      );
      
      console.log('FFmpeg output:', stderr || stdout);
      console.log('Successfully converted to MP3');
      
      finalAudioPath = mp3Path;
      
      // Clean up original file
      await unlink(audioPath).catch(() => {});
    } catch (error) {
      console.error('FFmpeg conversion failed:', error.message);
      console.error('FFmpeg stderr:', error.stderr || error.stdout);
      throw new Error(`Audio conversion failed: ${error.message}`);
    }
    
    console.log(`Audio ready for Deepgram: ${finalAudioPath}, type: ${contentType}`);
    
    // Transcribe with Deepgram Nova-3
    const deepgramUrl = 'https://api.deepgram.com/v1/listen';
    const params = new URLSearchParams({
      model: 'nova-3',
      smart_format: 'true',
      punctuate: 'true',
      paragraphs: 'true',
      utterances: 'true',
      diarize: 'false'
    });
    
    console.log('Sending to Deepgram...');
    
    const fs = require('fs');
    const audioStream = fs.createReadStream(finalAudioPath);
    
    const deepgramResponse = await fetch(`${deepgramUrl}?${params}`, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${DEEPGRAM_API_KEY}`,
        'Content-Type': contentType
      },
      body: audioStream
    });
    
    if (!deepgramResponse.ok) {
      const errorText = await deepgramResponse.text();
      throw new Error(`Deepgram API error: ${deepgramResponse.status} - ${errorText}`);
    }
    
    const transcription = await deepgramResponse.json();
    
    console.log('Transcription complete');
    
    // Extract lyrics with timestamps
    const results = transcription.results;
    const channels = results.channels[0];
    const alternatives = channels.alternatives[0];
    
    const lyricsText = alternatives.transcript;
    const words = alternatives.words || [];
    const paragraphs = alternatives.paragraphs?.paragraphs || [];
    
    const lyricsData = {
      text: lyricsText,
      words: words.map(w => ({
        word: w.word,
        start: w.start,
        end: w.end,
        confidence: w.confidence
      })),
      paragraphs: paragraphs.map(p => ({
        text: p.sentences.map(s => s.text).join(' '),
        start: p.start,
        end: p.end
      })),
      confidence: alternatives.confidence,
      metadata: {
        duration: results.metadata?.duration || 0,
        model: 'nova-3'
      }
    };
    
    // Update job with lyrics
    await docClient.send(new UpdateCommand({
      TableName: JOBS_TABLE,
      Key: { jobId },
      UpdateExpression: 'SET lyricsData = :lyrics, #status = :status, progress = :progress, updatedAt = :updated',
      ExpressionAttributeNames: { '#status': 'status' },
      ExpressionAttributeValues: {
        ':lyrics': lyricsData,
        ':status': 'TRANSCRIBED',
        ':progress': 60,
        ':updated': new Date().toISOString()
      },
      // Remove undefined values
      RemoveUndefinedValues: true
    }));
    
    // Clean up
    fs.unlinkSync(audioPath);
    
    return {
      statusCode: 200,
      body: {
        jobId,
        lyrics: lyricsData
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
