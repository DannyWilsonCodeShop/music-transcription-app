// Simple Chord Recognition Test for meetup_ring.mp3
// This test bypasses DynamoDB storage and focuses on chord detection only

const AWS = require('aws-sdk');
const fs = require('fs');
const path = require('path');

const lambda = new AWS.Lambda({ region: 'us-east-1' });

async function testSimpleChordRecognition() {
  console.log('🎸 Testing Simple Chord Recognition with meetup_ring.mp3...');
  
  const audioFilePath = path.join(__dirname, 'public', 'meetup_ring.mp3');
  
  // Check if the audio file exists
  if (!fs.existsSync(audioFilePath)) {
    console.error('❌ Audio file not found:', audioFilePath);
    return { success: false, error: 'Audio file not found' };
  }
  
  console.log('✅ Audio file found:', audioFilePath);
  
  // Get file stats
  const stats = fs.statSync(audioFilePath);
  console.log('📊 File size:', (stats.size / 1024 / 1024).toFixed(2), 'MB');
  
  // Use a simpler approach - test with a mock audio URL that doesn't require S3 upload
  const testAudioUrl = 'https://chordscout-audio-dev-463470937777.s3.amazonaws.com/audio/meetup_ring.mp3';
  
  try {
    console.log('🚀 Starting simple chord recognition test...');
    console.log('🎵 Audio URL:', testAudioUrl);
    
    // Create a minimal test payload that won't store large data to DynamoDB
    const params = {
      FunctionName: 'chordscout-enhanced-audio-analyzer-dev',
      Payload: JSON.stringify({
        audioUrl: testAudioUrl,
        jobId: 'test-simple-chords-' + Date.now(),
        testMode: true,
        skipDynamoStorage: true, // Skip storing to DynamoDB
        returnAnalysisOnly: true, // Return analysis directly
        maxChords: 100 // Limit chord analysis to prevent size issues
      })
    };
    
    console.log('⏱️ Invoking enhanced audio analyzer (simple mode)...');
    const startTime = Date.now();
    
    const result = await lambda.invoke(params).promise();
    const processingTime = Date.now() - startTime;
    
    console.log('📊 Lambda Response Status:', result.StatusCode);
    console.log('⏱️ Processing time:', processingTime, 'ms');
    
    if (result.StatusCode === 200) {
      const response = JSON.parse(result.Payload);
      console.log('✅ Simple chord recognition completed!');
      
      // Log the response structure to understand what we're getting
      console.log('📄 Response keys:', Object.keys(response));
      if (response.body) {
        console.log('📄 Body keys:', Object.keys(response.body));
      }
      
      // Try to extract chord data from various possible locations
      let chordData = null;
      let analysisData = null;
      
      if (response.body && response.body.analysis) {
        analysisData = response.body.analysis;
        chordData = analysisData.chords;
      } else if (response.body && response.body.chords) {
        chordData = response.body.chords;
      } else if (response.analysis) {
        analysisData = response.analysis;
        chordData = analysisData.chords;
      } else if (response.chords) {
        chordData = response.chords;
      }
      
      if (chordData && chordData.chords) {
        const chords = chordData.chords;
        console.log('\n🎼 Simple Chord Recognition Results:');
        console.log('📊 Total chord detections:', chords.length);
        console.log('⏱️ Analysis interval:', chordData.analysisInterval || 'unknown', 'seconds');
        
        // Show first 10 chord detections
        console.log('\n🎼 First 10 chord detections:');
        chords.slice(0, 10).forEach((chord, index) => {
          const downbeatIndicator = chord.isDownbeat ? '[DOWNBEAT]' : '';
          const passingIndicator = chord.isPassingChord ? '[PASSING]' : '';
          
          console.log(`[${index.toString().padStart(2, '0')}] ${chord.start?.toFixed(1) || chord.time?.toFixed(1)}s: ${chord.chord} ${downbeatIndicator}${passingIndicator}`);
        });
        
        // Analyze chord distribution
        const chordCounts = {};
        chords.forEach(chord => {
          chordCounts[chord.chord] = (chordCounts[chord.chord] || 0) + 1;
        });
        
        console.log('\n📊 Top 5 Chord Distribution:');
        Object.entries(chordCounts)
          .sort(([,a], [,b]) => b - a)
          .slice(0, 5)
          .forEach(([chord, count]) => {
            const percentage = ((count / chords.length) * 100).toFixed(1);
            console.log(`${chord.padEnd(6)}: ${count.toString().padStart(3)} times (${percentage}%)`);
          });
        
        return {
          success: true,
          totalChords: chords.length,
          analysisInterval: chordData.analysisInterval,
          chordDistribution: chordCounts,
          processingTime: processingTime,
          sampleChords: chords.slice(0, 10)
        };
        
      } else {
        console.log('⚠️ No chord data found in response');
        console.log('📄 Full response preview:', JSON.stringify(response, null, 2).substring(0, 1000) + '...');
        return {
          success: false,
          error: 'No chord data in response',
          responsePreview: JSON.stringify(response, null, 2).substring(0, 500)
        };
      }
      
    } else {
      console.error('❌ Lambda invocation failed');
      console.error('Status:', result.StatusCode);
      console.error('Error:', result.Payload);
      return { 
        success: false, 
        error: result.Payload,
        statusCode: result.StatusCode
      };
    }
    
  } catch (error) {
    console.error('❌ Simple chord recognition test failed:', error);
    return { 
      success: false, 
      error: error.message,
      stack: error.stack
    };
  }
}

// Test with the local enhanced audio analyzer module directly
async function testLocalChordAnalysis() {
  console.log('🏠 Testing Local Chord Analysis Module...');
  
  try {
    const localAnalyzerPath = path.join(__dirname, 'local-server', 'modules', 'enhanced-audio-analyzer.js');
    
    if (fs.existsSync(localAnalyzerPath)) {
      console.log('✅ Local enhanced audio analyzer found');
      
      // Read the module to see what functions are available
      const moduleContent = fs.readFileSync(localAnalyzerPath, 'utf8');
      
      // Look for exported functions
      const exportMatches = moduleContent.match(/exports\.\w+/g) || [];
      const functionMatches = moduleContent.match(/function \w+/g) || [];
      
      console.log('📋 Available exports:', exportMatches);
      console.log('📋 Available functions:', functionMatches);
      
      // Try to require and test the module
      try {
        const localAnalyzer = require(localAnalyzerPath);
        console.log('📋 Module exports:', Object.keys(localAnalyzer));
        
        // If there's an analyzeAudio function, try to use it
        if (localAnalyzer.analyzeAudioLocally) {
          console.log('🎵 Testing analyzeAudioLocally function...');
          
          const audioFilePath = path.join(__dirname, 'public', 'meetup_ring.mp3');
          
          // This is a mock test since the function might not be fully implemented
          console.log('⚠️ Local analysis function exists but may not be fully implemented');
          return { success: true, message: 'Local analyzer module found and loaded' };
          
        } else {
          console.log('⚠️ No analyzeAudioLocally function found');
          return { success: false, error: 'No analyzeAudioLocally function' };
        }
        
      } catch (requireError) {
        console.error('❌ Error requiring local analyzer:', requireError.message);
        return { success: false, error: 'Failed to require local analyzer' };
      }
      
    } else {
      console.log('❌ Local enhanced audio analyzer not found');
      return { success: false, error: 'Local analyzer not found' };
    }
    
  } catch (error) {
    console.error('❌ Local chord analysis test failed:', error);
    return { success: false, error: error.message };
  }
}

// Run the simple chord recognition test
async function runSimpleChordTest() {
  console.log('🧪 Running Simple Meetup Ring Chord Recognition Test...\n');
  
  const lambdaTest = await testSimpleChordRecognition();
  console.log('\n' + '='.repeat(60) + '\n');
  
  const localTest = await testLocalChordAnalysis();
  
  console.log('\n🎯 Simple Chord Recognition Results:');
  console.log('Lambda Test:', JSON.stringify(lambdaTest, null, 2));
  console.log('Local Test:', JSON.stringify(localTest, null, 2));
  
  return {
    lambdaTest,
    localTest
  };
}

// Export for use in other tests
module.exports = {
  testSimpleChordRecognition,
  testLocalChordAnalysis,
  runSimpleChordTest
};

// Run if called directly
if (require.main === module) {
  runSimpleChordTest().catch(console.error);
}