// Fix DynamoDB Size Limit - Hybrid S3 + DynamoDB Storage Solution
// Stores large chord data in S3, keeps metadata in DynamoDB

const AWS = require('aws-sdk');
const fs = require('fs');
const path = require('path');

const s3 = new AWS.S3({ region: 'us-east-1' });
const dynamodb = new AWS.DynamoDB.DocumentClient({ region: 'us-east-1' });

const CHORD_DATA_BUCKET = 'chordscout-chord-data-dev-463470937777';
const JOBS_TABLE = 'ChordScout-Jobs-dev';

async function fixDynamoDbSizeLimit() {
  console.log('🔧 Implementing DynamoDB Size Limit Fix...\n');
  
  // Solution 1: Hybrid Storage (S3 + DynamoDB)
  console.log('📊 SOLUTION 1: Hybrid Storage (Recommended)');
  console.log('✅ Store large chord data in S3');
  console.log('✅ Store metadata and references in DynamoDB');
  console.log('✅ No data loss, full functionality preserved');
  
  const hybridExample = {
    // DynamoDB record (under 400KB)
    dynamoRecord: {
      jobId: 'job-123',
      status: 'COMPLETE',
      title: 'Amazing Grace',
      key: 'G major',
      tempo: 120,
      timeSignature: '3/4',
      chordDataS3Key: 'chord-data/job-123-chords.json', // Reference to S3
      chordCount: 901,
      analysisMetadata: {
        totalChords: 901,
        analysisInterval: 0.2,
        downbeats: 120,
        passingChords: 781
      },
      createdAt: new Date().toISOString()
    },
    
    // S3 object (unlimited size)
    s3ChordData: {
      jobId: 'job-123',
      chords: [], // Full 901 chord array would go here
      analysis: {
        tempo: { bpm: 120, confidence: 0.95 },
        key: { root: 'G', mode: 'major', confidence: 0.89 },
        timeSignature: { numerator: 3, denominator: 4 }
      }
    }
  };
  
  console.log('\n📋 Hybrid Storage Structure:');
  console.log('DynamoDB Record Size:', JSON.stringify(hybridExample.dynamoRecord).length, 'bytes');
  console.log('S3 Chord Data: Unlimited size');
  
  // Solution 2: Compressed Storage
  console.log('\n📊 SOLUTION 2: Data Compression');
  console.log('✅ Compress chord data before DynamoDB storage');
  console.log('✅ Can reduce size by 60-80%');
  console.log('⚠️ Still may hit limits with very long songs');
  
  // Solution 3: Reduced Analysis Interval
  console.log('\n📊 SOLUTION 3: Reduce Analysis Interval');
  console.log('✅ Change from 0.2s to 0.5s intervals');
  console.log('✅ Reduces chord count from ~900 to ~360');
  console.log('⚠️ Less precise chord detection');
  
  return {
    recommendedSolution: 'hybrid',
    hybridExample: hybridExample
  };
}

// Implementation: Enhanced Audio Analyzer with S3 Storage
async function enhancedAudioAnalyzerWithS3Storage(event) {
  console.log('🎵 Enhanced Audio Analyzer with S3 Storage...');
  
  const { audioUrl, jobId } = event;
  
  try {
    // Step 1: Perform chord analysis (same as before)
    const analysis = await performChordAnalysis(audioUrl);
    
    // Step 2: Store large chord data in S3
    const s3Key = `chord-data/${jobId}-chords.json`;
    const chordData = {
      jobId: jobId,
      chords: analysis.chords.chords, // Full chord array
      analysis: {
        tempo: analysis.tempo,
        key: analysis.key,
        timeSignature: analysis.timeSignature
      },
      metadata: {
        analysisVersion: '2.0',
        totalChords: analysis.chords.chords.length,
        analysisInterval: analysis.chords.analysisInterval,
        createdAt: new Date().toISOString()
      }
    };
    
    await s3.putObject({
      Bucket: CHORD_DATA_BUCKET,
      Key: s3Key,
      Body: JSON.stringify(chordData),
      ContentType: 'application/json'
    }).promise();
    
    console.log(`✅ Chord data stored in S3: ${s3Key}`);
    
    // Step 3: Store compact metadata in DynamoDB
    const dynamoRecord = {
      jobId: jobId,
      status: 'CHORD_ANALYSIS_COMPLETE',
      chordDataS3Key: s3Key,
      chordCount: analysis.chords.chords.length,
      key: `${analysis.key.root} ${analysis.key.mode}`,
      tempo: analysis.tempo.bpm,
      timeSignature: `${analysis.timeSignature.numerator}/${analysis.timeSignature.denominator}`,
      analysisMetadata: {
        totalChords: analysis.chords.chords.length,
        analysisInterval: analysis.chords.analysisInterval,
        downbeats: analysis.chords.chords.filter(c => c.isDownbeat).length,
        passingChords: analysis.chords.chords.filter(c => c.isPassingChord).length,
        confidence: analysis.chords.chords.reduce((sum, c) => sum + c.confidence, 0) / analysis.chords.chords.length
      },
      updatedAt: new Date().toISOString()
    };
    
    await dynamodb.update({
      TableName: JOBS_TABLE,
      Key: { jobId },
      UpdateExpression: 'SET #status = :status, chordDataS3Key = :s3Key, chordCount = :count, #key = :key, tempo = :tempo, timeSignature = :timeSignature, analysisMetadata = :metadata, updatedAt = :updated',
      ExpressionAttributeNames: {
        '#status': 'status',
        '#key': 'key'
      },
      ExpressionAttributeValues: {
        ':status': dynamoRecord.status,
        ':s3Key': dynamoRecord.chordDataS3Key,
        ':count': dynamoRecord.chordCount,
        ':key': dynamoRecord.key,
        ':tempo': dynamoRecord.tempo,
        ':timeSignature': dynamoRecord.timeSignature,
        ':metadata': dynamoRecord.analysisMetadata,
        ':updated': dynamoRecord.updatedAt
      }
    }).promise();
    
    console.log('✅ Metadata stored in DynamoDB');
    
    return {
      statusCode: 200,
      body: {
        message: 'Chord analysis completed with S3 storage',
        jobId: jobId,
        chordCount: analysis.chords.chords.length,
        s3Key: s3Key
      }
    };
    
  } catch (error) {
    console.error('❌ Enhanced audio analysis failed:', error);
    throw error;
  }
}

// Implementation: PDF Generator with S3 Chord Data Retrieval
async function pdfGeneratorWithS3ChordData(event) {
  console.log('📄 PDF Generator with S3 Chord Data Retrieval...');
  
  const { jobId } = event;
  
  try {
    // Step 1: Get job metadata from DynamoDB
    const jobRecord = await dynamodb.get({
      TableName: JOBS_TABLE,
      Key: { jobId }
    }).promise();
    
    if (!jobRecord.Item) {
      throw new Error('Job not found');
    }
    
    const job = jobRecord.Item;
    console.log(`✅ Job metadata retrieved: ${job.chordCount} chords`);
    
    // Step 2: Get full chord data from S3
    const chordDataResponse = await s3.getObject({
      Bucket: CHORD_DATA_BUCKET,
      Key: job.chordDataS3Key
    }).promise();
    
    const chordData = JSON.parse(chordDataResponse.Body.toString());
    console.log(`✅ Chord data retrieved from S3: ${chordData.chords.length} chords`);
    
    // Step 3: Generate PDF with full chord data
    const pdfData = {
      title: job.title || 'Untitled',
      chords: chordData.chords,
      key: job.key,
      tempo: job.tempo,
      timeSignature: job.timeSignature,
      jobId: jobId
    };
    
    const pdfBuffer = await generatePDF(pdfData);
    
    // Step 4: Store PDF in S3 and update job
    const pdfS3Key = `pdfs/${jobId}.pdf`;
    await s3.putObject({
      Bucket: 'chordscout-pdfs-dev-463470937777',
      Key: pdfS3Key,
      Body: pdfBuffer,
      ContentType: 'application/pdf'
    }).promise();
    
    const pdfUrl = `https://chordscout-pdfs-dev-463470937777.s3.amazonaws.com/${pdfS3Key}`;
    
    await dynamodb.update({
      TableName: JOBS_TABLE,
      Key: { jobId },
      UpdateExpression: 'SET #status = :status, pdfUrl = :url, completedAt = :completed',
      ExpressionAttributeNames: { '#status': 'status' },
      ExpressionAttributeValues: {
        ':status': 'COMPLETE',
        ':url': pdfUrl,
        ':completed': new Date().toISOString()
      }
    }).promise();
    
    console.log('✅ PDF generated and stored successfully');
    
    return {
      statusCode: 200,
      body: {
        message: 'PDF generated successfully',
        pdfUrl: pdfUrl,
        chordCount: chordData.chords.length
      }
    };
    
  } catch (error) {
    console.error('❌ PDF generation failed:', error);
    throw error;
  }
}

// Mock functions for demonstration
async function performChordAnalysis(audioUrl) {
  // This would be the actual chord analysis logic
  return {
    chords: { chords: new Array(901).fill(null).map((_, i) => ({ chord: 'G', time: i * 0.2 })), analysisInterval: 0.2 },
    tempo: { bpm: 120 },
    key: { root: 'G', mode: 'major' },
    timeSignature: { numerator: 3, denominator: 4 }
  };
}

async function generatePDF(data) {
  // This would be the actual PDF generation logic
  return Buffer.from('mock pdf data');
}

// Export the solution
module.exports = {
  fixDynamoDbSizeLimit,
  enhancedAudioAnalyzerWithS3Storage,
  pdfGeneratorWithS3ChordData
};

// Run the analysis
if (require.main === module) {
  fixDynamoDbSizeLimit()
    .then(result => {
      console.log('\n🎯 RECOMMENDED SOLUTION: Hybrid S3 + DynamoDB Storage');
      console.log('✅ Unlimited chord data storage in S3');
      console.log('✅ Fast metadata queries in DynamoDB');
      console.log('✅ No functionality loss');
      console.log('✅ Cost-effective and scalable');
    })
    .catch(error => {
      console.error('❌ Analysis failed:', error.message);
    });
}