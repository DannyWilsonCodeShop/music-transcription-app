// Test 3: Enhanced Chord Detection
// This will test if we get 1500 chords for a 5-minute song (0.2s intervals)

const AWS = require('aws-sdk');

const lambda = new AWS.Lambda({ region: 'us-east-1' });

async function testChordDetection() {
  console.log('🎸 Testing Enhanced Chord Detection...');
  
  // For a 5-minute song at 0.2s intervals, we should get:
  // 5 minutes = 300 seconds
  // 300 seconds ÷ 0.2s = 1500 chord detections
  
  const testAudioUrl = 'https://chordscout-audio-dev-463470937777.s3.amazonaws.com/audio/test-5min-song.mp3';
  
  try {
    // Test the enhanced audio analyzer directly
    const params = {
      FunctionName: 'chordscout-v2-enhanced-audio-analyzer-dev',
      Payload: JSON.stringify({
        audioUrl: testAudioUrl,
        jobId: 'test-chords-' + Date.now(),
        expectedDuration: 300, // 5 minutes
        testMode: true
      })
    };
    
    console.log('🚀 Invoking enhanced audio analyzer...');
    console.log('⏱️ Expected: ~1500 chord detections for 5-minute song');
    
    const result = await lambda.invoke(params).promise();
    
    if (result.StatusCode === 200) {
      const response = JSON.parse(result.Payload);
      console.log('✅ Chord detection completed!');
      
      if (response.body && response.body.enhancedChords) {
        const chords = response.body.enhancedChords;
        console.log('🎵 Enhanced chords detected:');
        console.log(`📊 Total chord detections: ${chords.length}`);
        console.log(`🎯 Expected for 5min song: ~1500`);
        console.log(`📈 Detection rate: ${(chords.length / 300).toFixed(1)} per second`);
        
        // Analyze chord detection intervals
        if (chords.length > 1) {
          const intervals = [];
          for (let i = 1; i < Math.min(chords.length, 100); i++) {
            const interval = chords[i].time - chords[i-1].time;
            intervals.push(interval);
          }
          
          const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
          console.log(`⏱️ Average detection interval: ${avgInterval.toFixed(3)}s`);
          console.log(`🎯 Target interval: 0.200s`);
        }
        
        // Show first 10 chord detections
        console.log('\n🎼 First 10 chord detections:');
        chords.slice(0, 10).forEach((chord, index) => {
          console.log(`[${index}] ${chord.time.toFixed(1)}s: ${chord.chord} (${chord.nashvilleNumber}) ${chord.isDownbeat ? '[DOWNBEAT]' : ''}`);
        });
        
        // Check if we're getting the expected number of detections
        const expectedChords = 1500;
        const actualChords = chords.length;
        const accuracy = (actualChords / expectedChords) * 100;
        
        return {
          success: true,
          totalChords: actualChords,
          expectedChords: expectedChords,
          accuracy: accuracy.toFixed(1) + '%',
          avgInterval: avgInterval?.toFixed(3),
          sampleChords: chords.slice(0, 10),
          processingTime: response.body.processingTime
        };
      } else {
        console.log('⚠️ No enhanced chords found in response');
        return {
          success: false,
          error: 'No enhanced chords in response',
          response: response.body
        };
      }
    } else {
      console.error('❌ Lambda invocation failed');
      console.error('Status:', result.StatusCode);
      console.error('Error:', result.Payload);
      return { success: false, error: result.Payload };
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    return { success: false, error: error.message };
  }
}

// Test with a known 3-minute song (should get ~900 chords)
async function testChordDetectionShort() {
  console.log('🎸 Testing Enhanced Chord Detection (3-minute song)...');
  
  try {
    const params = {
      FunctionName: 'chordscout-v2-enhanced-audio-analyzer-dev',
      Payload: JSON.stringify({
        // Use Amazing Grace URL from previous tests
        audioUrl: 'https://chordscout-audio-dev-463470937777.s3.amazonaws.com/audio/test-3min-song.mp3',
        jobId: 'test-chords-3min-' + Date.now(),
        expectedDuration: 180, // 3 minutes
        testMode: true
      })
    };
    
    console.log('🚀 Testing 3-minute song chord detection...');
    console.log('⏱️ Expected: ~900 chord detections for 3-minute song');
    
    const result = await lambda.invoke(params).promise();
    
    console.log('📊 Lambda Response Status:', result.StatusCode);
    
    if (result.StatusCode === 200) {
      const response = JSON.parse(result.Payload);
      console.log('📄 Response preview:', JSON.stringify(response, null, 2).substring(0, 500) + '...');
      
      return {
        success: true,
        response: response.body
      };
    } else {
      return {
        success: false,
        error: result.Payload
      };
    }
    
  } catch (error) {
    console.error('❌ 3-minute test failed:', error);
    return { success: false, error: error.message };
  }
}

// Run both chord detection tests
async function runChordTests() {
  console.log('🧪 Running Enhanced Chord Detection Tests...\n');
  
  const test1 = await testChordDetection();
  console.log('\n' + '='.repeat(50) + '\n');
  const test2 = await testChordDetectionShort();
  
  console.log('\n🎯 Chord Detection Test Results:');
  console.log('Test 1 (5-minute):', JSON.stringify(test1, null, 2));
  console.log('Test 2 (3-minute):', JSON.stringify(test2, null, 2));
}

runChordTests().catch(console.error);