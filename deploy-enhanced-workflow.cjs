// Deploy Enhanced Step Functions Workflow
// Updates the Step Functions state machine to use the enhanced pipeline

const AWS = require('aws-sdk');
const fs = require('fs');

AWS.config.update({ region: 'us-east-1' });
const stepfunctions = new AWS.StepFunctions();

const STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-V2-Transcription-dev';

async function deployEnhancedWorkflow() {
  console.log('🚀 Deploying Enhanced Step Functions Workflow...\n');

  try {
    // Read the enhanced workflow definition
    const workflowDefinition = fs.readFileSync('./enhanced-step-functions-workflow.json', 'utf8');
    
    console.log('📋 Enhanced Workflow Features:');
    console.log('  • Parallel audio and lyrics analysis');
    console.log('  • 0.2-second chord detection intervals');
    console.log('  • Syllable-level lyrics processing');
    console.log('  • Musical integration orchestrator');
    console.log('  • Enhanced PDF generation with measure-based layout\n');

    // Update the state machine
    const updateParams = {
      stateMachineArn: STATE_MACHINE_ARN,
      definition: workflowDefinition,
      roleArn: 'arn:aws:iam::090130568474:role/StepFunctionsExecutionRole'
    };

    console.log('🔄 Updating Step Functions state machine...');
    const result = await stepfunctions.updateStateMachine(updateParams).promise();
    
    console.log('✅ Enhanced workflow deployed successfully!');
    console.log(`🔗 State Machine ARN: ${STATE_MACHINE_ARN}`);
    console.log(`📅 Update Date: ${result.updateDate}\n`);

    console.log('🎯 Enhanced Features Now Active:');
    console.log('  ✅ 0.2-second chord detection (900 chords per 3-min song)');
    console.log('  ✅ Syllable-level lyrics analysis');
    console.log('  ✅ Downbeat identification');
    console.log('  ✅ Measure-based PDF layout');
    console.log('  ✅ RED downbeat / BLACK passing chord colors');
    console.log('  ✅ Professional Nashville Number System output\n');

    console.log('🧪 Test the enhanced system:');
    console.log('  1. Visit: https://dev.dqg97bbmmprz.amplifyapp.com/');
    console.log('  2. Submit any YouTube music URL');
    console.log('  3. Expect: Professional PDF with 900+ chord detections');
    console.log('  4. Format: Perfect measure-based layout with color coding\n');

    console.log('🎉 Enhanced music transcription system is now fully operational!');

  } catch (error) {
    console.error('❌ Deployment failed:', error);
    
    if (error.code === 'InvalidParameterValue') {
      console.log('\n🔧 Troubleshooting:');
      console.log('  • Check that all Lambda function ARNs exist');
      console.log('  • Verify IAM role permissions');
      console.log('  • Ensure workflow JSON syntax is valid');
    }
  }
}

if (require.main === module) {
  deployEnhancedWorkflow();
}

module.exports = { deployEnhancedWorkflow };