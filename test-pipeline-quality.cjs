#!/usr/bin/env node
/**
 * Pipeline Quality Testing Script
 * 
 * Tests each stage of the ChordScout pipeline:
 * 1. YouTube audio download (MP3 quality)
 * 2. Audio analysis (chord detection)
 * 3. Key detection
 * 4. Pattern analysis
 * 
 * Usage: node test-pipeline-quality.js <youtube-url>
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

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function section(title) {
  console.log('\n' + '='.repeat(80));
  log(title, 'bright');
  console.log('='.repeat(80) + '\n');
}

async function getJobStatus(jobId) {
  const params = {
    TableName: JOBS_TABLE,
    Key: { jobId }
  };
  
  const result = await dynamodb.get(params).promise();
  return result.Item;
}

async function downloadAudioFromS3(jobId, outputPath) {
  log(`Searching for audio in S3...`, 'cyan');
  
  // Try multiple possible S3 key formats
  const possibleKeys = [
    `audio/${jobId}.mp3`,
    `audio/${jobId}.m4a`,
    `audio/${jobId}/youtube_audio.mp3`,
    `audio/${jobId}/youtube_audio.m4a`
  ];
  
  let audioData = null;
  let foundKey = null;
  
  for (const s3Key of possibleKeys) {
    try {
      log(`  Trying: ${s3Key}`, 'cyan');
      const params = {
        Bucket: AUDIO_BUCKET,
        Key: s3Key
      };
      
      audioData = await s3.getObject(params).promise();
      foundKey = s3Key;
      log(`  ✓ Found: ${s3Key}`, 'green');
      break;
    } catch (error) {
      if (error.code !== 'NoSuchKey') {
        throw error;
      }
      // Continue to next key
    }
  }
  
  if (!audioData) {
    log(`✗ Audio file not found in S3`, 'red');
    log(`\nTried these keys:`, 'yellow');
    possibleKeys.forEach(key => log(`  - ${key}`, 'cyan'));
    throw new Error('Audio file not found in S3');
  }
  
  fs.writeFileSync(outputPath, audioData.Body);
    
    const stats = fs.statSync(outputPath);
    const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
    
    log(`✓ Audio downloaded successfully`, 'green');
    log(`  File: ${outputPath}`, 'cyan');
    log(`  Size: ${fileSizeMB} MB`, 'cyan');
    
    return {
      path: outputPath,
      size: stats.size,
      sizeMB: fileSizeMB
    };
  } catch (error) {
    log(`✗ Failed to download audio: ${error.message}`, 'red');
    throw error;
  }
}

async function analyzeAudioQuality(audioPath) {
  section('STAGE 1: Audio Quality Analysis');
  
  const stats = fs.statSync(audioPath);
  const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
  
  log('File Information:', 'bright');
  log(`  Path: ${audioPath}`, 'cyan');
  log(`  Size: ${fileSizeMB} MB`, 'cyan');
  
  // Estimate bitrate based on file size and duration
  // This is approximate - actual bitrate analysis would require ffprobe
  log('\nQuality Indicators:', 'bright');
  log(`  File size: ${fileSizeMB} MB`, 'cyan');
  log(`  Expected for 192kbps MP3: ~1.4 MB per minute`, 'yellow');
  log(`  Expected for 128kbps MP3: ~0.9 MB per minute`, 'yellow');
  log(`  Expected for 320kbps MP3: ~2.4 MB per minute`, 'yellow');
  
  return {
    path: audioPath,
    size: stats.size,
    sizeMB: fileSizeMB
  };
}

async function analyzeChordDetection(jobData) {
  section('STAGE 2: Chord Detection Analysis');
  
  if (!jobData.chordsData) {
    log('✗ No chord data available', 'red');
    return null;
  }
  
  const chords = jobData.chordsData;
  
  log('Chord Detection Results:', 'bright');
  log(`  Model: ${chords.model || 'Unknown'}`, 'cyan');
  log(`  Total chords: ${chords.totalChords || 0}`, 'cyan');
  log(`  Duration: ${chords.duration || 0}s`, 'cyan');
  log(`  Tempo: ${chords.tempo || 0} BPM`, 'cyan');
  log(`  Time signature: ${chords.timeSignature || 'Unknown'}`, 'cyan');
  
  // Analyze chord types
  const chordTypes = {};
  const chordRoots = {};
  
  if (chords.chords && Array.isArray(chords.chords)) {
    chords.chords.forEach(chord => {
      const name = chord.chord;
      
      // Count chord types
      if (name.includes('maj7')) {
        chordTypes['maj7'] = (chordTypes['maj7'] || 0) + 1;
      } else if (name.includes('m7')) {
        chordTypes['m7'] = (chordTypes['m7'] || 0) + 1;
      } else if (name.match(/[A-G][#b]?7$/)) {
        chordTypes['7'] = (chordTypes['7'] || 0) + 1;
      } else if (name.includes('sus4')) {
        chordTypes['sus4'] = (chordTypes['sus4'] || 0) + 1;
      } else if (name.includes('dim')) {
        chordTypes['dim'] = (chordTypes['dim'] || 0) + 1;
      } else if (name.includes('m') && !name.includes('maj')) {
        chordTypes['minor'] = (chordTypes['minor'] || 0) + 1;
      } else {
        chordTypes['major'] = (chordTypes['major'] || 0) + 1;
      }
      
      // Count chord roots
      const root = name.match(/^[A-G][#b]?/)?.[0] || name;
      chordRoots[root] = (chordRoots[root] || 0) + 1;
    });
    
    log('\nChord Type Distribution:', 'bright');
    Object.entries(chordTypes)
      .sort((a, b) => b[1] - a[1])
      .forEach(([type, count]) => {
        const percentage = ((count / chords.totalChords) * 100).toFixed(1);
        log(`  ${type}: ${count} (${percentage}%)`, 'cyan');
      });
    
    log('\nMost Common Chord Roots:', 'bright');
    Object.entries(chordRoots)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .forEach(([root, count]) => {
        log(`  ${root}: ${count} times`, 'cyan');
      });
    
    log('\nFirst 10 Chords:', 'bright');
    chords.chords.slice(0, 10).forEach((chord, i) => {
      log(`  ${i + 1}. ${chord.chord.padEnd(8)} at ${chord.start.toFixed(1)}s (${chord.duration.toFixed(1)}s, conf: ${chord.confidence.toFixed(2)})`, 'cyan');
    });
  }
  
  return chordTypes;
}

async function analyzeKeyDetection(jobData) {
  section('STAGE 3: Key Detection Analysis');
  
  if (!jobData.chordsData) {
    log('✗ No chord data available', 'red');
    return null;
  }
  
  const chords = jobData.chordsData;
  
  log('Key Detection Results:', 'bright');
  log(`  Detected key: ${chords.key || 'Unknown'} ${chords.mode || ''}`, 'cyan');
  log(`  Confidence: ${chords.keyConfidence || 0}`, 'cyan');
  
  // Analyze if key makes sense based on chord frequency
  if (chords.chords && Array.isArray(chords.chords)) {
    const chordRoots = {};
    chords.chords.forEach(chord => {
      const root = chord.chord.match(/^[A-G][#b]?/)?.[0] || chord.chord;
      chordRoots[root] = (chordRoots[root] || 0) + 1;
    });
    
    const mostCommon = Object.entries(chordRoots)
      .sort((a, b) => b[1] - a[1])[0];
    
    log('\nKey Validation:', 'bright');
    log(`  Most common chord: ${mostCommon[0]} (${mostCommon[1]} times)`, 'cyan');
    log(`  Detected key: ${chords.key}`, 'cyan');
    
    if (mostCommon[0] === chords.key) {
      log(`  ✓ Most common chord matches detected key`, 'green');
    } else {
      log(`  ⚠ Most common chord (${mostCommon[0]}) differs from detected key (${chords.key})`, 'yellow');
      log(`  This might indicate incorrect key detection`, 'yellow');
    }
  }
  
  return {
    key: chords.key,
    mode: chords.mode,
    confidence: chords.keyConfidence
  };
}

async function analyzePatterns(jobData) {
  section('STAGE 4: Pattern Analysis');
  
  if (!jobData.chordsData || !jobData.chordsData.patternAnalysis) {
    log('✗ No pattern data available', 'red');
    return null;
  }
  
  const patterns = jobData.chordsData.patternAnalysis;
  
  log(`Found ${patterns.length} repeating patterns:`, 'bright');
  
  patterns.slice(0, 5).forEach((pattern, i) => {
    log(`\nPattern ${i + 1}:`, 'bright');
    log(`  Progression: ${pattern.progression.join(' → ')}`, 'cyan');
    log(`  Nashville: ${pattern.nashvilleProgression.join(' → ')}`, 'cyan');
    log(`  Length: ${pattern.length} chords`, 'cyan');
    log(`  Occurrences: ${pattern.occurrences} times`, 'cyan');
  });
  
  return patterns;
}

async function testPipeline(youtubeUrl) {
  section('ChordScout Pipeline Quality Test');
  
  log(`Testing URL: ${youtubeUrl}`, 'cyan');
  
  // Submit job via API
  log('\nSubmitting job to API...', 'yellow');
  
  const https = require('https');
  const apiUrl = 'https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev/jobs';
  
  const jobData = await new Promise((resolve, reject) => {
    const postData = JSON.stringify({
      youtubeUrl: youtubeUrl,
      title: 'Pipeline Quality Test'
    });
    
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': postData.length
      }
    };
    
    const req = https.request(apiUrl, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(new Error(`Failed to parse response: ${data}`));
        }
      });
    });
    
    req.on('error', reject);
    req.write(postData);
    req.end();
  });
  
  const jobId = jobData.jobId;
  log(`✓ Job created: ${jobId}`, 'green');
  
  // Poll for completion
  log('\nWaiting for job to complete...', 'yellow');
  
  let job;
  let attempts = 0;
  const maxAttempts = 60; // 5 minutes
  
  while (attempts < maxAttempts) {
    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
    
    job = await getJobStatus(jobId);
    
    if (!job) {
      log(`✗ Job not found: ${jobId}`, 'red');
      return;
    }
    
    log(`  Status: ${job.status} (${job.progress}%)`, 'cyan');
    
    if (job.status === 'COMPLETE') {
      log(`✓ Job completed!`, 'green');
      break;
    }
    
    if (job.status === 'FAILED') {
      log(`✗ Job failed: ${job.errorMessage}`, 'red');
      return;
    }
    
    attempts++;
  }
  
  if (attempts >= maxAttempts) {
    log(`✗ Job timed out after ${maxAttempts * 5} seconds`, 'red');
    return;
  }
  
  // Download audio file
  section('Downloading Audio File for Quality Check');
  
  const outputDir = path.join(process.cwd(), 'pipeline-test-output');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  const audioPath = path.join(outputDir, `${jobId}.mp3`);
  
  try {
    await downloadAudioFromS3(jobId, audioPath);
    
    // Analyze audio quality
    await analyzeAudioQuality(audioPath);
    
    log('\n' + '='.repeat(80), 'bright');
    log('AUDIO FILE SAVED FOR MANUAL INSPECTION', 'green');
    log('='.repeat(80), 'bright');
    log(`\nYou can now listen to the MP3 file to verify quality:`, 'yellow');
    log(`  ${audioPath}`, 'cyan');
    log(`\nCheck for:`, 'yellow');
    log(`  - Audio clarity and bitrate`, 'cyan');
    log(`  - Any compression artifacts`, 'cyan');
    log(`  - Whether all instruments are audible`, 'cyan');
    log(`  - Overall sound quality`, 'cyan');
    
  } catch (error) {
    log(`\n✗ Could not download audio file: ${error.message}`, 'red');
  }
  
  // Analyze chord detection
  await analyzeChordDetection(job);
  
  // Analyze key detection
  await analyzeKeyDetection(job);
  
  // Analyze patterns
  await analyzePatterns(job);
  
  // Summary
  section('SUMMARY');
  
  log('Pipeline Test Complete!', 'green');
  log(`\nJob ID: ${jobId}`, 'cyan');
  log(`Audio file: ${audioPath}`, 'cyan');
  log(`\nNext steps:`, 'yellow');
  log(`  1. Listen to the MP3 file to verify audio quality`, 'cyan');
  log(`  2. Check if the detected chords match what you hear`, 'cyan');
  log(`  3. Verify the detected key is correct`, 'cyan');
  log(`  4. Compare patterns with the actual song structure`, 'cyan');
  
  // Save full job data
  const jsonPath = path.join(outputDir, `${jobId}-full-data.json`);
  fs.writeFileSync(jsonPath, JSON.stringify(job, null, 2));
  log(`\nFull job data saved to: ${jsonPath}`, 'cyan');
}

// Main execution
const youtubeUrl = process.argv[2];

if (!youtubeUrl) {
  console.error('Usage: node test-pipeline-quality.js <youtube-url>');
  console.error('Example: node test-pipeline-quality.js https://www.youtube.com/watch?v=dQw4w9WgXcQ');
  process.exit(1);
}

testPipeline(youtubeUrl)
  .then(() => {
    log('\n✓ Test completed successfully', 'green');
    process.exit(0);
  })
  .catch(error => {
    log(`\n✗ Test failed: ${error.message}`, 'red');
    console.error(error);
    process.exit(1);
  });
