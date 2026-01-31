// Test 2: Lyrics Extraction from Audio File
// This will test if we can extract lyrics from an MP3 file

const AWS = require('aws-sdk');

const lambda = new AWS.Lambda({ region: 'us-east-1' });

async function testLyricsExtraction() {
  console.log('🎤 Testing Lyrics Extraction from Audio...');
  
  // Use a known audio file URL (we'll get this from the audio extraction test)
  const testAudioUrl = 'https://chordscout-audio-dev-463470937777.s3.amazonaws.com/audio/test-audio.mp3';
  
  try {
    // Test the enhanced lyrics analyzer directly
    const params = {
      FunctionName: 'chordscout-v2-enhanced-lyrics-analyzer-dev',
      Payload: JSON.stringify({
        audioUrl: testAudioUrl,
        jobId: 'test-lyrics-' + Date.now()
      })
    };
    
    console.log('🚀 Invoking enhanced lyrics analyzer...');
    const result = await lambda.invoke(params).promise();
    
    if (result.StatusCode === 200) {
      const response = JSON.parse(result.Payload);
      console.log('✅ Lyrics extraction completed!');
      console.log('📄 Response:', JSON.stringify(response, null, 2));
      
      if (response.body && response.body.syllableAlignedLyrics) {
        const lyrics = response.body.syllableAlignedLyrics;
        console.log('🎵 Syllable-aligned lyrics found:');
        console.log(`📊 Total syllables: ${lyrics.length}`);
        
        // Show first 10 syllables
        lyrics.slice(0, 10).forEach((syllable, index) => {
          console.log(`[${index}] ${syllable.text} (${syllable.startTime}s - ${syllable.endTime}s)`);
        });
        
        return {
          success: true,
          totalSyllables: lyrics.length,
          sampleSyllables: lyrics.slice(0, 10),
          processingTime: response.body.processingTime
        };
      } else {
        console.log('⚠️ No syllable-aligned lyrics found');
        return {
          success: false,
          error: 'No syllable-aligned lyrics in response',
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

// Alternative test with a known good audio file
async function testLyricsWithKnownAudio() {
  console.log('🎤 Testing Lyrics with Known Audio File...');
  
  try {
    // Create a test payload with a simple audio file
    const params = {
      FunctionName: 'chordscout-v2-enhanced-lyrics-analyzer-dev',
      Payload: JSON.stringify({
        // Use a publicly available test audio file
        audioUrl: 'https://www.soundjay.com/misc/sounds/bell-ringing-05.wav',
        jobId: 'test-lyrics-known-' + Date.now(),
        testMode: true
      })
    };
    
    console.log('🚀 Testing with known audio file...');
    const result = await lambda.invoke(params).promise();
    
    console.log('📊 Lambda Response Status:', result.StatusCode);
    console.log('📄 Lambda Response:', result.Payload);
    
    return {
      success: result.StatusCode === 200,
      response: JSON.parse(result.Payload)
    };
    
  } catch (error) {
    console.error('❌ Known audio test failed:', error);
    return { success: false, error: error.message };
  }
}

// Run both tests
async function runLyricsTests() {
  console.log('🧪 Running Lyrics Extraction Tests...\n');
  
  const test1 = await testLyricsExtraction();
  console.log('\n' + '='.repeat(50) + '\n');
  const test2 = await testLyricsWithKnownAudio();
  
  console.log('\n🎯 Lyrics Extraction Test Results:');
  console.log('Test 1 (Standard):', JSON.stringify(test1, null, 2));
  console.log('Test 2 (Known Audio):', JSON.stringify(test2, null, 2));
}

runLyricsTests().catch(console.error);