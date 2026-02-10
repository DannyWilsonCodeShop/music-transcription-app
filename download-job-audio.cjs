#!/usr/bin/env node
/**
 * Download Audio from Existing Job
 * 
 * Downloads the MP3 file from S3 for an existing job
 * so you can listen to it and verify quality
 * 
 * Usage: node download-job-audio.js <job-id>
 */

const AWS = require('aws-sdk');
const fs = require('fs');
const path = require('path');

// AWS Configuration
AWS.config.update({ region: 'us-east-1' });
const dynamodb = new AWS.DynamoDB.DocumentClient();
const s3 = new AWS.S3();

const JOBS_TABLE = 'ChordScout-Jobs-V2-dev';
const AUDIO_BUCKET = 'chordscout-audio-temp-dev-463470937777';

async function getJobStatus(jobId) {
  const params = {
    TableName: JOBS_TABLE,
    Key: { jobId }
  };
  
  const result = await dynamodb.get(params).promise();
  return result.Item;
}

async function downloadAudio(jobId) {
  console.log(`\n${'='.repeat(80)}`);
  console.log(`Downloading audio for job: ${jobId}`);
  console.log('='.repeat(80) + '\n');
  
  // Get job info
  console.log('Fetching job info...');
  const job = await getJobStatus(jobId);
  
  if (!job) {
    console.error(`✗ Job not found: ${jobId}`);
    process.exit(1);
  }
  
  console.log(`✓ Job found`);
  console.log(`  Status: ${job.status}`);
  console.log(`  Title: ${job.videoTitle || 'Unknown'}`);
  console.log(`  Duration: ${job.duration || 0}s`);
  
  // Download audio from S3
  // Try multiple possible S3 key formats
  const possibleKeys = [
    `audio/${jobId}.mp3`,
    `audio/${jobId}.m4a`,
    `audio/${jobId}/youtube_audio.mp3`,
    `audio/${jobId}/youtube_audio.m4a`
  ];
  
  const outputDir = path.join(process.cwd(), 'downloaded-audio');
  
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  console.log(`\nSearching for audio file in S3...`);
  console.log(`  Bucket: ${AUDIO_BUCKET}`);
  
  let audioData = null;
  let foundKey = null;
  let fileExtension = 'mp3';
  
  for (const s3Key of possibleKeys) {
    try {
      console.log(`  Trying: ${s3Key}`);
      const params = {
        Bucket: AUDIO_BUCKET,
        Key: s3Key
      };
      
      audioData = await s3.getObject(params).promise();
      foundKey = s3Key;
      fileExtension = s3Key.endsWith('.m4a') ? 'm4a' : 'mp3';
      console.log(`  ✓ Found: ${s3Key}`);
      break;
    } catch (error) {
      if (error.code !== 'NoSuchKey') {
        throw error;
      }
      // Continue to next key
    }
  }
  
  if (!audioData) {
    console.error(`\n✗ Audio file not found in S3`);
    console.error(`\nTried these keys:`);
    possibleKeys.forEach(key => console.error(`  - ${key}`));
    console.error(`\nPossible reasons:`);
    console.error(`  1. Job hasn't completed audio download yet`);
    console.error(`  2. Audio download failed`);
    console.error(`  3. Different S3 bucket or key format`);
    console.error(`\nCheck job status:`);
    console.error(`  Job status: ${job.status}`);
    console.error(`  Progress: ${job.progress}%`);
    process.exit(1);
  }
  
  const outputPath = path.join(outputDir, `${jobId}.${fileExtension}`);
  
  console.log(`\nDownloading from S3...`);
  console.log(`  Bucket: ${AUDIO_BUCKET}`);
  console.log(`  Key: ${foundKey}`);
  
  try {
    fs.writeFileSync(outputPath, audioData.Body);
    
    const stats = fs.statSync(outputPath);
    const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
    
    console.log(`\n✓ Audio downloaded successfully!`);
    console.log(`  File: ${outputPath}`);
    console.log(`  Size: ${fileSizeMB} MB`);
    
    // Estimate bitrate
    const duration = job.duration || 0;
    if (duration > 0) {
      const bitrateKbps = Math.round((stats.size * 8) / (duration * 1000));
      console.log(`  Estimated bitrate: ~${bitrateKbps} kbps`);
      
      console.log(`\nQuality Assessment:`);
      if (bitrateKbps >= 256) {
        console.log(`  ✓ High quality (256+ kbps)`);
      } else if (bitrateKbps >= 192) {
        console.log(`  ✓ Good quality (192-256 kbps)`);
      } else if (bitrateKbps >= 128) {
        console.log(`  ⚠ Medium quality (128-192 kbps)`);
      } else {
        console.log(`  ✗ Low quality (<128 kbps) - may affect chord detection`);
      }
    }
    
    // Show chord detection info if available
    if (job.chordsData) {
      console.log(`\nChord Detection Info:`);
      console.log(`  Model: ${job.chordsData.model || 'Unknown'}`);
      console.log(`  Total chords: ${job.chordsData.totalChords || 0}`);
      console.log(`  Detected key: ${job.chordsData.key || 'Unknown'} ${job.chordsData.mode || ''}`);
      console.log(`  Key confidence: ${job.chordsData.keyConfidence || 0}`);
      
      if (job.chordsData.chords && job.chordsData.chords.length > 0) {
        console.log(`\n  First 5 chords:`);
        job.chordsData.chords.slice(0, 5).forEach((chord, i) => {
          console.log(`    ${i + 1}. ${chord.chord} at ${chord.start.toFixed(1)}s`);
        });
      }
    }
    
    console.log(`\n${'='.repeat(80)}`);
    console.log(`NEXT STEPS:`);
    console.log('='.repeat(80));
    console.log(`\n1. Listen to the MP3 file:`);
    console.log(`   open "${outputPath}"`);
    console.log(`\n2. Check audio quality:`);
    console.log(`   - Is the audio clear?`);
    console.log(`   - Can you hear all instruments?`);
    console.log(`   - Any compression artifacts?`);
    console.log(`\n3. Manually identify chords:`);
    console.log(`   - What chords do YOU hear?`);
    console.log(`   - What key is the song in?`);
    console.log(`   - Compare with detected chords above`);
    console.log(`\n4. Report findings:`);
    console.log(`   - If audio quality is poor, the issue is in YouTube download`);
    console.log(`   - If audio is good but chords are wrong, the issue is in chord detection`);
    
  } catch (error) {
    console.error(`\n✗ Failed to download audio: ${error.message}`);
    
    if (error.code === 'NoSuchKey') {
      console.error(`\nThe audio file doesn't exist in S3.`);
      console.error(`This could mean:`);
      console.error(`  - The job hasn't reached the audio download stage yet`);
      console.error(`  - The audio download failed`);
      console.error(`  - The S3 key is different than expected`);
    }
    
    process.exit(1);
  }
}

// Main execution
const jobId = process.argv[2];

if (!jobId) {
  console.error('Usage: node download-job-audio.js <job-id>');
  console.error('Example: node download-job-audio.js abc123-def456-ghi789');
  process.exit(1);
}

downloadAudio(jobId)
  .then(() => {
    console.log(`\n✓ Download complete\n`);
    process.exit(0);
  })
  .catch(error => {
    console.error(`\n✗ Error: ${error.message}`);
    console.error(error);
    process.exit(1);
  });
