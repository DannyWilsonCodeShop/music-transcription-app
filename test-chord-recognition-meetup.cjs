// Test Chord Recognition with meetup_ring.mp3
// This test isolates chord detection functionality using the specific audio file

const AWS = require('aws-sdk');
const fs = require('fs');
const path = require('path');

const lambda = new AWS.Lambda({ region: 'us-east-1' });

async function testChordRecognitionMeetup() {
  console.log('🎸 Testing Chord Recognition with meetup_ring.mp3...');
  
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
  
  // For this test, we'll need to upload the file to S3 first or use a pre-uploaded URL
  // Let's assume it's already uploaded and use a test URL
  const testAudioUrl = 'https://chordscout-audio-dev-463470937777.s3.amazonaws.com/audio/meetup_ring.mp3';
  
  try {
    console.log('🚀 Starting chord recognition test...');
    console.log('🎵 Audio URL:', testAudioUrl);
    
    // Test the enhanced audio analyzer for chord detection
    const params = {
      FunctionName: 'chordscout-enhanced-audio-analyzer-dev',
      Payload: JSON.stringify({
        audioUrl: testAudioUrl,
        jobId: 'test-meetup-chords-' + Date.now(),
        testMode: true,
        chordAnalysisOnly: true // Focus only on chord detection
      })
    };
    
    console.log('⏱️ Invoking enhanced audio analyzer...');
    const startTime = Date.now();
    
    const result = await lambda.invoke(params).promise();
    const processingTime = Date.now() - startTime;
    
    console.log('📊 Lambda Response Status:', result.StatusCode);
    console.log('⏱️ Processing time:', processingTime, 'ms');
    
    if (result.StatusCode === 200) {
      const response = JSON.parse(result.Payload);
      console.log('✅ Chord recognition completed!');
      
      if (response.body && response.body.analysis) {
        const analysis = response.body.analysis;
        
        // Extract chord information
        const chordAnalysis = analysis.chords;
        const nashvilleNumbers = analysis.nashvilleNumbers;
        
        if (chordAnalysis && chordAnalysis.chords) {
          const chords = chordAnalysis.chords;
          console.log('\n🎼 Chord Recognition Results:');
          console.log('📊 Total chord detections:', chords.length);
          console.log('⏱️ Analysis interval:', chordAnalysis.analysisInterval, 'seconds');
          console.log('🎯 Detection rate:', (chords.length * chordAnalysis.analysisInterval / 60).toFixed(1), 'chords per minute');
          
          // Show tempo and key information
          if (analysis.tempo) {
            console.log('🥁 Detected BPM:', analysis.tempo.bpm);
            console.log('🎵 Tempo confidence:', (analysis.tempo.confidence * 100).toFixed(1) + '%');
          }
          
          if (analysis.key) {
            console.log('🗝️ Detected key:', analysis.key.root, analysis.key.mode);
            console.log('🎵 Key confidence:', (analysis.key.confidence * 100).toFixed(1) + '%');
          }
          
          // Show first 20 chord detections with Nashville numbers
          console.log('\n🎼 First 20 chord detections:');
          chords.slice(0, 20).forEach((chord, index) => {
            const nashvilleChord = nashvilleNumbers?.allChords?.find(nc => 
              Math.abs(nc.start - chord.start) < 0.1
            );
            
            const nashvilleNum = nashvilleChord?.nashvilleNumber || 'N/A';
            const downbeatIndicator = chord.isDownbeat ? '[DOWNBEAT]' : '';
            const passingIndicator = chord.isPassingChord ? '[PASSING]' : '';
            
            console.log(`[${index.toString().padStart(2, '0')}] ${chord.start.toFixed(1)}s: ${chord.chord.padEnd(4)} (${nashvilleNum}) ${downbeatIndicator}${passingIndicator}`);
          });
          
          // Analyze chord distribution
          const chordCounts = {};
          chords.forEach(chord => {
            chordCounts[chord.chord] = (chordCounts[chord.chord] || 0) + 1;
          });
          
          console.log('\n📊 Chord Distribution:');
          Object.entries(chordCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10)
            .forEach(([chord, count]) => {
              const percentage = ((count / chords.length) * 100).toFixed(1);
              console.log(`${chord.padEnd(6)}: ${count.toString().padStart(3)} times (${percentage}%)`);
            });
          
          // Analyze downbeats vs passing chords
          const downbeats = chords.filter(c => c.isDownbeat);
          const passingChords = chords.filter(c => c.isPassingChord);
          
          console.log('\n🎯 Beat Analysis:');
          console.log('🔴 Downbeats:', downbeats.length);
          console.log('⚫ Passing chords:', passingChords.length);
          console.log('📊 Downbeat ratio:', ((downbeats.length / chords.length) * 100).toFixed(1) + '%');
          
          // Show Nashville number distribution
          if (nashvilleNumbers && nashvilleNumbers.allChords) {
            const nashvilleCounts = {};
            nashvilleNumbers.allChords.forEach(chord => {
              nashvilleCounts[chord.nashvilleNumber] = (nashvilleCounts[chord.nashvilleNumber] || 0) + 1;
            });
            
            console.log('\n🔢 Nashville Number Distribution:');
            Object.entries(nashvilleCounts)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 8)
              .forEach(([number, count]) => {
                const percentage = ((count / nashvilleNumbers.allChords.length) * 100).toFixed(1);
                console.log(`${number.padEnd(4)}: ${count.toString().padStart(3)} times (${percentage}%)`);
              });
          }
          
          return {
            success: true,
            totalChords: chords.length,
            analysisInterval: chordAnalysis.analysisInterval,
            detectionRate: (chords.length * chordAnalysis.analysisInterval / 60).toFixed(1),
            tempo: analysis.tempo,
            key: analysis.key,
            chordDistribution: chordCounts,
            downbeats: downbeats.length,
            passingChords: passingChords.length,
            processingTime: processingTime,
            sampleChords: chords.slice(0, 20)
          };
          
        } else {
          console.log('⚠️ No chord analysis found in response');
          console.log('📄 Response structure:', Object.keys(response.body));
          return {
            success: false,
            error: 'No chord analysis in response',
            responseKeys: Object.keys(response.body)
          };
        }
        
      } else {
        console.log('⚠️ No analysis data found in response');
        console.log('📄 Full response:', JSON.stringify(response, null, 2));
        return {
          success: false,
          error: 'No analysis data in response',
          response: response
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
    console.error('❌ Chord recognition test failed:', error);
    return { 
      success: false, 
      error: error.message,
      stack: error.stack
    };
  }
}

// Test with local audio analyzer (if available)
async function testLocalChordRecognition() {
  console.log('🏠 Testing Local Chord Recognition...');
  
  try {
    // Check if local server is available
    const localServerPath = path.join(__dirname, 'local-server', 'modules', 'enhanced-audio-analyzer.js');
    
    if (fs.existsSync(localServerPath)) {
      console.log('✅ Local audio analyzer found');
      
      const localAnalyzer = require(localServerPath);
      const audioFilePath = path.join(__dirname, 'public', 'meetup_ring.mp3');
      
      if (fs.existsSync(audioFilePath)) {
        console.log('🎵 Processing local audio file...');
        
        // This would call the local analyzer
        // const result = await localAnalyzer.analyzeAudio(audioFilePath);
        
        console.log('⚠️ Local analysis not implemented yet - use Lambda version');
        return { success: false, error: 'Local analysis not implemented' };
        
      } else {
        console.log('❌ Audio file not found for local analysis');
        return { success: false, error: 'Audio file not found' };
      }
      
    } else {
      console.log('⚠️ Local audio analyzer not found - using Lambda version only');
      return { success: false, error: 'Local analyzer not available' };
    }
    
  } catch (error) {
    console.error('❌ Local chord recognition test failed:', error);
    return { success: false, error: error.message };
  }
}

// Run the chord recognition test
async function runMeetupChordTest() {
  console.log('🧪 Running Meetup Ring Chord Recognition Test...\n');
  
  const lambdaTest = await testChordRecognitionMeetup();
  console.log('\n' + '='.repeat(60) + '\n');
  
  const localTest = await testLocalChordRecognition();
  
  console.log('\n🎯 Meetup Ring Chord Recognition Results:');
  console.log('Lambda Test:', JSON.stringify(lambdaTest, null, 2));
  console.log('Local Test:', JSON.stringify(localTest, null, 2));
  
  return {
    lambdaTest,
    localTest
  };
}

// Export for use in other tests
module.exports = {
  testChordRecognitionMeetup,
  testLocalChordRecognition,
  runMeetupChordTest
};

// Run if called directly
if (require.main === module) {
  runMeetupChordTest().catch(console.error);
}