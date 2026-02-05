#!/usr/bin/env node

/**
 * Submit Test Job
 * 
 * Submits a YouTube URL for transcription and returns the job ID
 */

const https = require('https');

const API_URL = 'https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev';

async function submitJob(youtubeUrl) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({ youtubeUrl });

    const options = {
      hostname: 'l43ftjo75d.execute-api.us-east-1.amazonaws.com',
      port: 443,
      path: '/dev/jobs',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
      }
    };

    const req = https.request(options, (res) => {
      let body = '';

      res.on('data', (chunk) => {
        body += chunk;
      });

      res.on('end', () => {
        try {
          const response = JSON.parse(body);
          if (res.statusCode === 200 || res.statusCode === 201) {
            resolve(response);
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${body}`));
          }
        } catch (error) {
          reject(new Error(`Failed to parse response: ${body}`));
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.write(data);
    req.end();
  });
}

async function pollJobStatus(jobId) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'l43ftjo75d.execute-api.us-east-1.amazonaws.com',
      port: 443,
      path: `/dev/jobs/${jobId}`,
      method: 'GET'
    };

    const req = https.request(options, (res) => {
      let body = '';

      res.on('data', (chunk) => {
        body += chunk;
      });

      res.on('end', () => {
        try {
          const response = JSON.parse(body);
          resolve(response);
        } catch (error) {
          reject(new Error(`Failed to parse response: ${body}`));
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.end();
  });
}

async function main() {
  const youtubeUrl = process.argv[2];

  if (!youtubeUrl) {
    console.error('Usage: node submit-test-job.cjs <youtube-url>');
    console.error('');
    console.error('Example:');
    console.error('  node submit-test-job.cjs "https://www.youtube.com/watch?v=Q-RKhgsZu64"');
    console.error('');
    console.error('This will submit the job and monitor its progress.');
    process.exit(1);
  }

  try {
    console.log('🎵 Submitting job...');
    console.log(`URL: ${youtubeUrl}`);
    console.log('');

    const result = await submitJob(youtubeUrl);
    const jobId = result.jobId;

    console.log('✅ Job submitted successfully!');
    console.log(`Job ID: ${jobId}`);
    console.log('');
    console.log('Monitoring progress...');
    console.log('');

    // Poll for status
    let lastStatus = '';
    let lastProgress = 0;

    const pollInterval = setInterval(async () => {
      try {
        const status = await pollJobStatus(jobId);
        
        if (status.status !== lastStatus || status.progress !== lastProgress) {
          const progressBar = '█'.repeat(Math.floor(status.progress / 5)) + '░'.repeat(20 - Math.floor(status.progress / 5));
          console.log(`[${progressBar}] ${status.progress}% - ${status.status}`);
          lastStatus = status.status;
          lastProgress = status.progress;
        }

        if (status.status === 'COMPLETE') {
          clearInterval(pollInterval);
          console.log('');
          console.log('✅ Job completed!');
          console.log('');
          console.log('Next steps:');
          console.log(`  1. Analyze patterns: node test-pattern-analysis.cjs ${jobId}`);
          console.log(`  2. Create diagnostic PDF: node create-pattern-diagnostic-pdf.cjs ${jobId}`);
          console.log('');
          if (status.pdfUrl) {
            console.log(`PDF URL: ${status.pdfUrl}`);
          }
        } else if (status.status === 'FAILED') {
          clearInterval(pollInterval);
          console.log('');
          console.error('❌ Job failed!');
          console.error(`Error: ${status.errorMessage || 'Unknown error'}`);
          process.exit(1);
        }
      } catch (error) {
        // Ignore polling errors, keep trying
      }
    }, 3000);  // Poll every 3 seconds

    // Timeout after 10 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      console.log('');
      console.log('⏱️  Timeout reached (10 minutes)');
      console.log(`Job ID: ${jobId}`);
      console.log('Check status manually with:');
      console.log(`  node test-pattern-analysis.cjs ${jobId}`);
    }, 600000);

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

main();
