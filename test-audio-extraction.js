// Test 1: Audio Extraction from YouTube
// This will test if we can properly extract audio from a YouTube URL

const AWS = require('aws-sdk');

const stepfunctions = new AWS.StepFunctions({ region: 'us-east-1' });

async function testAudioExtraction() {
  console.log('🎵 Testing Audio Extraction from YouTube...');
  
  const testUrl = 'https://www.youtube.com/watch?v=CDdvReNKKuk'; // Amazing Grace - 3 min song
  
  try {
    // Start just the audio extraction step
    const params = {
      stateMachineArn: 'arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-Enhanced-Workflow-dev',
      input: JSON.stringify({
        youtubeUrl: testUrl,
        testMode: 'AUDIO_ONLY' // Custom flag to stop after audio extraction
      })
    };
    
    console.log('🚀 Starting audio extraction test...');
    const execution = await stepfunctions.startExecution(params).promise();
    console.log('📋 Execution ARN:', execution.executionArn);
    
    // Monitor execution
    let status = 'RUNNING';
    let attempts = 0;
    
    while (status === 'RUNNING' && attempts < 20) {
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      const result = await stepfunctions.describeExecution({
        executionArn: execution.executionArn
      }).promise();
      
      status = result.status;
      console.log(`[${attempts}] Status: ${status}`);
      
      if (status === 'SUCCEEDED') {
        const output = JSON.parse(result.output);
        console.log('✅ Audio extraction completed!');
        console.log('📄 Output:', JSON.stringify(output, null, 2));
        
        // Check if audio file was created
        if (output.audioUrl) {
          console.log('🎵 Audio URL:', output.audioUrl);
          console.log('🧪 Test downloading audio file...');
          
          // Try to download a small portion to verify it exists
          const response = await fetch(output.audioUrl, { method: 'HEAD' });
          console.log('📊 Audio file status:', response.status);
          console.log('📏 Audio file size:', response.headers.get('content-length'));
          console.log('🎼 Audio file type:', response.headers.get('content-type'));
          
          return {
            success: true,
            audioUrl: output.audioUrl,
            fileSize: response.headers.get('content-length'),
            contentType: response.headers.get('content-type')
          };
        }
      } else if (status === 'FAILED') {
        console.error('❌ Audio extraction failed');
        console.error('Error:', result.error);
        return { success: false, error: result.error };
      }
      
      attempts++;
    }
    
    if (attempts >= 20) {
      console.error('⏰ Test timed out');
      return { success: false, error: 'Timeout' };
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    return { success: false, error: error.message };
  }
}

// Run the test
testAudioExtraction().then(result => {
  console.log('\n🎯 Audio Extraction Test Result:');
  console.log(JSON.stringify(result, null, 2));
}).catch(console.error);