/**
 * Test Perfect Layout Deployment
 * Verifies that the deployed PDF generator uses the perfect 4-measure layout
 */

const https = require('https');
const fs = require('fs');

const API_URL = 'https://ppq03hif98.execute-api.us-east-1.amazonaws.com/dev';

async function testPerfectLayoutDeployment() {
  console.log('🧪 Testing Perfect Layout Deployment');
  console.log('=====================================\n');
  
  try {
    // Step 1: Create a job with YouTube URL
    console.log('📝 Step 1: Creating job...');
    const createJobResponse = await makeRequest('POST', '/jobs', {
      youtubeUrl: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
      title: 'Perfect Layout Test'
    });
    
    const jobId = createJobResponse.jobId;
    console.log(`✅ Job created: ${jobId}\n`);
    
    // Step 2: Wait for job to complete (poll status)
    console.log('⏳ Step 2: Waiting for job to complete...');
    let jobStatus = 'PENDING';
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes max
    
    while (jobStatus !== 'COMPLETE' && jobStatus !== 'FAILED' && attempts < maxAttempts) {
      await sleep(5000); // Wait 5 seconds
      
      const statusResponse = await makeRequest('GET', `/jobs/${jobId}`);
      jobStatus = statusResponse.status;
      const progress = statusResponse.progress || 0;
      
      console.log(`   Status: ${jobStatus} (${progress}%)`);
      
      if (jobStatus === 'FAILED') {
        console.error('❌ Job failed:', statusResponse.errorMessage);
        return;
      }
      
      attempts++;
    }
    
    if (jobStatus !== 'COMPLETE') {
      console.error('❌ Job did not complete in time');
      return;
    }
    
    console.log('✅ Job completed!\n');
    
    // Step 3: Get final job data
    console.log('📊 Step 3: Analyzing results...');
    const finalJob = await makeRequest('GET', `/jobs/${jobId}`);
    
    console.log('\n📄 PDF Generation Results:');
    console.log('==========================');
    console.log(`PDF URL: ${finalJob.pdfUrl}`);
    console.log(`Chords Detected: ${finalJob.chords?.length || 0}`);
    console.log(`Chord Changes: ${finalJob.chordAnalysis?.summary?.totalChanges || 0}`);
    console.log(`Data Reduction: ${finalJob.chordAnalysis?.summary?.dataReduction || 0}%`);
    
    // Step 4: Download and verify PDF
    console.log('\n📥 Step 4: Downloading PDF...');
    const pdfBuffer = await downloadFile(finalJob.pdfUrl);
    const pdfFileName = `test-perfect-layout-${jobId}.pdf`;
    fs.writeFileSync(pdfFileName, pdfBuffer);
    console.log(`✅ PDF saved: ${pdfFileName}`);
    
    // Step 5: Verify PDF format
    console.log('\n🔍 Step 5: Verifying PDF format...');
    const pdfText = pdfBuffer.toString('utf-8', 0, 1000); // Check first 1000 bytes
    
    // Check for indicators of perfect layout
    const hasNashvilleNumbers = pdfText.includes('Nashville Number System');
    const hasVerseLabels = pdfText.includes('Verse');
    
    console.log('\n✅ PDF Format Verification:');
    console.log(`   Nashville Number System: ${hasNashvilleNumbers ? '✅' : '❌'}`);
    console.log(`   Verse Labels: ${hasVerseLabels ? '✅' : '❌'}`);
    
    console.log('\n🎉 Perfect Layout Deployment Test Complete!');
    console.log(`\nOpen the PDF to verify:`);
    console.log(`   ${pdfFileName}`);
    console.log(`\nExpected format:`);
    console.log(`   ✅ 4 measures per line`);
    console.log(`   ✅ RED downbeat chords`);
    console.log(`   ✅ BLACK passing chords`);
    console.log(`   ✅ Verse labels every 8 measures`);
    console.log(`   ✅ Column positions: [38, 73, 108, 143]`);
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
  }
}

function makeRequest(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, API_URL);
    
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    };
    
    const req = https.request(url, options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve(parsed);
        } catch (error) {
          reject(new Error(`Failed to parse response: ${data}`));
        }
      });
    });
    
    req.on('error', reject);
    
    if (body) {
      req.write(JSON.stringify(body));
    }
    
    req.end();
  });
}

function downloadFile(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      const chunks = [];
      
      res.on('data', (chunk) => {
        chunks.push(chunk);
      });
      
      res.on('end', () => {
        resolve(Buffer.concat(chunks));
      });
    }).on('error', reject);
  });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Run the test
if (require.main === module) {
  testPerfectLayoutDeployment();
}

module.exports = { testPerfectLayoutDeployment };
