// Test the Corrected Enhanced Workflow
const AWS = require('aws-sdk');

const stepfunctions = new AWS.StepFunctions({ region: 'us-east-1' });

async function testCorrectedWorkflow() {
  console.log('🧪 Testing Corrected Enhanced Workflow...');
  
  const testUrl = 'https://www.youtube.com/watch?v=CDdvReNKKuk'; // Amazing Grace - 3 min song
  
  try {
    // Start the corrected workflow
    const params = {
      stateMachineArn: 'arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-V2-Transcription-dev',
      input: JSON.stringify({
        youtubeUrl: testUrl,
        jobId: 'test-corrected-' + Date.now()
      })
    };
    
    console.log('🚀 Starting corrected enhanced workflow...');
    console.log('🎵 Test URL:', testUrl);
    
    const execution = await stepfunctions.startExecution(params).promise();
    console.log('📋 Execution ARN:', execution.executionArn);
    
    // Monitor execution for a few steps
    let status = 'RUNNING';
    let attempts = 0;
    let lastStatus = '';
    
    while (status === 'RUNNING' && attempts < 30) {
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      const result = await stepfunctions.describeExecution({
        executionArn: execution.executionArn
      }).promise();
      
      status = result.status;
      
      // Get execution history to see which step we're on
      const history = await stepfunctions.getExecutionHistory({
        executionArn: execution.executionArn,
        maxResults: 10,
        reverseOrder: true
      }).promise();
      
      const latestEvent = history.events[0];
      let currentStep = 'Unknown';
      
      if (latestEvent.type === 'TaskStateEntered') {
        currentStep = latestEvent.stateEnteredEventDetails.name;
      } else if (latestEvent.type === 'TaskStateExited') {
        currentStep = latestEvent.stateExitedEventDetails.name + ' (completed)';
      } else if (latestEvent.type === 'ParallelStateEntered') {
        currentStep = 'ParallelAnalysis (running enhanced audio + lyrics)';
      }
      
      if (currentStep !== lastStatus) {
        console.log(`[${attempts}] Status: ${status} | Current Step: ${currentStep}`);
        lastStatus = currentStep;
      }\n      \n      if (status === 'SUCCEEDED') {\n        const output = JSON.parse(result.output);\n        console.log('✅ Corrected workflow completed successfully!');\n        console.log('📄 Final Output:', JSON.stringify(output, null, 2));\n        \n        // Check if we got enhanced features\n        if (output.enhancedFeatures) {\n          console.log('🎯 Enhanced Features Detected:');\n          console.log(`  📊 Chords: ${output.enhancedFeatures.chordsDetected}`);\n          console.log(`  📐 Measure Layout: ${output.enhancedFeatures.measureBasedLayout}`);\n          console.log(`  🎤 Syllable Alignment: ${output.enhancedFeatures.syllableAlignment}`);\n        }\n        \n        return {\n          success: true,\n          output: output,\n          executionArn: execution.executionArn\n        };\n      } else if (status === 'FAILED') {\n        console.error('❌ Corrected workflow failed');\n        console.error('Error:', result.error);\n        console.error('Cause:', result.cause);\n        \n        // Get more details from execution history\n        const failureEvents = history.events.filter(e => \n          e.type.includes('Failed') || e.type.includes('TimedOut')\n        );\n        \n        if (failureEvents.length > 0) {\n          console.error('Failure Details:', JSON.stringify(failureEvents[0], null, 2));\n        }\n        \n        return {\n          success: false,\n          error: result.error,\n          cause: result.cause,\n          executionArn: execution.executionArn\n        };\n      }\n      \n      attempts++;\n    }\n    \n    if (attempts >= 30) {\n      console.log('⏰ Test timed out after 2.5 minutes');\n      console.log('📊 Final Status:', status);\n      return {\n        success: false,\n        error: 'Timeout',\n        finalStatus: status,\n        executionArn: execution.executionArn\n      };\n    }\n    \n  } catch (error) {\n    console.error('❌ Test failed:', error);\n    return { success: false, error: error.message };\n  }\n}\n\n// Run the test\ntestCorrectedWorkflow().then(result => {\n  console.log('\\n🎯 Corrected Workflow Test Result:');\n  console.log(JSON.stringify(result, null, 2));\n  \n  if (result.success) {\n    console.log('\\n🎉 SUCCESS! The corrected enhanced workflow is working!');\n    console.log('💡 Enhanced features should now be properly integrated.');\n  } else {\n    console.log('\\n🔍 ANALYSIS NEEDED:');\n    console.log('Check the execution details to see which step failed.');\n    if (result.executionArn) {\n      console.log(`AWS Console: https://console.aws.amazon.com/states/home?region=us-east-1#/executions/details/${result.executionArn.split(':').pop()}`);\n    }\n  }\n}).catch(console.error);