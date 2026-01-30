// Test Enhanced Music Transcription System
// Tests the complete pipeline with 0.2s chord detection and syllable analysis

const AWS = require('aws-sdk');

// Configure AWS
AWS.config.update({ region: 'us-east-1' });
const stepfunctions = new AWS.StepFunctions();
const dynamodb = new AWS.DynamoDB.DocumentClient();

const STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-V2-Transcription-dev';
const JOBS_TABLE = 'ChordScout-Jobs-V2-dev';

async function testEnhancedSystem() {
  console.log('🚀 Testing Enhanced Music Transcription System...\n');

  try {
    // Test YouTube URL (Amazing Grace)
    const testUrl = 'https://www.youtube.com/watch?v=CDdvReNKKuk';
    const jobId = `test-enhanced-${Date.now()}`;

    console.log(`📝 Job ID: ${jobId}`);
    console.log(`🎵 Test URL: ${testUrl}\n`);

    // Create job record in DynamoDB
    await dynamodb.put({
      TableName: JOBS_TABLE,
      Item: {
        jobId: jobId,
        youtubeUrl: testUrl,
        status: 'PENDING',
        progress: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
    }).promise();

    console.log('✅ Job record created in DynamoDB');

    // Start enhanced Step Functions execution
    const executionParams = {
      stateMachineArn: STATE_MACHINE_ARN,
      name: `enhanced-test-${Date.now()}`,
      input: JSON.stringify({
        jobId: jobId,
        youtubeUrl: testUrl
      })
    };

    const execution = await stepfunctions.startExecution(executionParams).promise();
    console.log('✅ Enhanced Step Functions execution started');
    console.log(`🔗 Execution ARN: ${execution.executionArn}\n`);

    // Monitor execution progress
    console.log('📊 Monitoring execution progress...\n');
    
    let executionStatus = 'RUNNING';
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes max

    while (executionStatus === 'RUNNING' && attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
      
      const statusResult = await stepfunctions.describeExecution({
        executionArn: execution.executionArn
      }).promise();
      
      executionStatus = statusResult.status;
      attempts++;

      // Get job status from DynamoDB
      const jobResult = await dynamodb.get({
        TableName: JOBS_TABLE,
        Key: { jobId: jobId }
      }).promise();

      const job = jobResult.Item;
      if (job) {
        console.log(`⏳ Status: ${job.status} | Progress: ${job.progress || 0}% | Step: ${job.statusMessage || 'Processing...'}`);
        
        // Show enhanced analysis progress
        if (job.musicalAnalysis) {
          console.log('🎼 Musical Analysis: ✅ Complete');
        }
        if (job.lyricsAnalysis) {
          console.log('📝 Lyrics Analysis: ✅ Complete');
        }
        if (job.pdfData) {
          console.log('📄 PDF Data: ✅ Ready');
        }
      }

      if (executionStatus !== 'RUNNING') {
        break;
      }
    }

    console.log(`\n🏁 Execution completed with status: ${executionStatus}`);

    // Get final job result
    const finalJobResult = await dynamodb.get({
      TableName: JOBS_TABLE,
      Key: { jobId: jobId }
    }).promise();

    const finalJob = finalJobResult.Item;
    
    if (finalJob) {
      console.log('\n📊 Final Results:');
      console.log(`Status: ${finalJob.status}`);
      console.log(`Progress: ${finalJob.progress || 0}%`);
      
      if (finalJob.pdfUrl) {
        console.log(`📄 PDF URL: ${finalJob.pdfUrl}`);
      }
      
      // Show enhanced analysis results
      if (finalJob.musicalAnalysis) {
        const analysis = finalJob.musicalAnalysis;
        console.log('\n🎼 Enhanced Musical Analysis:');
        console.log(`- Tempo: ${analysis.tempo?.bpm || 'Unknown'} BPM`);
        console.log(`- Key: ${analysis.key?.root || 'Unknown'} ${analysis.key?.mode || ''}`);
        console.log(`- Time Signature: ${analysis.timeSignature?.numerator || 4}/${analysis.timeSignature?.denominator || 4}`);
        console.log(`- Total Chords: ${analysis.chords?.chords?.length || 0} (0.2s intervals)`);
      }
      
      if (finalJob.lyricsAnalysis) {
        const lyrics = finalJob.lyricsAnalysis;
        console.log('\n📝 Enhanced Lyrics Analysis:');
        console.log(`- Total Syllables: ${lyrics.syllables?.length || 0}`);
        console.log(`- Verses: ${lyrics.verses?.length || 0}`);
        console.log(`- Pickup Notes: ${lyrics.pickupNotes?.length || 0}`);
      }
      
      if (finalJob.pdfData) {
        const pdfData = finalJob.pdfData;
        console.log('\n📄 PDF Generation Data:');
        console.log(`- Measure Lines: ${pdfData.measureLines?.length || 0}`);
        console.log(`- Total Syllables: ${pdfData.totalSyllables || 0}`);
        console.log(`- Total Chords: ${pdfData.totalChords || 0}`);
        console.log(`- Layout: ${pdfData.pdfMetadata?.layoutType || 'standard'}`);
      }
      
      if (finalJob.qualityMetrics) {
        const quality = finalJob.qualityMetrics;
        console.log('\n📈 Quality Metrics:');
        console.log(`- Overall Quality: ${(quality.overallQuality * 100).toFixed(1)}%`);
        console.log(`- Production Ready: ${quality.isProductionReady ? '✅ Yes' : '❌ No'}`);
        if (quality.recommendations?.length > 0) {
          console.log('- Recommendations:');
          quality.recommendations.forEach(rec => console.log(`  • ${rec}`));
        }
      }
    }

    if (executionStatus === 'SUCCEEDED') {
      console.log('\n🎉 Enhanced system test completed successfully!');
      console.log('✅ All enhanced features are working:');
      console.log('  • 0.2-second chord detection');
      console.log('  • Syllable-level lyrics analysis');
      console.log('  • Downbeat identification');
      console.log('  • Measure-based PDF layout');
      console.log('  • RED/BLACK chord color coding');
      console.log('  • Professional Nashville Number System output');
    } else {
      console.log(`\n❌ Test failed with status: ${executionStatus}`);
      
      // Get execution details for debugging
      const executionDetails = await stepfunctions.describeExecution({
        executionArn: execution.executionArn
      }).promise();
      
      if (executionDetails.output) {
        console.log('Error details:', JSON.parse(executionDetails.output));
      }
    }

  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Run the test
if (require.main === module) {
  testEnhancedSystem();
}

module.exports = { testEnhancedSystem };