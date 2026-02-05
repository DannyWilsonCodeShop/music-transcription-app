#!/usr/bin/env node

/**
 * Test Pattern Analysis
 * 
 * This script fetches a job's chord detection results and displays
 * the detected repeating patterns in a clear format.
 */

const AWS = require('aws-sdk');

// Configure AWS
AWS.config.update({
  region: 'us-east-1',
  credentials: new AWS.SharedIniFileCredentials({ profile: 'chordscout' })
});

const dynamodb = new AWS.DynamoDB.DocumentClient();

async function analyzePatterns(jobId) {
  console.log('='.repeat(80));
  console.log('🎵 CHORD PATTERN ANALYSIS');
  console.log('='.repeat(80));
  console.log(`Job ID: ${jobId}\n`);

  try {
    // Get job data from DynamoDB
    const result = await dynamodb.get({
      TableName: 'ChordScout-Jobs-V2-dev',
      Key: { jobId }
    }).promise();

    if (!result.Item) {
      console.error('❌ Job not found');
      return;
    }

    const job = result.Item;
    console.log(`Title: ${job.videoTitle || 'Unknown'}`);
    console.log(`Status: ${job.status}`);
    console.log(`Progress: ${job.progress}%\n`);

    if (!job.chordsData) {
      console.error('❌ No chord data available yet');
      return;
    }

    const chordsData = job.chordsData;
    
    // Display key detection
    console.log('🎹 KEY DETECTION');
    console.log('-'.repeat(80));
    console.log(`Detected Key: ${chordsData.key} ${chordsData.mode}`);
    console.log(`Confidence: ${(chordsData.keyConfidence * 100).toFixed(1)}%`);
    console.log(`Tempo: ${chordsData.tempo} BPM`);
    console.log(`Time Signature: ${chordsData.timeSignature}`);
    console.log(`Total Chords: ${chordsData.totalChords}`);
    console.log(`Duration: ${chordsData.duration}s\n`);

    // Display pattern analysis
    if (chordsData.patternAnalysis && chordsData.patternAnalysis.length > 0) {
      console.log('📊 REPEATING CHORD PATTERNS');
      console.log('-'.repeat(80));
      console.log(`Found ${chordsData.patternAnalysis.length} repeating patterns\n`);

      for (const pattern of chordsData.patternAnalysis) {
        console.log(`Pattern ${pattern.patternNumber}:`);
        console.log(`  Progression: ${pattern.progression.join(' → ')}`);
        console.log(`  Length: ${pattern.length} chords`);
        console.log(`  Occurrences: ${pattern.occurrences} times`);
        console.log(`  Chord positions: ${pattern.positions.join(', ')}`);
        
        // Calculate time ranges if we have chord data
        if (chordsData.chords && chordsData.chords.length > 0) {
          const times = pattern.positions
            .filter(pos => pos < chordsData.chords.length)
            .map(pos => {
              const chord = chordsData.chords[pos];
              return `${(chord.start || chord.time || 0).toFixed(1)}s`;
            })
            .slice(0, 5);  // Show first 5
          
          if (times.length > 0) {
            console.log(`  Time stamps: ${times.join(', ')}${pattern.positions.length > 5 ? '...' : ''}`);
          }
        }
        console.log('');
      }
    } else {
      console.log('⚠️  No repeating patterns detected\n');
    }

    // Display song structure
    if (chordsData.songStructure && chordsData.songStructure.length > 0) {
      console.log('🎼 SONG STRUCTURE');
      console.log('-'.repeat(80));
      
      for (const section of chordsData.songStructure) {
        console.log(`${section.label}:`);
        console.log(`  Measures: ${section.measureStart}-${section.measureEnd}`);
        console.log(`  Time: ${section.startTime}s - ${section.endTime}s`);
        console.log(`  Repetitions: ${section.patternCount}x`);
        if (section.pattern) {
          console.log(`  Pattern: ${section.pattern.join(' → ')}`);
        }
        console.log('');
      }
    } else {
      console.log('⚠️  No song structure detected\n');
    }

    // Display first 20 chords for reference
    if (chordsData.chords && chordsData.chords.length > 0) {
      console.log('🎸 CHORD SEQUENCE (First 20)');
      console.log('-'.repeat(80));
      
      const chordsToShow = chordsData.chords.slice(0, 20);
      for (let i = 0; i < chordsToShow.length; i++) {
        const chord = chordsToShow[i];
        const time = (chord.start || chord.time || 0).toFixed(1);
        const duration = (chord.duration || 0).toFixed(1);
        console.log(`${i + 1}. ${chord.chord.padEnd(6)} @ ${time.padStart(6)}s (${duration}s)`);
      }
      
      if (chordsData.chords.length > 20) {
        console.log(`... and ${chordsData.chords.length - 20} more chords`);
      }
      console.log('');
    }

    console.log('='.repeat(80));
    console.log('✅ Analysis complete');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error(error.stack);
  }
}

// Get job ID from command line
const jobId = process.argv[2];

if (!jobId) {
  console.error('Usage: node test-pattern-analysis.cjs <jobId>');
  process.exit(1);
}

analyzePatterns(jobId);
