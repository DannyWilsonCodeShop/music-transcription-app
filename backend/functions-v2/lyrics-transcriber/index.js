// Lambda: Enhanced Lyrics Transcriber
// Transcribes audio using Deepgram Nova-3 API with syllable-level alignment

const { S3Client, GetObjectCommand } = require('@aws-sdk/client-s3');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, UpdateCommand } = require('@aws-sdk/lib-dynamodb');
const { writeFile } = require('fs/promises');
const fetch = require('node-fetch');

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
    
    // Determine content type from file extension
    const fileExtension = key.split('.').pop().toLowerCase();
    const contentTypeMap = {
      'mp3': 'audio/mpeg',
      'm4a': 'audio/mp4',
      'mp4': 'audio/mp4',
      'webm': 'audio/webm',
      'opus': 'audio/opus',
      'ogg': 'audio/ogg',
      'wav': 'audio/wav',
      'flac': 'audio/flac'
    };
    
    const contentType = contentTypeMap[fileExtension] || 'audio/mpeg';
    console.log(`Audio format: ${fileExtension}, Content-Type: ${contentType}`);
    
    // Use audio directly without conversion (Deepgram supports many formats)
    const finalAudioPath = audioPath;
    
    console.log(`Audio ready for Deepgram: ${finalAudioPath}, type: ${contentType}`);
    
    // Transcribe with Deepgram Nova-3 with enhanced features
    const deepgramUrl = 'https://api.deepgram.com/v1/listen';
    const params = new URLSearchParams({
      model: 'nova-3',
      smart_format: 'true',
      punctuate: 'true',
      paragraphs: 'true',
      utterances: 'true',
      diarize: 'false',
      word_timestamps: 'true',
      syllable_timestamps: 'true', // Enhanced: syllable-level timestamps
      phoneme_timestamps: 'true'   // Enhanced: phoneme-level analysis
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
    console.log('Full Deepgram response:', JSON.stringify(transcription, null, 2));
    
    // Extract enhanced lyrics with syllable-level alignment
    const results = transcription.results;
    const channels = results.channels[0];
    const alternatives = channels.alternatives[0];
    
    const lyricsText = alternatives.transcript;
    const words = alternatives.words || [];
    const paragraphs = alternatives.paragraphs?.paragraphs || [];
    
    console.log('Transcript text:', lyricsText);
    console.log('Words count:', words.length);
    console.log('Paragraphs count:', paragraphs.length);
    
    // Enhanced: Generate syllable-aligned lyrics
    const syllableAlignedLyrics = generateSyllableAlignment(words);
    console.log('Syllable-aligned lyrics count:', syllableAlignedLyrics.length);
    
    const lyricsData = {
      text: lyricsText,
      words: words.map(w => ({
        word: w.word,
        start: w.start,
        end: w.end,
        confidence: w.confidence,
        syllables: w.syllables || [] // Enhanced: syllable data
      })),
      paragraphs: paragraphs.map(p => ({
        text: p.sentences.map(s => s.text).join(' '),
        start: p.start,
        end: p.end
      })),
      syllableAlignedLyrics: syllableAlignedLyrics, // Enhanced: syllable alignment
      confidence: alternatives.confidence,
      metadata: {
        duration: results.metadata?.duration || 0,
        model: 'nova-3',
        enhanced: true,
        syllableCount: syllableAlignedLyrics.length
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

// Enhanced: Generate syllable-level alignment for musical integration
function generateSyllableAlignment(words) {
  const syllables = [];
  
  words.forEach(word => {
    if (word.syllables && word.syllables.length > 0) {
      // Use Deepgram syllable data if available
      word.syllables.forEach(syllable => {
        syllables.push({
          text: syllable.text,
          startTime: syllable.start,
          endTime: syllable.end,
          confidence: syllable.confidence || word.confidence,
          word: word.word
        });
      });
    } else {
      // Fallback: Split word into estimated syllables
      const estimatedSyllables = splitIntoSyllables(word.word);
      const syllableDuration = (word.end - word.start) / estimatedSyllables.length;
      
      estimatedSyllables.forEach((syllable, index) => {
        const startTime = word.start + (index * syllableDuration);
        const endTime = startTime + syllableDuration;
        
        syllables.push({
          text: syllable,
          startTime: startTime,
          endTime: endTime,
          confidence: word.confidence,
          word: word.word,
          estimated: true
        });
      });
    }
  });
  
  return syllables;
}

// Enhanced: Simple syllable splitting algorithm
function splitIntoSyllables(word) {
  // Simple vowel-based syllable splitting
  const vowels = 'aeiouAEIOU';
  const syllables = [];
  let currentSyllable = '';
  
  for (let i = 0; i < word.length; i++) {
    currentSyllable += word[i];
    
    // If we hit a vowel and the next character is a consonant, end syllable
    if (vowels.includes(word[i]) && i < word.length - 1 && !vowels.includes(word[i + 1])) {
      // Look ahead to see if we should include the next consonant
      if (i < word.length - 2 && !vowels.includes(word[i + 2])) {
        // Two consonants ahead, take one
        currentSyllable += word[i + 1];
        i++;
      }
      syllables.push(currentSyllable);
      currentSyllable = '';
    }
  }
  
  // Add remaining characters
  if (currentSyllable) {
    if (syllables.length > 0) {
      syllables[syllables.length - 1] += currentSyllable;
    } else {
      syllables.push(currentSyllable);
    }
  }
  
  return syllables.length > 0 ? syllables : [word];
}
