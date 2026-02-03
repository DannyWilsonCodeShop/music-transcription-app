// Simple Test of the Corrected Enhanced Workflow
const AWS = require('aws-sdk');

const stepfunctions = new AWS.StepFunctions({ region: 'us-east-1' });

async function testWorkflow() {
  console.log('🧪 Testing Corrected Enhanced Workflow...');
  
  try {
    const params = {
      stateMachineArn: 'arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-V2-Transcription-dev',
      input: JSON.stringify({
        youtubeUrl: 'https://www.youtube.com/watch?v=CDdvReNKKuk',
        jobId: 'test-corrected-' + Date.now()
      })
    };
    
    console.log('🚀 Starting corrected workflow...');
    const execution = await stepfunctions.startExecution(params).promise();
    console.log('📋 Execution ARN:', execution.executionArn);
    
    // Monitor for 2 minutes
    let attempts = 0;
    while (attempts < 24) { // 24 * 5 seconds = 2 minutes
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      const result = await stepfunctions.describeExecution({
        executionArn: execution.executionArn
      }).promise();
      
      console.log(`[${attempts}] Status: ${result.status}`);
      
      if (result.status === 'SUCCEEDED') {
        console.log('✅ Workflow completed successfully!');
        const output = JSON.parse(result.output);
        console.log('📄 Output:', JSON.stringify(output, null, 2));
        return { success: true, output };
      } else if (result.status === 'FAILED') {
        console.error('❌ Workflow failed');
        console.error('Error:', result.error);
        return { success: false, error: result.error };
      }
      
      attempts++;
    }
    
    console.log('⏰ Test timed out');
    return { success: false, error: 'Timeout' };
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    return { success: false, error: error.message };
  }
}

testWorkflow().then(result => {
  console.log('\n🎯 Test Result:', JSON.stringify(result, null, 2));
}).catch(console.error);