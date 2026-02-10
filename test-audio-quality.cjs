#!/usr/bin/env node
/**
 * Test Audio Quality
 * 
 * Submits a job, waits for audio download, then immediately downloads
 * the audio file before it gets deleted
 */

const AWS = require('aws-sdk');
const https = require('https');
const fs = require('fs');
const path = require('path');

// AWS Configuration
AWS.config.update({ region: 'us-east-1' });
const dynamodb = new AWS.DynamoDB.DocumentClient();
const s3 = new AWS.S3();

const JOBS_TABLE = 'ChordScout-Jobs-V2-dev';
const AUDIO_BUCKET = 'chordscout-audio-temp-dev-463470937777';
const API_URL = 'https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev/jobs';

async function submitJob(youtubeUrl) {
  console.log('\n📤 Submitting job...');
  console.log(`   URL: ${youtubeUrl}`);
  
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({
      youtubeUrl: youtubeUrl,
      title: 'Audio Quality Test'
    });
    
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': postData.length
      }
    };
    
    const req = https.request(API_URL, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          resolve(result);
        } catch (e) {
          reject(new Error(`Failed to parse response: ${data}`));
        }
      });
    });
    
    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

async function getJobStatus(jobId) {
  const params = {
    TableName: JOBS_TABLE,
    Key: { jobId }
  };
  
  const result = await dynamodb.get(params).promise();
  return result.Item;
}

async function downloadAudioFromS3(jobId) {
  const possibleKeys = [
    `audio/${jobId}.mp3`,
    `audio/${jobId}.m4a`,
    `audio/${jobId}/youtube_audio.mp3`,
    `audio/${jobId}/youtube_audio.m4a`
  ];
  
  for (const s3Key of possibleKeys) {
    try {
      const params = {
        Bucket: AUDIO_BUCKET,
        Key: s3Key
      };
      
      const data = await s3.getObject(params).promise();
      
      const outputDir = path.join(process.cwd(), 'audio-quality-test');
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }
      
      const extension = s3Key.endsWith('.m4a') ? 'm4a' : 'mp3';
      const outputPath = path.join(outputDir, `${jobId}.${extension}`);
      
      fs.writeFileSync(outputPath, data.Body);
      
      const stats = fs.statSync(outputPath);
      const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
      
      return {
        path: outputPath,
        size: stats.size,
        sizeMB: fileSizeMB,
        s3Key: s3Key
      };
    } catch (error) {
      if (error.code !== 'NoSuchKey') {
        throw error;
      }
    }
  }
  
  return null;
}

async function testAudioQuality(youtubeUrl) {
  console.log('\n' + '='.repeat(80));
  console.log('🎵 Audio Quality Test');
  console.log('='.repeat(80));
  
  // Submit job
  const jobData = await submitJob(youtubeUrl);
  const jobId = jobData.jobId;
  
  console.log(`✅ Job created: ${jobId}\n`);
  
  // Poll for audio download completion
  console.log('⏳ Waiting for audio download...');
  
  let attempts = 0;
  const maxAttempts = 60; // 5 minutes
  let job = null;
  
  while (attempts < maxAttempts) {
    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
    
    job = await getJobStatus(jobId);
    
    if (!job) {
      console.log(`❌ Job not found: ${jobId}`);
      return;
    }
    
    console.log(`   Status: ${job.status} (${job.progress}%)`);
    
    // Try to download audio as soon as it's available
    if (job.status === 'AUDIO_READY' || job.status === 'TRANSCRIBING_LYRICS' || 
        job.status === 'DETECTING_CHORDS' || job.status === 'CHORDS_DETECTED' ||
        job.status === 'COMPLETE') {
      
      console.log('\n📥 Attempting to download audio...');
      const audioFile = await downloadAudioFromS3(jobId);
      
      if (audioFile) {
        console.log('\n' + '='.repeat(80));
        console.log('✅ AUDIO DOWNLOADED SUCCESSFULLY!');
        console.log('='.repeat(80));
        console.log(`\nFile: ${audioFile.path}`);
        console.log(`Size: ${audioFile.sizeMB} MB`);
        console.log(`S3 Key: ${audioFile.s3Key}`);
        
        // Estimate bitrate if we have duration
        if (job.duration && job.duration > 0) {
          const bitrateKbps = Math.round((audioFile.size * 8) / (job.duration * 1000));
          console.log(`Duration: ${job.duration}s`);
          console.log(`Estimated bitrate: ~${bitrateKbps} kbps`);
          
          console.log(`\n📊 Quality Assessment:`);
          if (bitrateKbps >= 256) {
            console.log(`   ✅ High quality (256+ kbps)`);
          } else if (bitrateKbps >= 192) {
            console.log(`   ✅ Good quality (192-256 kbps)`);
          } else if (bitrateKbps >= 128) {
            console.log(`   ⚠️  Medium quality (128-192 kbps)`);
          } else {
            console.log(`   ❌ Low quality (<128 kbps) - may affect chord detection`);
          }
        }
        
        console.log(`\n${'='.repeat(80)}`);
        console.log('🎧 NEXT STEPS:');
        console.log('='.repeat(80));
        console.log(`\n1. Listen to the audio file:`);
        console.log(`   open "${audioFile.path}"`);
        console.log(`\n2. Check audio quality:`);
        console.log(`   - Is the audio clear?`);
        console.log(`   - Can you hear all instruments?`);
        console.log(`   - Any compression artifacts?`);
        console.log(`\n3. Wait for job to complete, then check detected chords:`);
        console.log(`   node list-recent-jobs.cjs`);
        console.log(`\n4. Compare what you hear vs what was detected`);
        
        // Keep polling until complete to show final results
        if (job.status !== 'COMPLETE' && job.status !== 'FAILED') {
          console.log(`\n⏳ Waiting for chord detection to complete...`);
        }
      } else {
        console.log(`   ⚠️  Audio not in S3 yet, will try again...`);
      }
    }
    
    if (job.status === 'COMPLETE') {
      console.log(`\n✅ Job completed!`);
      
      if (job.chordsData) {
        console.log(`\n📊 Chord Detection Results:`);
        console.log(`   Model: ${job.chordsData.model || 'Unknown'}`);
        console.log(`   Total chords: ${job.chordsData.totalChords || 0}`);
        console.log(`   Key: ${job.chordsData.key || 'Unknown'} ${job.chordsData.mode || ''}`);
        console.log(`   Confidence: ${job.chordsData.keyConfidence || 0}`);
        
        if (job.chordsData.chords && job.chordsData.chords.length > 0) {
          console.log(`\n   First 10 chords:`);
          job.chordsData.chords.slice(0, 10).forEach((chord, i) => {
            console.log(`     ${i + 1}. ${chord.chord} at ${chord.start.toFixed(1)}s`);
          });
        }
      }
      
      break;
    }
    
    if (job.status === 'FAILED') {
      console.log(`\n❌ Job failed: ${job.errorMessage || 'Unknown error'}`);
      break;
    }
    
    attempts++;
  }
  
  if (attempts >= maxAttempts) {
    console.log(`\n⏱️  Timeout after ${maxAttempts * 5} seconds`);
  }
  
  console.log(`\n${'='.repeat(80)}\n`);
}

// Main execution
const youtubeUrl = process.argv[2];

if (!youtubeUrl) {
  console.error('Usage: node test-audio-quality.cjs <youtube-url>');
  console.error('\nExample:');
  console.error('  node test-audio-quality.cjs "https://www.youtube.com/watch?v=dQw4w9WgXcQ"');
  console.error('\nRecommended test songs:');
  console.error('  - "Let It Be" by The Beatles (simple chords)');
  console.error('  - "Wonderwall" by Oasis (simple progressions)');
  console.error('  - "The Girl from Ipanema" (jazz with 7th chords)');
  process.exit(1);
}

testAudioQuality(youtubeUrl)
  .then(() => {
    console.log('✅ Test completed');
    process.exit(0);
  })
  .catch(error => {
    console.error(`\n❌ Error: ${error.message}`);
    console.error(error);
    process.exit(1);
  });
