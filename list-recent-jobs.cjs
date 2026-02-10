#!/usr/bin/env node
/**
 * List Recent Jobs
 * Shows your most recent ChordScout jobs with their IDs
 */

const AWS = require('aws-sdk');

// AWS Configuration
AWS.config.update({ region: 'us-east-1' });
const dynamodb = new AWS.DynamoDB.DocumentClient();

const JOBS_TABLE = 'ChordScout-Jobs-V2-dev';

async function listRecentJobs() {
  console.log('\n' + '='.repeat(80));
  console.log('Recent ChordScout Jobs');
  console.log('='.repeat(80) + '\n');
  
  try {
    // Scan the table to get recent jobs
    // Note: In production, you'd want to use a GSI with a timestamp
    const params = {
      TableName: JOBS_TABLE,
      Limit: 20
    };
    
    const result = await dynamodb.scan(params).promise();
    
    if (!result.Items || result.Items.length === 0) {
      console.log('No jobs found.');
      return;
    }
    
    // Sort by creation time (most recent first)
    const jobs = result.Items.sort((a, b) => {
      const timeA = new Date(a.createdAt || 0).getTime();
      const timeB = new Date(b.createdAt || 0).getTime();
      return timeB - timeA;
    });
    
    console.log(`Found ${jobs.length} recent jobs:\n`);
    
    jobs.forEach((job, index) => {
      const status = job.status || 'UNKNOWN';
      const progress = job.progress || 0;
      const title = job.videoTitle || job.title || 'Untitled';
      const createdAt = job.createdAt ? new Date(job.createdAt).toLocaleString() : 'Unknown';
      
      // Status emoji
      let statusEmoji = '⏳';
      if (status === 'COMPLETE') statusEmoji = '✅';
      else if (status === 'FAILED') statusEmoji = '❌';
      else if (status.includes('DETECTING')) statusEmoji = '🎸';
      else if (status.includes('DOWNLOADING')) statusEmoji = '⬇️';
      
      console.log(`${index + 1}. ${statusEmoji} ${status} (${progress}%)`);
      console.log(`   Job ID: ${job.jobId}`);
      console.log(`   Title: ${title}`);
      console.log(`   Created: ${createdAt}`);
      
      if (job.chordsData) {
        console.log(`   Chords: ${job.chordsData.totalChords || 0} detected`);
        console.log(`   Key: ${job.chordsData.key || 'Unknown'} ${job.chordsData.mode || ''}`);
        console.log(`   Model: ${job.chordsData.model || 'Unknown'}`);
      }
      
      console.log('');
    });
    
    console.log('='.repeat(80));
    console.log('To download audio from a job:');
    console.log('  node download-job-audio.cjs <JOB_ID>');
    console.log('\nExample:');
    if (jobs.length > 0) {
      console.log(`  node download-job-audio.cjs ${jobs[0].jobId}`);
    }
    console.log('='.repeat(80) + '\n');
    
  } catch (error) {
    console.error('Error listing jobs:', error.message);
    console.error('\nMake sure you have AWS credentials configured:');
    console.error('  aws configure');
    process.exit(1);
  }
}

listRecentJobs()
  .then(() => process.exit(0))
  .catch(error => {
    console.error('Error:', error);
    process.exit(1);
  });
